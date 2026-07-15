"""
games/spy_views.py — "Who's the Spy" endpoints.

The one thing that must not go wrong here: SECRETS.
Public state (broadcast to the room) never contains the words or the spy's
identity. Each player fetches their OWN word from /my-role, which returns only
their private payload. Get this wrong and the game is unplayable.
"""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rooms.models import Room

from .models import GameDefinition, GamePlayer, GameSession
from .whos_spy import (
    MAX_PLAYERS, MIN_PLAYERS, SpyError, cast_vote, leave_game, private_state,
    public_state, start_game, submit_description,
)

SPY_CODE = "whos_spy"


def _broadcast(room_id: str, event_type: str, data: dict):
    """Push PUBLIC game state to the room. Never call this with secrets."""
    layer = get_channel_layer()
    if layer is None:
        return
    async_to_sync(layer.group_send)(
        f"room_{room_id}",
        {"type": "room_event", "event_type": event_type, "data": data},
    )


def _session_for_room(room_id):
    return (GameSession.objects
            .filter(room_id=room_id)
            .exclude(status=GameSession.Status.FINISHED)
            .order_by("-created_at")
            .first())


def _my_slot(session, user):
    p = session.players.filter(user=user).first()
    return p.seat_slot if p else None


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def spy_state(request, room_id):
    session = _session_for_room(room_id)
    if not session:
        return Response({"session": None})
    return Response({"session": public_state(session)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def spy_create(request, room_id):
    """Host opens a lobby. Players join, then the host starts."""
    room = Room.objects.filter(room_id=room_id).first()
    if not room:
        return Response({"detail": "Room not found."}, status=status.HTTP_404_NOT_FOUND)
    if room.owner_id != request.user.id:
        return Response({"detail": "Only the host can start a game."},
                        status=status.HTTP_403_FORBIDDEN)
    if _session_for_room(room_id):
        return Response({"detail": "A game is already running."},
                        status=status.HTTP_400_BAD_REQUEST)

    definition, _ = GameDefinition.objects.get_or_create(
        code=SPY_CODE,
        defaults={
            "name": "Who's the Spy",
            "min_players": MIN_PLAYERS,
            "max_players": MAX_PLAYERS,
            "bundle_url": "",   # native Flutter UI, not a WebView bundle
            "is_active": True,
        },
    )
    stake = int(request.data.get("stake_coins", 0))
    session = GameSession.objects.create(
        definition=definition,
        room_id=room_id,
        host=request.user,
        stake_coins=max(0, stake),
        status=GameSession.Status.LOBBY,
        state={"phase": "lobby"},
    )
    # the host takes slot 0
    GamePlayer.objects.create(session=session, user=request.user, seat_slot=0)

    data = public_state(session)
    _broadcast(room_id, "spy_state", data)
    return Response(data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def spy_join(request, room_id):
    session = _session_for_room(room_id)
    if not session:
        return Response({"detail": "No game to join."}, status=status.HTTP_400_BAD_REQUEST)
    if session.status != GameSession.Status.LOBBY:
        return Response({"detail": "Game already started."},
                        status=status.HTTP_400_BAD_REQUEST)
    if session.players.filter(user=request.user).exists():
        return Response(public_state(session))
    if session.players.count() >= MAX_PLAYERS:
        return Response({"detail": "Game is full."}, status=status.HTTP_400_BAD_REQUEST)

    used = set(session.players.values_list("seat_slot", flat=True))
    slot = next(i for i in range(MAX_PLAYERS) if i not in used)
    GamePlayer.objects.create(session=session, user=request.user, seat_slot=slot)

    data = public_state(session)
    _broadcast(room_id, "spy_state", data)
    return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def spy_start(request, room_id):
    session = _session_for_room(room_id)
    if not session:
        return Response({"detail": "No game."}, status=status.HTTP_400_BAD_REQUEST)
    if session.host_id != request.user.id:
        return Response({"detail": "Only the host can start."},
                        status=status.HTTP_403_FORBIDDEN)
    try:
        data = start_game(session_id=session.id)
    except SpyError as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # Broadcast PUBLIC state only. Each player then pulls their own secret word
    # from /my-role — the word is never in a room-wide message.
    _broadcast(room_id, "spy_state", data)
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def spy_my_role(request, room_id):
    """Your word, and whether you're the spy. Private to you."""
    session = _session_for_room(room_id)
    if not session or session.status != GameSession.Status.PLAYING:
        return Response({"detail": "No active game."},
                        status=status.HTTP_400_BAD_REQUEST)
    slot = _my_slot(session, request.user)
    if slot is None:
        return Response({"detail": "You're not in this game."},
                        status=status.HTTP_403_FORBIDDEN)
    return Response(private_state(session, slot))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def spy_describe(request, room_id):
    session = _session_for_room(room_id)
    if not session:
        return Response({"detail": "No game."}, status=status.HTTP_400_BAD_REQUEST)
    slot = _my_slot(session, request.user)
    if slot is None:
        return Response({"detail": "You're not in this game."},
                        status=status.HTTP_403_FORBIDDEN)
    try:
        data = submit_description(
            session_id=session.id, seat_slot=slot,
            text=request.data.get("text", ""))
    except SpyError as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    _broadcast(room_id, "spy_state", data)
    return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def spy_vote(request, room_id):
    session = _session_for_room(room_id)
    if not session:
        return Response({"detail": "No game."}, status=status.HTTP_400_BAD_REQUEST)
    slot = _my_slot(session, request.user)
    if slot is None:
        return Response({"detail": "You're not in this game."},
                        status=status.HTTP_403_FORBIDDEN)
    try:
        data = cast_vote(
            session_id=session.id, voter_slot=slot,
            target_slot=int(request.data.get("target_slot", -1)))
    except (SpyError, ValueError) as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    _broadcast(room_id, "spy_state", data)
    return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def spy_leave(request, room_id):
    session = _session_for_room(room_id)
    if not session:
        return Response({"detail": "No game."}, status=status.HTTP_400_BAD_REQUEST)
    slot = _my_slot(session, request.user)
    if slot is None:
        return Response({"detail": "You're not in this game."},
                        status=status.HTTP_403_FORBIDDEN)
    data = leave_game(session_id=session.id, seat_slot=slot)
    _broadcast(room_id, "spy_state", data)
    return Response(data)
