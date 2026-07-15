"""
games/draw_views.py — "Draw & Guess" lifecycle endpoints.

Only the LOW-FREQUENCY actions live here (create / join / start / my-word /
end-round). The high-frequency stuff — brush strokes and guesses — goes through
the WebSocket consumer, because an HTTP round-trip per brush point would make
drawing feel like mud and would hammer the DB for disposable data.
"""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rooms.models import Room

from .draw_guess import (
    MAX_PLAYERS, MIN_PLAYERS, DrawError, drawer_state, end_round, leave_game,
    public_state, start_game,
)
from .models import GameDefinition, GamePlayer, GameSession

DRAW_CODE = "draw_guess"


def _broadcast(room_id: str, event_type: str, data: dict):
    layer = get_channel_layer()
    if layer is None:
        return
    async_to_sync(layer.group_send)(
        f"room_{room_id}",
        {"type": "room_event", "event_type": event_type, "data": data},
    )


def _session(room_id):
    return (GameSession.objects
            .filter(room_id=room_id, definition__code=DRAW_CODE)
            .exclude(status__in=[GameSession.Status.FINISHED,
                                 GameSession.Status.ABANDONED])
            .order_by("-created_at")
            .first())


def _my_slot(session, user):
    p = session.players.filter(user=user).first()
    return p.seat_slot if p else None


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def draw_state(request, room_id):
    session = _session(room_id)
    if not session:
        return Response({"session": None})
    return Response({"session": public_state(session)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def draw_create(request, room_id):
    room = Room.objects.filter(room_id=room_id).first()
    if not room:
        return Response({"detail": "Room not found."}, status=status.HTTP_404_NOT_FOUND)
    if room.owner_id != request.user.id:
        return Response({"detail": "Only the host can start a game."},
                        status=status.HTTP_403_FORBIDDEN)
    if _session(room_id):
        return Response({"detail": "A game is already running."},
                        status=status.HTTP_400_BAD_REQUEST)

    definition, _ = GameDefinition.objects.get_or_create(
        code=DRAW_CODE,
        defaults={
            "name": "Draw & Guess",
            "min_players": MIN_PLAYERS,
            "max_players": MAX_PLAYERS,
            "bundle_url": "",   # native Flutter canvas, not a WebView
            "is_active": True,
        },
    )
    session = GameSession.objects.create(
        definition=definition, room_id=room_id, host=request.user,
        status=GameSession.Status.LOBBY, state={"phase": "lobby"},
    )
    GamePlayer.objects.create(session=session, user=request.user, seat_slot=0)

    data = public_state(session)
    _broadcast(room_id, "draw_state", data)
    return Response(data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def draw_join(request, room_id):
    session = _session(room_id)
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
    _broadcast(room_id, "draw_state", data)
    return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def draw_start(request, room_id):
    session = _session(room_id)
    if not session:
        return Response({"detail": "No game."}, status=status.HTTP_400_BAD_REQUEST)
    if session.host_id != request.user.id:
        return Response({"detail": "Only the host can start."},
                        status=status.HTTP_403_FORBIDDEN)
    try:
        data = start_game(session_id=session.id)
    except DrawError as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # public state carries a MASKED hint, never the word
    _broadcast(room_id, "draw_state", data)
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def draw_my_word(request, room_id):
    """Only the current drawer can read this."""
    session = _session(room_id)
    if not session or session.status != GameSession.Status.PLAYING:
        return Response({"detail": "No active game."},
                        status=status.HTTP_400_BAD_REQUEST)
    slot = _my_slot(session, request.user)
    if slot is None:
        return Response({"detail": "You're not in this game."},
                        status=status.HTTP_403_FORBIDDEN)
    try:
        return Response(drawer_state(session, slot))
    except DrawError as e:
        return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def draw_end_round(request, room_id):
    """Time's up. (The host's client calls this; the server re-checks state, so
    a client can't end a round early to escape a bad drawing.)"""
    session = _session(room_id)
    if not session:
        return Response({"detail": "No game."}, status=status.HTTP_400_BAD_REQUEST)
    if session.host_id != request.user.id:
        return Response({"detail": "Only the host can end the round."},
                        status=status.HTTP_403_FORBIDDEN)
    data = end_round(session_id=session.id)
    _broadcast(room_id, "draw_state", data)
    return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def draw_leave(request, room_id):
    session = _session(room_id)
    if not session:
        return Response({"detail": "No game."}, status=status.HTTP_400_BAD_REQUEST)
    slot = _my_slot(session, request.user)
    if slot is None:
        return Response({"detail": "You're not in this game."},
                        status=status.HTTP_403_FORBIDDEN)
    data = leave_game(session_id=session.id, seat_slot=slot)
    _broadcast(room_id, "draw_state", data)
    return Response(data)
