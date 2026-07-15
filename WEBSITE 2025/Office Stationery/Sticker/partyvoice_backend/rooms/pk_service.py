"""
PK battle scoring/settlement + ZEGOCLOUD In-app Chat Kit token endpoint.

pk_service: start a battle, attribute gift value to a side, settle on time-up.
chat token: DMs use the ZEGOCLOUD In-app Chat (ZIM) Kit, which needs its own
token (separate from the Live Audio Room token). The client requests it here
before opening a DM/group conversation. Same Token04 format, no room payload
(it's an identity token for the ZIM service).
"""

from django.conf import settings
from django.db import transaction as db_txn
from django.db.models import F
from django.utils import timezone

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from rtc.zego_token import generate_token04
from .pk_battles import PKBattle


class PKError(Exception):
    pass


@db_txn.atomic
def start_pk(*, a_user_id: int, b_user_id: int, room_a: str, room_b: str,
            duration_seconds: int = 300) -> PKBattle:
    if a_user_id == b_user_id:
        raise PKError("A host cannot PK themselves.")
    active = PKBattle.objects.filter(
        status=PKBattle.Status.ACTIVE
    ).filter(models_q(a_user_id, b_user_id)).exists()
    if active:
        raise PKError("One of these hosts is already in a PK.")
    return PKBattle.objects.create(
        side_a_user_id=a_user_id, side_b_user_id=b_user_id,
        room_a_id=room_a, room_b_id=room_b, duration_seconds=duration_seconds)


def models_q(a, b):
    from django.db.models import Q
    return (Q(side_a_user_id=a) | Q(side_b_user_id=a) |
            Q(side_a_user_id=b) | Q(side_b_user_id=b))


@db_txn.atomic
def attribute_gift(*, pk_id: int, recipient_user_id: int, diamond_value: int):
    """Called from the gift flow when a gift lands during an active PK."""
    pk = PKBattle.objects.select_for_update().get(pk=pk_id)
    if not pk.is_live:
        return pk
    if recipient_user_id == pk.side_a_user_id:
        PKBattle.objects.filter(pk=pk_id).update(score_a=F("score_a") + diamond_value)
    elif recipient_user_id == pk.side_b_user_id:
        PKBattle.objects.filter(pk=pk_id).update(score_b=F("score_b") + diamond_value)
    pk.refresh_from_db()
    return pk


@db_txn.atomic
def settle_pk(*, pk_id: int) -> PKBattle:
    pk = PKBattle.objects.select_for_update().get(pk=pk_id)
    if pk.status == PKBattle.Status.FINISHED:
        return pk
    pk.status = PKBattle.Status.FINISHED
    pk.finished_at = timezone.now()
    if pk.score_a > pk.score_b:
        pk.winner_id = pk.side_a_user_id
    elif pk.score_b > pk.score_a:
        pk.winner_id = pk.side_b_user_id
    else:
        pk.winner_id = None  # draw
    pk.save(update_fields=["status", "finished_at", "winner"])
    return pk


class ChatTokenView(APIView):
    """
    POST /api/chat/token
    Mints a ZEGOCLOUD In-app Chat (ZIM) identity token for DMs/group chat.
    No room payload — this authorizes the user against the ZIM service.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "rtc_token"

    def post(self, request):
        if not settings.ZEGO_APP_ID or len(settings.ZEGO_SERVER_SECRET) != 32:
            return Response({"detail": "Chat is not configured."}, status=503)
        token = generate_token04(
            app_id=settings.ZEGO_APP_ID,
            user_id=request.user.zego_user_id,
            server_secret=settings.ZEGO_SERVER_SECRET,
            effective_time_seconds=settings.ZEGO_TOKEN_TTL_SECONDS,
            payload="",  # identity token (no room/stream privilege)
        )
        return Response({
            "token": token,
            "app_id": settings.ZEGO_APP_ID,
            "user_id": request.user.zego_user_id,
            "expires_in": settings.ZEGO_TOKEN_TTL_SECONDS,
        })
