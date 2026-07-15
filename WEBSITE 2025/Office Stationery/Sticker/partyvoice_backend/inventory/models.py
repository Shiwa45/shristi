"""
inventory/models.py + services.py — Cosmetic items & user inventory.

Cosmetics are the Phase-4 avatar layer: frames, chat bubbles, entrance effects,
name colors, badges, and (later) 3D avatar parts. Items are catalog-defined;
ownership is per-user; one item per slot can be "equipped".

The 3D avatar engine itself (face-pinching/cloth-changing) is a client concern;
the backend just owns the catalog, ownership, and equip state.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class CosmeticItem(models.Model):
    class Slot(models.TextChoices):
        AVATAR_FRAME = "frame", "Avatar frame"
        CHAT_BUBBLE = "bubble", "Chat bubble"
        ENTRANCE = "entrance", "Entrance effect"
        NAME_COLOR = "name_color", "Name color"
        BADGE = "badge", "Badge"
        AVATAR_PART = "avatar_part", "3D avatar part"

    code = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=60)
    slot = models.CharField(max_length=15, choices=Slot.choices, db_index=True)
    asset_url = models.URLField(blank=True)
    coin_cost = models.PositiveIntegerField(default=0)     # 0 = not directly purchasable
    is_purchasable = models.BooleanField(default=False)
    vip_only_level = models.PositiveSmallIntegerField(default=0)  # 0 = no VIP gate

    def __str__(self):
        return f"{self.name} [{self.slot}]"


class InventoryItem(models.Model):
    class Source(models.TextChoices):
        PURCHASE = "purchase", "Purchase"
        LOOT = "loot", "Loot box"
        EVENT = "event", "Event reward"
        VIP = "vip", "VIP perk"
        GIFT = "gift", "Gift"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="inventory")
    item = models.ForeignKey(CosmeticItem, on_delete=models.PROTECT, related_name="owned_by")
    source = models.CharField(max_length=10, choices=Source.choices)
    equipped = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)  # null = permanent
    acquired_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "item")
        indexes = [models.Index(fields=["user", "equipped"])]

    @property
    def is_expired(self) -> bool:
        return bool(self.expires_at and self.expires_at < timezone.now())


# ----------------------------- services -----------------------------

from django.db import transaction as db_txn

from economy.models import Currency, Transaction
from economy.services import InsufficientFunds, debit


class InventoryError(Exception):
    pass


@db_txn.atomic
def grant_item(*, user_id: int, item_code: str, source: str, days: int | None = None) -> InventoryItem:
    item = CosmeticItem.objects.get(code=item_code)
    expires = timezone.now() + timezone.timedelta(days=days) if days else None
    inv, created = InventoryItem.objects.get_or_create(
        user_id=user_id, item=item,
        defaults={"source": source, "expires_at": expires})
    if not created and expires:
        # extend a timed item
        base = inv.expires_at if (inv.expires_at and inv.expires_at > timezone.now()) else timezone.now()
        inv.expires_at = base + timezone.timedelta(days=days)
        inv.save(update_fields=["expires_at"])
    return inv


@db_txn.atomic
def purchase_item(*, user_id: int, item_code: str) -> InventoryItem:
    item = CosmeticItem.objects.get(code=item_code)
    if not item.is_purchasable or item.coin_cost <= 0:
        raise InventoryError("This item is not for sale.")
    try:
        debit(user_id=user_id, currency=Currency.COIN, amount=item.coin_cost,
              txn_type=Transaction.Type.PURCHASE,
              idempotency_key=f"cosmetic:{user_id}:{item_code}:{int(timezone.now().timestamp())}",
              initiator_id=user_id, system_sink=True,
              metadata={"reason": "cosmetic_purchase", "item": item_code})
    except InsufficientFunds:
        raise InventoryError("Not enough coins.")
    return grant_item(user_id=user_id, item_code=item_code,
                      source=InventoryItem.Source.PURCHASE)


@db_txn.atomic
def equip_item(*, user_id: int, item_code: str) -> InventoryItem:
    inv = InventoryItem.objects.select_related("item").get(user_id=user_id, item__code=item_code)
    if inv.is_expired:
        raise InventoryError("This item has expired.")
    # only one equipped item per slot — unequip others in the same slot
    InventoryItem.objects.filter(
        user_id=user_id, item__slot=inv.item.slot, equipped=True
    ).exclude(pk=inv.pk).update(equipped=False)
    inv.equipped = True
    inv.save(update_fields=["equipped"])
    return inv


def unequip_item(*, user_id: int, item_code: str):
    InventoryItem.objects.filter(user_id=user_id, item__code=item_code).update(equipped=False)


def equipped_loadout(*, user_id: int) -> dict:
    """The user's currently equipped cosmetics, keyed by slot."""
    out = {}
    for inv in InventoryItem.objects.filter(
        user_id=user_id, equipped=True).select_related("item"):
        if not inv.is_expired:
            out[inv.item.slot] = {"code": inv.item.code, "asset_url": inv.item.asset_url}
    return out
