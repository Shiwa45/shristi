"""
rooms/auctions.py — live auction rooms.

Design decisions that matter:
  * The SERVER owns the price. A bid is only valid if it beats the current bid
    by at least `min_increment`; ties and stale bids are rejected.
  * Bids are ESCROWED, not just recorded. When you bid, coins leave your wallet
    immediately (so you can't bid coins you don't have, or spend them twice).
    When you're outbid, they're refunded in full. The winner's escrow is
    settled to the seller/house on close.
  * Anti-snipe: a bid inside the final `ANTI_SNIPE_WINDOW` extends the auction,
    so a last-millisecond bid can't steal the lot.
  * Every coin move goes through the double-entry ledger with an idempotency
    key, so a retried bid can't double-charge.
"""

from datetime import timedelta

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from economy.models import Currency, Transaction
from economy.services import InsufficientFunds, credit, debit

ANTI_SNIPE_WINDOW = timedelta(seconds=15)
ANTI_SNIPE_EXTENSION = timedelta(seconds=15)


class AuctionError(Exception):
    """Bid rejected (too low, closed, insufficient funds, self-outbid…)."""


class AuctionLot(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        LIVE = "live", "Live"
        SOLD = "sold", "Sold"
        UNSOLD = "unsold", "Unsold (no bids)"
        CANCELLED = "cancelled", "Cancelled"

    room = models.ForeignKey("rooms.Room", on_delete=models.CASCADE,
                             related_name="auction_lots")
    name = models.CharField(max_length=120)
    subtitle = models.CharField(max_length=200, blank=True)
    emoji = models.CharField(max_length=8, default="👑")
    image_url = models.URLField(blank=True)

    starting_bid = models.PositiveIntegerField(default=1000)
    min_increment = models.PositiveIntegerField(default=1000)
    current_bid = models.PositiveIntegerField(default=0)
    current_leader = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="leading_lots")

    status = models.CharField(max_length=12, choices=Status.choices,
                              default=Status.SCHEDULED, db_index=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.status})"

    @property
    def next_min_bid(self) -> int:
        if self.current_bid == 0:
            return self.starting_bid
        return self.current_bid + self.min_increment

    @property
    def seconds_left(self) -> int:
        if not self.ends_at:
            return 0
        return max(0, int((self.ends_at - timezone.now()).total_seconds()))


class AuctionBid(models.Model):
    """One bid. `is_active` marks the bid whose coins are still escrowed."""
    lot = models.ForeignKey(AuctionLot, on_delete=models.CASCADE, related_name="bids")
    bidder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name="auction_bids")
    amount = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)  # escrow still held
    refunded = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-amount", "created_at"]
        indexes = [models.Index(fields=["lot", "-amount"])]


# ---------------- service ----------------

def start_lot(*, lot_id: int, duration_seconds: int = 300) -> AuctionLot:
    with transaction.atomic():
        lot = AuctionLot.objects.select_for_update().get(id=lot_id)
        if lot.status != AuctionLot.Status.SCHEDULED:
            raise AuctionError("Lot is not scheduled.")
        lot.status = AuctionLot.Status.LIVE
        lot.ends_at = timezone.now() + timedelta(seconds=duration_seconds)
        lot.save(update_fields=["status", "ends_at"])
    return lot


@transaction.atomic
def place_bid(*, lot_id: int, bidder_id: int, amount: int) -> dict:
    """Place a bid: validate, escrow the coins, refund the previous leader.

    Returns a dict suitable for broadcasting to the room.
    """
    lot = AuctionLot.objects.select_for_update().get(id=lot_id)

    if lot.status != AuctionLot.Status.LIVE:
        raise AuctionError("This auction isn't live.")
    if lot.ends_at and timezone.now() >= lot.ends_at:
        raise AuctionError("This auction has ended.")
    if lot.current_leader_id == bidder_id:
        raise AuctionError("You're already the highest bidder.")
    if amount < lot.next_min_bid:
        raise AuctionError(f"Bid must be at least {lot.next_min_bid}.")

    # escrow the new bid: coins leave the bidder's wallet now
    try:
        debit(
            bidder_id, Currency.COIN, amount,
            txn_type=Transaction.Type.PURCHASE,
            idempotency_key=f"auction:bid:{lot.id}:{bidder_id}:{amount}",
            initiator_id=bidder_id,
            system_sink=True,  # held by the house until settle/refund
            metadata={"reason": "auction_bid", "lot": lot.id},
        )
    except InsufficientFunds:
        raise AuctionError("Not enough coins for this bid.")

    # refund the previous leader's escrow
    previous = (AuctionBid.objects
                .select_for_update()
                .filter(lot=lot, is_active=True, refunded=False)
                .first())
    if previous:
        credit(
            previous.bidder_id, Currency.COIN, previous.amount,
            txn_type=Transaction.Type.REFUND,
            idempotency_key=f"auction:refund:{lot.id}:{previous.id}",
            initiator_id=None,
            system_source=True,
            metadata={"reason": "auction_outbid", "lot": lot.id},
        )
        previous.is_active = False
        previous.refunded = True
        previous.save(update_fields=["is_active", "refunded"])

    bid = AuctionBid.objects.create(lot=lot, bidder_id=bidder_id, amount=amount)

    lot.current_bid = amount
    lot.current_leader_id = bidder_id
    # anti-snipe: a late bid extends the clock
    extended = False
    if lot.ends_at and (lot.ends_at - timezone.now()) < ANTI_SNIPE_WINDOW:
        lot.ends_at = timezone.now() + ANTI_SNIPE_EXTENSION
        extended = True
    lot.save(update_fields=["current_bid", "current_leader", "ends_at"])

    return {
        "lot_id": lot.id,
        "current_bid": lot.current_bid,
        "leader_id": bid.bidder.public_id.hex,
        "leader_name": _display_name(bid.bidder),
        "next_min_bid": lot.next_min_bid,
        "seconds_left": lot.seconds_left,
        "extended": extended,
        "outbid_user_id": previous.bidder.public_id.hex if previous else None,
    }


@transaction.atomic
def close_lot(*, lot_id: int) -> dict:
    """Settle the auction. Winner's escrow is already held; award the lot.
    No bids -> mark unsold (nothing to refund; nothing was escrowed)."""
    lot = AuctionLot.objects.select_for_update().get(id=lot_id)
    if lot.status != AuctionLot.Status.LIVE:
        raise AuctionError("Lot is not live.")

    winning = (AuctionBid.objects
               .select_for_update()
               .filter(lot=lot, is_active=True, refunded=False)
               .first())

    if not winning:
        lot.status = AuctionLot.Status.UNSOLD
        lot.save(update_fields=["status"])
        return {"lot_id": lot.id, "status": lot.status, "winner": None}

    # winner's coins stay with the house (already debited). Mark settled.
    winning.is_active = False
    winning.save(update_fields=["is_active"])

    lot.status = AuctionLot.Status.SOLD
    lot.save(update_fields=["status"])

    # Award the item: grant the cosmetic/VIP here if the lot maps to one.
    # (Inventory grant is left to the caller so lots stay generic.)
    return {
        "lot_id": lot.id,
        "status": lot.status,
        "winner": {
            "user_id": winning.bidder.public_id.hex,
            "name": _display_name(winning.bidder),
            "amount": winning.amount,
        },
    }


def top_bidders(lot: AuctionLot, limit: int = 5):
    """Highest distinct bidders, for the room's leaderboard."""
    seen, out = set(), []
    for b in lot.bids.select_related("bidder", "bidder__profile").all():
        if b.bidder_id in seen:
            continue
        seen.add(b.bidder_id)
        out.append({
            "user_id": b.bidder.public_id.hex,
            "name": _display_name(b.bidder),
            "amount": b.amount,
        })
        if len(out) >= limit:
            break
    return out


def lot_state(lot: AuctionLot) -> dict:
    return {
        "lot_id": lot.id,
        "name": lot.name,
        "subtitle": lot.subtitle,
        "emoji": lot.emoji,
        "image_url": lot.image_url,
        "status": lot.status,
        "current_bid": lot.current_bid,
        "next_min_bid": lot.next_min_bid,
        "seconds_left": lot.seconds_left,
        "leader_name": _display_name(lot.current_leader) if lot.current_leader else None,
        "top_bidders": top_bidders(lot),
    }


def _display_name(user) -> str:
    prof = getattr(user, "profile", None)
    return prof.display_name if prof and prof.display_name else user.username
