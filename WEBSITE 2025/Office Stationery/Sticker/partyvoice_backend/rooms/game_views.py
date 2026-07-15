"""
rooms/game_views.py — auction + spin-game endpoints.

Each mutating call does the work in the service layer (which owns the money and
the truth) and then BROADCASTS the new state to the room's WebSocket group, so
every client sees the same bid / spin / payout at the same time. Without the
broadcast these rooms would be single-player.
"""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .auctions import (
    AuctionError, AuctionLot, close_lot, lot_state, place_bid, start_lot,
)
from .models import Room
from .spin_game import (
    SpinError, SpinRound, open_round, place_bet, round_state, settle_round,
)


def _broadcast(room_id: str, event_type: str, data: dict):
    """Push an event to everyone in the room's WebSocket group.

    Must match RoomConsumer.room_event's contract exactly: it expects
    {"type": "room_event", "event_type": <str>, "data": {...}} and re-emits
    {"type": <event_type>, **data} to clients, which is what the Flutter
    RoomSocket switches on.
    """
    layer = get_channel_layer()
    if layer is None:
        return
    async_to_sync(layer.group_send)(
        f"room_{room_id}",
        {"type": "room_event", "event_type": event_type, "data": data},
    )


def _room_or_404(room_id):
    return Room.objects.filter(room_id=room_id).first()


# ---------------- auction ----------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def auction_state(request, room_id):
    room = _room_or_404(room_id)
    if not room:
        return Response({"detail": "Room not found."}, status=status.HTTP_404_NOT_FOUND)
    lot = (AuctionLot.objects
           .filter(room=room, status__in=[AuctionLot.Status.LIVE,
                                          AuctionLot.Status.SCHEDULED])
           .select_related("current_leader")
           .first())
    if not lot:
        return Response({"lot": None})
    return Response({"lot": lot_state(lot)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def auction_create(request, room_id):
    """Host creates + starts a lot."""
    room = _room_or_404(room_id)
    if not room:
        return Response({"detail": "Room not found."}, status=status.HTTP_404_NOT_FOUND)
    if room.owner_id != request.user.id:
        return Response({"detail": "Only the host can list a lot."},
                        status=status.HTTP_403_FORBIDDEN)
    lot = AuctionLot.objects.create(
        room=room,
        name=request.data.get("name", "Untitled lot")[:120],
        subtitle=request.data.get("subtitle", "")[:200],
        emoji=request.data.get("emoji", "👑")[:8],
        starting_bid=int(request.data.get("starting_bid", 1000)),
        min_increment=int(request.data.get("min_increment", 1000)),
    )
    try:
        lot = start_lot(lot_id=lot.id,
                        duration_seconds=int(request.data.get("duration", 300)))
    except AuctionError as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    _broadcast(room.room_id, "auction_state", lot_state(lot))
    return Response(lot_state(lot), status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def auction_bid(request, room_id):
    room = _room_or_404(room_id)
    if not room:
        return Response({"detail": "Room not found."}, status=status.HTTP_404_NOT_FOUND)
    lot = AuctionLot.objects.filter(room=room, status=AuctionLot.Status.LIVE).first()
    if not lot:
        return Response({"detail": "No live auction."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        amount = int(request.data.get("amount", 0))
        result = place_bid(lot_id=lot.id, bidder_id=request.user.id, amount=amount)
    except (AuctionError, ValueError) as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    lot.refresh_from_db()
    _broadcast(room.room_id, "auction_bid",
               {**result, "top_bidders": lot_state(lot)["top_bidders"]})
    return Response(result)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def auction_close(request, room_id):
    room = _room_or_404(room_id)
    if not room:
        return Response({"detail": "Room not found."}, status=status.HTTP_404_NOT_FOUND)
    if room.owner_id != request.user.id:
        return Response({"detail": "Only the host can close the lot."},
                        status=status.HTTP_403_FORBIDDEN)
    lot = AuctionLot.objects.filter(room=room, status=AuctionLot.Status.LIVE).first()
    if not lot:
        return Response({"detail": "No live auction."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        result = close_lot(lot_id=lot.id)
    except AuctionError as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    _broadcast(room.room_id, "auction_closed", result)
    return Response(result)


# ---------------- spin game ----------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def spin_state(request, room_id):
    room = _room_or_404(room_id)
    if not room:
        return Response({"detail": "Room not found."}, status=status.HTTP_404_NOT_FOUND)
    rnd = SpinRound.objects.filter(room=room).first()
    if not rnd or rnd.status == SpinRound.Status.SETTLED:
        return Response({"round": None})
    return Response({"round": round_state(rnd)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def spin_open(request, room_id):
    """Open a new betting round (host, or a scheduled task)."""
    room = _room_or_404(room_id)
    if not room:
        return Response({"detail": "Room not found."}, status=status.HTTP_404_NOT_FOUND)
    if room.owner_id != request.user.id:
        return Response({"detail": "Only the host can start a round."},
                        status=status.HTTP_403_FORBIDDEN)
    rnd = open_round(room_id=room.id)
    _broadcast(room.room_id, "spin_round", round_state(rnd))
    return Response(round_state(rnd), status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def spin_bet(request, room_id):
    room = _room_or_404(room_id)
    if not room:
        return Response({"detail": "Room not found."}, status=status.HTTP_404_NOT_FOUND)
    rnd = SpinRound.objects.filter(room=room, status=SpinRound.Status.BETTING).first()
    if not rnd:
        return Response({"detail": "No open round."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        result = place_bet(
            round_id=rnd.id,
            user_id=request.user.id,
            symbol=request.data.get("symbol", ""),
            amount=int(request.data.get("amount", 0)),
        )
    except (SpinError, ValueError) as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    _broadcast(room.room_id, "spin_bet", result)
    return Response(result)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def spin_settle(request, room_id):
    """Land the wheel and pay out. Reveals the server seed so the round is
    verifiable: sha256(server_seed) must equal the hash published at open."""
    room = _room_or_404(room_id)
    if not room:
        return Response({"detail": "Room not found."}, status=status.HTTP_404_NOT_FOUND)
    rnd = (SpinRound.objects
           .filter(room=room)
           .exclude(status=SpinRound.Status.SETTLED)
           .first())
    if not rnd:
        return Response({"detail": "No round to settle."},
                        status=status.HTTP_400_BAD_REQUEST)

    try:
        result = settle_round(round_id=rnd.id)
    except SpinError as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    _broadcast(room.room_id, "spin_result", result)
    return Response(result)
