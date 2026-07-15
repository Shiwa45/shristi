"""
economy/views.py + payouts/views.py — Phase 2 REST API.

Money endpoints are deliberately thin: they validate input and delegate to the
service layer, which owns all the atomic/idempotent logic. Clients never send
authoritative amounts (coin packages and gift costs are server-side).
"""

import uuid

from redis.exceptions import RedisError

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from .gifts import Gift
from .gift_service import IAPValidationError, send_gift, validate_and_credit_iap
from .leaderboards import top_n, rank_of
from .models import Wallet
from .services import EconomyError, InsufficientFunds


# server-authoritative coin packages (product_id -> coins)
COIN_PACKAGES = {
    "coins_60": 60, "coins_300": 300, "coins_980": 980,
    "coins_1980": 1980, "coins_3280": 3280, "coins_6480": 6480,
}


class WalletView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        return Response({
            "coin_balance": wallet.coin_balance,
            "diamond_balance": wallet.diamond_balance,
            "lifetime_coins_spent": wallet.lifetime_coins_spent,
            "lifetime_diamonds_earned": wallet.lifetime_diamonds_earned,
        })


class GiftCatalogView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        gifts = Gift.objects.filter(is_active=True).order_by("sort_order", "coin_cost")
        return Response([{
            "code": g.code, "name": g.name, "tier": g.tier,
            "coin_cost": g.coin_cost, "diamond_value": g.diamond_value,
            "icon_url": g.icon_url, "animation_url": g.animation_url,
            "animation_type": g.animation_type,
        } for g in gifts])


class SendGiftView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        gift_code = request.data.get("gift_code")
        recipient_public_ids = request.data.get("recipient_ids", [])
        room_id = request.data.get("room_id", "")
        combo = int(request.data.get("combo", 1))
        # client supplies an idempotency key so retries don't double-charge
        idem = request.data.get("idempotency_key") or f"gift:{uuid.uuid4().hex}"

        if not gift_code or not recipient_public_ids:
            return Response({"detail": "gift_code and recipient_ids required"},
                            status=status.HTTP_400_BAD_REQUEST)

        recipients = list(
            User.objects.filter(public_id__in=recipient_public_ids).values_list("id", flat=True))
        if not recipients:
            return Response({"detail": "no valid recipients"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            event = send_gift(
                sender_id=request.user.id, recipient_ids=recipients,
                gift_code=gift_code, room_id=room_id, combo=combo, idempotency_key=idem)
        except InsufficientFunds:
            return Response({"detail": "Not enough coins."}, status=status.HTTP_402_PAYMENT_REQUIRED)
        except (EconomyError, Gift.DoesNotExist) as e:
            return Response({"detail": str(e) or "Invalid gift."}, status=status.HTTP_400_BAD_REQUEST)

        # Broadcast the gift to EVERYONE in the room.
        #
        # This runs server-side, after the ledger has actually moved the coins —
        # so the animation can never fire for a gift that wasn't paid for. It is
        # deliberately NOT trusted from the client: a client-sent broadcast could
        # be forged to fake gifts it never bought.
        if room_id:
            self._broadcast_gift(room_id, request.user, event, gift_code, combo)

        return Response({
            "ok": True, "event_id": event.id, "gift": gift_code,
            "recipients": event.recipient_count, "total_coin_cost": event.total_coin_cost,
        }, status=status.HTTP_201_CREATED)

    def _broadcast_gift(self, room_id, sender, event, gift_code, combo):
        layer = get_channel_layer()
        if layer is None:
            return
        gift = event.gift
        prof = getattr(sender, "profile", None)
        recipients = [
            (getattr(r.user, "profile", None).display_name
             if getattr(r.user, "profile", None) else r.user.username)
            for r in event.recipients.select_related("user", "user__profile")
        ]
        async_to_sync(layer.group_send)(
            f"room_{room_id}",
            {
                "type": "room_event",
                "event_type": "gift",
                "data": {
                    "sender_id": sender.public_id.hex,
                    "sender_name": prof.display_name if prof else sender.username,
                    "gift_code": gift_code,
                    "gift_name": gift.name,
                    "is_luxury": gift.tier == "luxury",
                    "combo": combo,
                    "recipient_name": recipients[0] if recipients else "",
                    "recipient_names": recipients,
                    # the SVGA/mp4 the clients should play, if the gift has one
                    "svga_url": gift.animation_url,
                    "total_coin_cost": event.total_coin_cost,
                },
            },
        )


class IAPValidateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get("product_id")
        purchase_token = request.data.get("purchase_token")
        if not product_id or not purchase_token:
            return Response({"detail": "product_id and purchase_token required"},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            result = validate_and_credit_iap(
                user_id=request.user.id, product_id=product_id,
                purchase_token=purchase_token, coin_packages=COIN_PACKAGES)
        except IAPValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"ok": True, "credited": result.created,
                         "transaction_id": result.transaction.id})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def leaderboard_view(request):
    metric = request.query_params.get("metric", "wealth")  # wealth|charm
    scope = request.query_params.get("scope", "global")
    period = request.query_params.get("period", "all")
    if metric not in ("wealth", "charm"):
        return Response({"detail": "metric must be wealth or charm"}, status=400)

    # Redis is a CACHE here, not the source of truth. If it's down (or simply
    # not running — the project is meant to boot with zero external services),
    # fall back to the wallet table rather than 500. A leaderboard that takes
    # the whole request down when the cache is cold is worse than a slightly
    # slower one.
    try:
        rows = top_n(metric, scope=scope, period=period, n=50)
        me = rank_of(metric, request.user.public_id.hex, scope=scope, period=period)
        return Response({
            "metric": metric, "scope": scope, "period": period,
            "top": [{"user_id": u, "score": s, "rank": r} for u, s, r in rows],
            "me": me,
            "source": "cache",
        })
    except RedisError:
        return Response(_leaderboard_from_db(metric, request.user))


def _leaderboard_from_db(metric, viewer):
    """Fallback: compute the ranking straight from the wallets."""
    field = "lifetime_coins_spent" if metric == "wealth" else "lifetime_diamonds_earned"
    qs = (Wallet.objects
          .select_related("user")
          .exclude(**{field: 0})
          .order_by(f"-{field}")[:50])

    top, me = [], None
    for i, w in enumerate(qs, start=1):
        entry = {
            "user_id": w.user.public_id.hex,
            "score": getattr(w, field),
            "rank": i,
        }
        top.append(entry)
        if w.user_id == viewer.id:
            me = entry

    return {
        "metric": metric, "scope": "global", "period": "all",
        "top": top, "me": me,
        "source": "db",   # so the client/ops can see the cache was bypassed
    }
