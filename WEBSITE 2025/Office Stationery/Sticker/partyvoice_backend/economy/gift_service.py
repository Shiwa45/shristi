"""
economy/gift_service.py — Gift sending + IAP top-up validation.

send_gift(): the room-facing money flow. Atomic, idempotent, multi-recipient.
validate_and_credit_iap(): server-side Google Play receipt validation -> mint coins.
"""

from django.db import transaction as db_txn

from .gifts import Gift, GiftEvent, GiftRecipient
from .leaderboards import add_score
from .models import Currency, Transaction
from .services import InsufficientFunds, EconomyError, credit, transfer


@db_txn.atomic
def send_gift(*, sender_id: int, recipient_ids: list[int], gift_code: str,
              room_id: str, combo: int, idempotency_key: str):
    """
    Charge the sender coin_cost * recipients * combo, award each recipient
    diamond_value * combo. One Transaction; one GiftEvent; N recipient credits.
    """
    if not recipient_ids:
        raise EconomyError("at least one recipient required")
    if combo < 1:
        raise EconomyError("combo must be >= 1")
    if sender_id in recipient_ids:
        raise EconomyError("cannot gift yourself")

    existing = Transaction.objects.filter(idempotency_key=idempotency_key).first()
    if existing:
        ev = existing.gift_events.first()
        return ev  # idempotent replay

    gift = Gift.objects.select_for_update().get(code=gift_code, is_active=True)
    n = len(recipient_ids)
    per_recipient_coins = gift.coin_cost * combo
    total_coins = per_recipient_coins * n
    per_recipient_diamonds = gift.diamond_value * combo

    # Charge sender once (the transfer to the first recipient carries the
    # full debit; remaining recipients get diamond credits in the same txn).
    # We model this as: one transfer for recipient[0], then credits for the rest,
    # all under the same idempotency-guarded Transaction created by transfer().
    first = recipient_ids[0]
    result = transfer(
        sender_id=sender_id, recipient_id=first,
        send_currency=Currency.COIN, send_amount=total_coins,
        recv_currency=Currency.DIAMOND, recv_amount=per_recipient_diamonds,
        txn_type=Transaction.Type.GIFT, idempotency_key=idempotency_key,
        metadata={"gift": gift_code, "room_id": room_id, "combo": combo, "recipients": n},
    )
    txn = result.transaction

    # additional recipients: credit diamonds within the same logical txn
    for rid in recipient_ids[1:]:
        credit(
            user_id=rid, currency=Currency.DIAMOND, amount=per_recipient_diamonds,
            txn_type=Transaction.Type.GIFT,
            idempotency_key=f"{idempotency_key}:r{rid}",
            initiator_id=sender_id, system_source=True,
            metadata={"gift": gift_code, "room_id": room_id, "via": txn.id},
        )

    event = GiftEvent.objects.create(
        sender_id=sender_id, gift=gift, room_id=room_id,
        recipient_count=n, combo=combo, total_coin_cost=total_coins, transaction=txn,
    )
    GiftRecipient.objects.bulk_create([
        GiftRecipient(event=event, user_id=rid, diamonds_awarded=per_recipient_diamonds)
        for rid in recipient_ids
    ])

    # Update the leaderboard cache: the sender's WEALTH (coins spent) and each
    # recipient's CHARM (diamonds earned). add_score never raises — if Redis is
    # down the gift still succeeds and the leaderboard view falls back to the
    # wallet table, which is the real source of truth.
    from accounts.models import User
    sender_pid = User.objects.values_list("public_id", flat=True).get(id=sender_id)
    add_score("wealth", sender_pid.hex, total_coins)
    for rid, pid in User.objects.filter(id__in=recipient_ids).values_list("id", "public_id"):
        add_score("charm", pid.hex, per_recipient_diamonds)

    return event


class IAPValidationError(Exception):
    pass


def validate_and_credit_iap(*, user_id: int, product_id: str, purchase_token: str,
                            coin_packages: dict, verifier=None):
    """
    Validate a Google Play purchase server-side, then mint coins.

    `coin_packages` maps product_id -> coin amount (server-authoritative; never
    trust a client-sent coin count). `verifier` is an injectable callable
    (purchase_token, product_id) -> dict for testability; in production it
    wraps the Google Play Developer API (androidpublisher.purchases.products.get).

    Idempotency key is the purchase_token, so replays never double-credit.
    """
    if product_id not in coin_packages:
        raise IAPValidationError(f"unknown product: {product_id}")

    verify = verifier or _google_play_verify
    receipt = verify(purchase_token, product_id)

    # Google Play: purchaseState 0 == purchased; consumptionState handled by us
    if receipt.get("purchaseState", 0) != 0:
        raise IAPValidationError("purchase not in PURCHASED state")

    coins = coin_packages[product_id]
    result = credit(
        user_id=user_id, currency=Currency.COIN, amount=coins,
        txn_type=Transaction.Type.TOPUP, idempotency_key=f"iap:{purchase_token}",
        initiator_id=user_id, system_source=True,
        metadata={"product_id": product_id, "order_id": receipt.get("orderId")},
    )
    return result


def _google_play_verify(purchase_token: str, product_id: str) -> dict:  # pragma: no cover
    """
    Production hook: call the Google Play Developer API to verify the token.
    Left as an integration point — wire a service account + googleapiclient here.
    Returning a real receipt dict on success; raising IAPValidationError otherwise.
    """
    raise IAPValidationError("Google Play verifier not configured")
