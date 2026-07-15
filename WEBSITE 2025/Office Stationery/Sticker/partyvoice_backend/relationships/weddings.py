"""
relationships/weddings.py — Weddings & marriage relationships.

A wedding is a ceremony held in a room; guests gift to fill affection/blessing
values. Marriage produces a ring on both profiles. Divorce comes in two forms:
consensual (free, mutual) and forced (unilateral, costs coins). Reunion within
a grace window restores affection/blessing.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


FORCED_DIVORCE_COST = 1000      # coins
REUNION_GRACE_DAYS = 30


class Ring(models.Model):
    """Ring catalog — cosmetic tiers bought with coins for proposals."""
    code = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=60)
    coin_cost = models.PositiveIntegerField()
    icon_url = models.URLField(blank=True)
    tier = models.PositiveSmallIntegerField(default=1)

    def __str__(self):
        return f"{self.name} ({self.coin_cost}c)"


class Marriage(models.Model):
    class Status(models.TextChoices):
        ENGAGED = "engaged", "Engaged (proposed)"
        MARRIED = "married", "Married"
        DIVORCED = "divorced", "Divorced"

    # ordered pair, partner_a is always the proposer
    partner_a = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="marriages_as_a")
    partner_b = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="marriages_as_b")
    ring = models.ForeignKey(Ring, on_delete=models.PROTECT, null=True, blank=True)

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ENGAGED, db_index=True)

    # values that fill from guest gifts during the ceremony / over the marriage
    affection = models.BigIntegerField(default=0)
    blessing = models.BigIntegerField(default=0)

    room_id = models.CharField(max_length=32, blank=True)  # ceremony room

    proposed_at = models.DateTimeField(auto_now_add=True)
    married_at = models.DateTimeField(null=True, blank=True)
    divorced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["partner_a", "status"]),
                   models.Index(fields=["partner_b", "status"])]

    def involves(self, user_id: int) -> bool:
        return user_id in (self.partner_a_id, self.partner_b_id)

    def partner_of(self, user_id: int) -> int:
        return self.partner_b_id if user_id == self.partner_a_id else self.partner_a_id

    @property
    def within_reunion_window(self) -> bool:
        if not self.divorced_at:
            return False
        return timezone.now() <= self.divorced_at + timezone.timedelta(days=REUNION_GRACE_DAYS)
