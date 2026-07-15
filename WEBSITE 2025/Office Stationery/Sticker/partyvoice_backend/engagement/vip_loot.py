"""
engagement/vip_loot.py — VIP grant logic + loot boxes.

VIP:
  * purchasable tiers: pay monthly_coin_price -> set/extend expiry
  * wealth-derived tiers: recompute from lifetime coins spent (no expiry)
  Daily VIP perks (bonus coins, free loot boxes) are granted by a Celery job
  that calls grant_daily_vip_perks() for active VIPs.

Loot boxes:
  * weighted random reward draw with a published drop table (required for
    Google Play compliance — odds must be disclosed)
  * draws are atomic; rewards credited via the ledger
"""

import random

from django.db import transaction as db_txn
from django.utils import timezone

from economy.models import Currency, Transaction, Wallet
from economy.services import credit, debit
from .models import UserVip, VipTier


class VipError(Exception):
    pass


@db_txn.atomic
def purchase_vip(*, user_id: int, level: int, months: int = 1) -> UserVip:
    tier = VipTier.objects.get(level=level)
    if tier.monthly_coin_price <= 0:
        raise VipError("This tier is not purchasable.")
    cost = tier.monthly_coin_price * months
    from economy.services import InsufficientFunds
    try:
        debit(user_id=user_id, currency=Currency.COIN, amount=cost,
              txn_type=Transaction.Type.PURCHASE,
              idempotency_key=f"vip:{user_id}:{level}:{_now()}",
              initiator_id=user_id, system_sink=True,
              metadata={"reason": "vip_purchase", "level": level, "months": months})
    except InsufficientFunds:
        raise VipError("Not enough coins for that VIP plan.")

    uv, _ = UserVip.objects.get_or_create(user_id=user_id)
    base = uv.expires_at if (uv.expires_at and uv.expires_at > timezone.now()) else timezone.now()
    uv.tier = tier
    uv.expires_at = base + timezone.timedelta(days=30 * months)
    uv.save()
    return uv


def recompute_wealth_vip(*, user_id: int) -> UserVip:
    """Set the user's VIP to the highest wealth-threshold tier they qualify for."""
    wallet = Wallet.objects.filter(user_id=user_id).first()
    spent = wallet.lifetime_coins_spent if wallet else 0
    tier = VipTier.objects.filter(
        wealth_threshold__lte=spent, wealth_threshold__gt=0
    ).order_by("-level").first()
    uv, _ = UserVip.objects.get_or_create(user_id=user_id)
    # only upgrade via wealth; never downgrade a paid, unexpired tier
    if tier and (uv.tier is None or tier.level > uv.tier.level):
        if not (uv.expires_at and uv.expires_at > timezone.now()):
            uv.tier = tier
            uv.expires_at = None  # wealth tiers don't expire
            uv.save()
    return uv


@db_txn.atomic
def grant_daily_vip_perks(*, user_id: int, day_key: str):
    """Idempotent per (user, day): bonus coins + free loot box tickets."""
    uv = UserVip.objects.filter(user_id=user_id).select_related("tier").first()
    if not uv or not uv.is_active:
        return
    perks = uv.tier.perks or {}
    daily_coins = int(perks.get("daily_coins", 0))
    if daily_coins:
        credit(user_id=user_id, currency=Currency.COIN, amount=daily_coins,
               txn_type=Transaction.Type.REWARD,
               idempotency_key=f"vip-daily:{user_id}:{day_key}",
               initiator_id=None, system_source=True,
               metadata={"reason": "vip_daily_coins", "day": day_key})


# ----------------------------- Loot boxes -----------------------------

class LootBox(models.Model if False else object):
    pass  # placeholder to keep import symmetry; real model below


from django.db import models


class LootTable(models.Model):
    code = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=60)
    ticket_cost = models.PositiveIntegerField(default=0)  # coins per draw (0 = free/VIP)
    is_active = models.BooleanField(default=True)


class LootReward(models.Model):
    class Kind(models.TextChoices):
        COINS = "coins", "Coins"
        DIAMONDS = "diamonds", "Diamonds"
        COSMETIC = "cosmetic", "Cosmetic item"

    table = models.ForeignKey(LootTable, on_delete=models.CASCADE, related_name="rewards")
    kind = models.CharField(max_length=10, choices=Kind.choices)
    amount = models.PositiveIntegerField(default=0)        # for coins/diamonds
    cosmetic_code = models.CharField(max_length=40, blank=True)
    weight = models.PositiveIntegerField(default=1)        # relative draw weight
    # published probability is weight / sum(weights) — expose this in the client

    def __str__(self):
        return f"{self.table.code}:{self.kind}:{self.amount or self.cosmetic_code} (w{self.weight})"


class LootDrawError(Exception):
    pass


@db_txn.atomic
def draw_loot(*, user_id: int, table_code: str, draw_nonce: str):
    """
    One weighted draw. `draw_nonce` makes the draw idempotent (a retried
    network call returns the same result instead of charging again).
    """
    table = LootTable.objects.select_for_update().get(code=table_code, is_active=True)
    rewards = list(table.rewards.all())
    if not rewards:
        raise LootDrawError("This loot box has no rewards configured.")

    idem = f"loot:{user_id}:{table_code}:{draw_nonce}"
    existing = Transaction.objects.filter(idempotency_key=idem).first()
    if existing:
        return existing.metadata.get("reward")

    if table.ticket_cost:
        from economy.services import InsufficientFunds
        try:
            debit(user_id=user_id, currency=Currency.COIN, amount=table.ticket_cost,
                  txn_type=Transaction.Type.PURCHASE, idempotency_key=f"{idem}:ticket",
                  initiator_id=user_id, system_sink=True,
                  metadata={"reason": "loot_ticket", "table": table_code})
        except InsufficientFunds:
            raise LootDrawError("Not enough coins to open this box.")

    total = sum(r.weight for r in rewards)
    roll = random.randint(1, total)
    acc = 0
    chosen = rewards[-1]
    for r in rewards:
        acc += r.weight
        if roll <= acc:
            chosen = r
            break

    reward_desc = {"kind": chosen.kind, "amount": chosen.amount,
                   "cosmetic": chosen.cosmetic_code}

    if chosen.kind == LootReward.Kind.COINS and chosen.amount:
        credit(user_id=user_id, currency=Currency.COIN, amount=chosen.amount,
               txn_type=Transaction.Type.REWARD, idempotency_key=idem,
               initiator_id=None, system_source=True,
               metadata={"reason": "loot_reward", "reward": reward_desc})
    elif chosen.kind == LootReward.Kind.DIAMONDS and chosen.amount:
        credit(user_id=user_id, currency=Currency.DIAMOND, amount=chosen.amount,
               txn_type=Transaction.Type.REWARD, idempotency_key=idem,
               initiator_id=None, system_source=True,
               metadata={"reason": "loot_reward", "reward": reward_desc})
    else:
        # cosmetic: record the txn for idempotency, grant inventory item
        from inventory.services import grant_item  # local import avoids cycle
        Transaction.objects.create(
            type=Transaction.Type.REWARD, idempotency_key=idem,
            initiator_id=None, metadata={"reason": "loot_reward", "reward": reward_desc})
        grant_item(user_id=user_id, item_code=chosen.cosmetic_code, source="loot")

    return reward_desc


def _now() -> str:
    return str(int(timezone.now().timestamp()))
