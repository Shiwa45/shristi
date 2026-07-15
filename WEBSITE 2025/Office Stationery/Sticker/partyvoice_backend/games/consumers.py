"""
games/consumers.py — Game state sync over Channels.

This is the transport behind the WebView game bridge. The HTML/JS game posts
moves up via postMessage -> Flutter -> this socket; the consumer fans them out
to all participants so every client's render stays in lockstep. Authoritative
checkpoints (turn changes, scores) are persisted to GameSession.state so a
reconnecting client can resync.

Separation of concerns:
  - move gossip (dice rolls, piece moves): broadcast + lightly persisted
  - lifecycle (start/settle): delegated to games.services (referee + economy)
"""

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer


class GameConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.group = f"game_{self.session_id}"

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4401)
            return
        session = await self._get_session(self.session_id)
        if session is None:
            await self.close(code=4404)
            return

        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        # resync: send the authoritative state snapshot to the joiner
        await self.send_json({"type": "game_state", "state": session.state,
                              "status": session.status, "seed": session.rng_seed})

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive_json(self, content, **kwargs):
        action = content.get("action")
        if action == "move":
            # gossip a move to everyone; optionally checkpoint authoritative bits
            payload = content.get("payload", {})
            checkpoint = content.get("checkpoint")  # server-relevant state delta
            if checkpoint:
                await self._merge_state(self.session_id, checkpoint)
            await self._broadcast("move", {
                "from": self.user.public_id.hex, "payload": payload})
        elif action == "chat":
            text = (content.get("text") or "").strip()[:200]
            if text:
                await self._broadcast("game_chat", {
                    "from": self.user.public_id.hex, "text": text})
        elif action == "sync_request":
            session = await self._get_session(self.session_id)
            if session:
                await self.send_json({"type": "game_state", "state": session.state,
                                      "status": session.status, "seed": session.rng_seed})
        else:
            await self.send_json({"type": "error", "detail": f"unknown action: {action}"})

    async def _broadcast(self, event_type, data):
        await self.channel_layer.group_send(
            self.group, {"type": "game_event", "event_type": event_type, "data": data})

    async def game_event(self, message):
        await self.send_json({"type": message["event_type"], **message["data"]})

    @database_sync_to_async
    def _get_session(self, sid):
        from .models import GameSession
        return GameSession.objects.filter(pk=sid).exclude(
            status=GameSession.Status.ABANDONED).first()

    @database_sync_to_async
    def _merge_state(self, sid, delta):
        from .models import GameSession
        session = GameSession.objects.filter(pk=sid).first()
        if not session:
            return
        state = session.state or {}
        state.update(delta)
        session.state = state
        session.save(update_fields=["state"])
