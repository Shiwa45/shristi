"""
events/models.py + services.py — Time-limited events engine.

A config-driven events system: each Event has a window, a type, and a reward
schedule. Players accrue progress against event tasks; rewards are claimed once.
Supports the common WePlay patterns: double-reward windows, contests
(leaderboard-ranked prizes), and milestone events.

Like all reward grants, payouts flow through the economy ledger with
idempotency keys derived from (event, user, milestone) so nothing double-pays.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class Event(models.Model):
    class Kind(models.TextChoices):
        MILESTONE = "milestone", "Milestone (accrue -> claim)"
        CONTEST = "contest", "Contest (leaderboard prizes)"
        DOUBLE = "double", "Double rewards window"

    code = models.SlugField(max_length=50, unique=True)
    title = models.CharField(max_length=100)
    kind = models.CharField(max_length=10, choices=Kind.choices)
    banner_url = models.URLField(blank=True)

    starts_at = models.DateTimeField(db_index=True)
    ends_at = models.DateTimeField(db_index=True)

    # what player action this event tracks, e.g. "gift_diamonds", "minutes_in_room"
    metric = models.CharField(max_length=40, blank=True)
    config = models.JSONField(default=dict, blank=True)  # multipliers, contest prize map
    is_active = models.BooleanField(default=True, db_index=True)

    @property
    def is_live(self) -> bool:
        now = timezone.now()
        return self.is_active and self.starts_at <= now <= self.ends_at


class EventMilestone(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="milestones")
    threshold = models.PositiveBigIntegerField()       # metric value to reach
    coin_reward = models.PositiveIntegerField(default=0)
    cosmetic_code = models.CharField(max_length=40, blank=True)

    class Meta:
        ordering = ["threshold"]


class EventProgress(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="progress")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="event_progress")
    value = models.PositiveBigIntegerField(default=0)
    claimed_milestone_ids = models.JSONField(default=list, blank=True)

    class Meta:
        unique_together = ("event", "user")


# ----------------------------- services -----------------------------

from django.db import transaction as db_txn

from economy.models import Currency, Transaction
from economy.services import credit


class EventError(Exception):
    pass


@db_txn.atomic
def accrue(*, event_code: str, user_id: int, amount: int) -> EventProgress:
    event = Event.objects.get(code=event_code)
    if not event.is_live:
        raise EventError("This event is not currently running.")
    prog, _ = EventProgress.objects.select_for_update().get_or_create(
        event=event, user_id=user_id)
    prog.value += max(0, amount)
    prog.save(update_fields=["value"])
    return prog


@db_txn.atomic
def claim_milestones(*, event_code: str, user_id: int) -> list:
    """Claim every reached-but-unclaimed milestone. Idempotent per milestone."""
    event = Event.objects.get(code=event_code)
    prog = EventProgress.objects.select_for_update().filter(
        event=event, user_id=user_id).first()
    if not prog:
        return []

    claimed_ids = set(prog.claimed_milestone_ids or [])
    newly = []
    for ms in event.milestones.all():
        if ms.id in claimed_ids:
            continue
        if prog.value >= ms.threshold:
            if ms.coin_reward:
                credit(user_id=user_id, currency=Currency.COIN, amount=ms.coin_reward,
                       txn_type=Transaction.Type.REWARD,
                       idempotency_key=f"event:{event_code}:{user_id}:ms{ms.id}",
                       initiator_id=None, system_source=True,
                       metadata={"reason": "event_milestone", "event": event_code, "milestone": ms.id})
            if ms.cosmetic_code:
                from inventory.services import grant_item
                grant_item(user_id=user_id, item_code=ms.cosmetic_code, source="event")
            claimed_ids.add(ms.id)
            newly.append(ms.id)

    prog.claimed_milestone_ids = list(claimed_ids)
    prog.save(update_fields=["claimed_milestone_ids"])
    return newly
