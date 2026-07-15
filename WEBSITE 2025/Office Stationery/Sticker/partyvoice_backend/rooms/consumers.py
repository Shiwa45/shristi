"""
rooms/consumers.py — Realtime room state over Django Channels.

Responsibilities (Phase 1):
  - presence: track who is in the room, keep occupant_count fresh
  - seat sync: take/leave/mute/lock a seat, broadcast to everyone
  - room chat: fan out public text messages
  - moderation: host/admin mute, kick, ban

Media (the actual audio) is NOT here — ZEGOCLOUD carries audio. This consumer
keeps the *authoritative seat/room state* that the Live Audio Room Kit UI is
layered on top of. The kit can also sync seats via ZEGO room attributes; we
mirror to the server so the backend stays the source of truth for bans,
admin rights, and economy hooks added in later phases.
"""

import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer


class RoomConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.group = f"room_{self.room_id}"

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4401)  # unauthorized
            return

        room = await self._get_room(self.room_id)
        if room is None:
            await self.close(code=4404)  # not found / closed
            return
        if await self._is_banned(room.id, self.user.id):
            await self.close(code=4403)  # banned
            return

        self._room_pk = room.id
        self._is_owner = room.owner_id == self.user.id
        self._is_admin = await self._is_admin_db(room.id, self.user.id)

        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

        new_count = await self._bump_presence(room.id, +1)
        await self._broadcast("presence", {
            "user_id": self.user.public_id.hex,
            "joined": True,
            "occupant_count": new_count,
        })
        # send the current seat snapshot to the freshly-joined client
        await self.send_json({"type": "seat_snapshot", "seats": await self._seat_snapshot(room.id)})

    async def disconnect(self, code):
        if not hasattr(self, "_room_pk"):
            return
        # vacate any seat the user held
        await self._vacate_user_seats(self._room_pk, self.user.id)
        new_count = await self._bump_presence(self._room_pk, -1)
        await self.channel_layer.group_discard(self.group, self.channel_name)
        await self._broadcast("presence", {
            "user_id": self.user.public_id.hex,
            "joined": False,
            "occupant_count": new_count,
        })

    # ---- inbound client messages ----
    async def receive_json(self, content, **kwargs):
        action = content.get("action")
        handler = {
            "seat_take": self._on_seat_take,
            "seat_leave": self._on_seat_leave,
            "seat_mute": self._on_seat_mute,     # host/admin
            "seat_lock": self._on_seat_lock,     # host/admin
            "chat": self._on_chat,
            "kick": self._on_kick,               # host/admin
            "ban": self._on_ban,                 # host/admin
            "draw_stroke": self._on_draw_stroke, # Draw & Guess: brush data
            "draw_clear": self._on_draw_clear,
            "draw_guess": self._on_draw_guess,
        }.get(action)
        if handler is None:
            await self.send_json({"type": "error", "detail": f"unknown action: {action}"})
            return
        await handler(content)

    async def _on_seat_take(self, content):
        index = int(content.get("index", -1))
        ok, reason, seat = await self._take_seat(self._room_pk, self.user.id, index)
        if not ok:
            await self.send_json({"type": "error", "detail": reason})
            return
        await self._broadcast("seat_update", seat)

    async def _on_seat_leave(self, content):
        index = int(content.get("index", -1))
        seat = await self._leave_seat(self._room_pk, self.user.id, index)
        if seat:
            await self._broadcast("seat_update", seat)

    async def _on_seat_mute(self, content):
        if not (self._is_owner or self._is_admin):
            await self.send_json({"type": "error", "detail": "not authorized"})
            return
        index = int(content.get("index", -1))
        muted = bool(content.get("muted", True))
        seat = await self._set_seat_flags(self._room_pk, index, muted=muted)
        if seat:
            await self._broadcast("seat_update", seat)

    async def _on_seat_lock(self, content):
        if not (self._is_owner or self._is_admin):
            await self.send_json({"type": "error", "detail": "not authorized"})
            return
        index = int(content.get("index", -1))
        locked = bool(content.get("locked", True))
        seat = await self._set_seat_flags(self._room_pk, index, locked=locked)
        if seat:
            await self._broadcast("seat_update", seat)

    async def _on_chat(self, content):
        text = (content.get("text") or "").strip()
        if not text:
            return
        if len(text) > 500:
            text = text[:500]
        # NOTE: text moderation hook lands in Phase 5 (T&S workstream)
        await self._broadcast("chat", {
            "user_id": self.user.public_id.hex,
            "name": await self._display_name(self.user.id),
            "text": text,
        })

    async def _on_kick(self, content):
        if not (self._is_owner or self._is_admin):
            await self.send_json({"type": "error", "detail": "not authorized"})
            return
        target = content.get("user_id")
        await self._broadcast("kick", {"user_id": target, "by": self.user.public_id.hex})

    async def _on_ban(self, content):
        if not (self._is_owner or self._is_admin):
            await self.send_json({"type": "error", "detail": "not authorized"})
            return
        target = content.get("user_id")
        await self._ban_user(self._room_pk, target, self.user.id)
        await self._broadcast("ban", {"user_id": target, "by": self.user.public_id.hex})

    # ---- group event -> client ----
    async def _broadcast(self, event_type, data):
        await self.channel_layer.group_send(
            self.group, {"type": "room_event", "event_type": event_type, "data": data}
        )

    async def room_event(self, message):
        await self.send_json({"type": message["event_type"], **message["data"]})

    # ================= DB helpers =================
    @database_sync_to_async
    def _get_room(self, room_id):
        from .models import Room
        return Room.objects.filter(room_id=room_id, status=Room.Status.LIVE).first()

    @database_sync_to_async
    def _is_admin_db(self, room_pk, user_id):
        from .models import Room
        return Room.objects.filter(id=room_pk, admins__id=user_id).exists()

    @database_sync_to_async
    def _is_banned(self, room_pk, user_id):
        from .models import RoomBan
        return RoomBan.objects.filter(room_id=room_pk, user_id=user_id).exists()

    @database_sync_to_async
    def _bump_presence(self, room_pk, delta):
        from django.db.models import F
        from .models import Room
        Room.objects.filter(id=room_pk).update(
            occupant_count=F("occupant_count") + delta
        )
        room = Room.objects.get(id=room_pk)
        if room.occupant_count < 0:  # clamp on races
            room.occupant_count = 0
            room.save(update_fields=["occupant_count"])
        return room.occupant_count

    @database_sync_to_async
    def _seat_snapshot(self, room_pk):
        from .models import SeatState
        out = []
        for s in SeatState.objects.filter(room_id=room_pk).select_related("occupant", "occupant__profile"):
            out.append(self._seat_dict(s))
        return out

    def _seat_dict(self, s):
        occ = s.occupant
        name = None
        avatar = None
        if occ:
            prof = getattr(occ, "profile", None)
            name = prof.display_name if prof else occ.username
            avatar = prof.avatar_url if prof else ""
        return {
            "index": s.index,
            "muted": s.muted,
            "locked": s.locked,
            "occupant_id": occ.public_id.hex if occ else None,
            "occupant_name": name,
            "occupant_avatar": avatar,
        }

    @database_sync_to_async
    def _take_seat(self, room_pk, user_id, index):
        from django.db import transaction
        from .models import SeatState
        with transaction.atomic():
            try:
                seat = SeatState.objects.select_for_update().get(room_id=room_pk, index=index)
            except SeatState.DoesNotExist:
                return False, "seat does not exist", None
            if seat.locked:
                return False, "seat is locked", None
            if seat.occupant_id and seat.occupant_id != user_id:
                return False, "seat is taken", None
            # vacate any other seat this user holds (one seat per user)
            SeatState.objects.filter(room_id=room_pk, occupant_id=user_id).exclude(index=index).update(occupant=None)
            seat.occupant_id = user_id
            seat.save(update_fields=["occupant"])
            return True, "", self._seat_dict(seat)

    @database_sync_to_async
    def _leave_seat(self, room_pk, user_id, index):
        from .models import SeatState
        seat = SeatState.objects.filter(room_id=room_pk, index=index, occupant_id=user_id).first()
        if not seat:
            return None
        seat.occupant = None
        seat.save(update_fields=["occupant"])
        return self._seat_dict(seat)

    @database_sync_to_async
    def _vacate_user_seats(self, room_pk, user_id):
        from .models import SeatState
        SeatState.objects.filter(room_id=room_pk, occupant_id=user_id).update(occupant=None)

    @database_sync_to_async
    def _set_seat_flags(self, room_pk, index, muted=None, locked=None):
        from .models import SeatState
        seat = SeatState.objects.filter(room_id=room_pk, index=index).first()
        if not seat:
            return None
        fields = []
        if muted is not None:
            seat.muted = muted
            fields.append("muted")
        if locked is not None:
            seat.locked = locked
            if locked:
                seat.occupant = None
                fields.append("occupant")
            fields.append("locked")
        seat.save(update_fields=fields)
        return self._seat_dict(seat)

    @database_sync_to_async
    def _ban_user(self, room_pk, target_public_id, by_user_id):
        from accounts.models import User
        from .models import RoomBan, SeatState
        target = User.objects.filter(public_id=target_public_id).first()
        if not target:
            return
        RoomBan.objects.get_or_create(
            room_id=room_pk, user=target, defaults={"created_by_id": by_user_id}
        )
        SeatState.objects.filter(room_id=room_pk, occupant=target).update(occupant=None)

    @database_sync_to_async
    def _display_name(self, user_id):
        from accounts.models import User
        u = User.objects.select_related("profile").get(id=user_id)
        return u.profile.display_name if hasattr(u, "profile") else u.username

    # ================= Draw & Guess =================
    #
    # Strokes are HIGH-FREQUENCY and DISPOSABLE. A drawing hand emits dozens of
    # points a second. These are relayed straight through the channel layer and
    # NEVER written to the database — persisting brush points would hammer
    # Postgres for data nobody will ever read again. The DB only holds the game
    # state (scores, phase, whose turn).
    #
    # We also don't round-trip through REST for the same reason: the latency of
    # an HTTP call per stroke would make drawing feel like mud.

    async def _on_draw_stroke(self, content):
        """Relay brush data to the room. Only the current drawer may draw."""
        session = await self._active_draw_session()
        if not session:
            return
        drawer_slot = await self._draw_drawer_slot(session)
        my_slot = await self._draw_my_slot(session, self.user.id)
        if my_slot is None or my_slot != drawer_slot:
            return  # not the drawer — silently ignore, don't leak that they tried

        # points come as a flat list [x1,y1,x2,y2,...] in 0..1 normalised space
        points = content.get("points") or []
        if not isinstance(points, list) or len(points) > 400:
            return
        await self._broadcast("draw_stroke", {
            "points": points,
            "color": str(content.get("color", "#FFFFFF"))[:9],
            "width": min(max(float(content.get("width", 3)), 1), 40),
            "erase": bool(content.get("erase", False)),
        })

    async def _on_draw_clear(self, content):
        session = await self._active_draw_session()
        if not session:
            return
        drawer_slot = await self._draw_drawer_slot(session)
        my_slot = await self._draw_my_slot(session, self.user.id)
        if my_slot is None or my_slot != drawer_slot:
            return
        await self._broadcast("draw_clear", {})

    async def _on_draw_guess(self, content):
        """A guess. Validated on the SERVER — a client cannot declare itself
        correct. Correct guesses and near-misses are told only to the guesser;
        wrong guesses are relayed to the room as normal chat."""
        session = await self._active_draw_session()
        if not session:
            return
        my_slot = await self._draw_my_slot(session, self.user.id)
        if my_slot is None:
            return
        text = (content.get("text") or "").strip()[:60]
        if not text:
            return

        result = await self._draw_submit_guess(session.id, my_slot, text)
        name = await self._display_name(self.user.id)

        if result.get("blocked"):
            await self.send_json({"type": "draw_feedback",
                                  "detail": result.get("reason", "")})
            return

        if result.get("correct"):
            # tell the guesser what they scored…
            await self.send_json({"type": "draw_feedback",
                                  "correct": True,
                                  "points": result.get("points", 0)})
            # …and tell the room only THAT they got it — never the word
            await self._broadcast("draw_solved", {
                "user_id": self.user.public_id.hex,
                "name": name,
                "slot": my_slot,
                "points": result.get("points", 0),
            })
            if result.get("round_over"):
                await self._broadcast("draw_state", result["state"])
            else:
                await self._broadcast("draw_state",
                                      await self._draw_public_state(session.id))
            return

        if result.get("close"):
            # near-miss is PRIVATE: broadcasting "close!" would be a free hint
            await self.send_json({"type": "draw_feedback", "close": True})
            return

        if result.get("relay"):
            await self._broadcast("chat", {
                "user_id": self.user.public_id.hex,
                "name": name,
                "text": text,
            })

    # ---- DB helpers for Draw & Guess ----
    @database_sync_to_async
    def _active_draw_session(self):
        from games.models import GameSession
        return (GameSession.objects
                .filter(room_id=self.room_id,
                        definition__code="draw_guess",
                        status=GameSession.Status.PLAYING)
                .first())

    @database_sync_to_async
    def _draw_drawer_slot(self, session):
        st = session.state
        order = st.get("drawer_order", [])
        if not order:
            return None
        return order[st.get("drawer_index", 0) % len(order)]

    @database_sync_to_async
    def _draw_my_slot(self, session, user_id):
        p = session.players.filter(user_id=user_id).first()
        return p.seat_slot if p else None

    @database_sync_to_async
    def _draw_submit_guess(self, session_id, seat_slot, text):
        from games.draw_guess import DrawError, submit_guess
        try:
            return submit_guess(session_id=session_id, seat_slot=seat_slot, text=text)
        except DrawError:
            return {"blocked": True, "reason": "Not guessing right now."}

    @database_sync_to_async
    def _draw_public_state(self, session_id):
        from games.draw_guess import public_state
        from games.models import GameSession
        return public_state(GameSession.objects.get(id=session_id))
