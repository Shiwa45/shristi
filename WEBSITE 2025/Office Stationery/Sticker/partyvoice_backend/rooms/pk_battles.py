"""
rooms/pk_battles.py — Gift PK battles.

Two hosts (or two rooms) compete for a fixed window; whoever's side receives
more gift value (diamonds) wins. The video co-host link is carried by the
ZEGOCLOUD Live Streaming Kit; this module owns the scoring and outcome.

Gift events tagged with a pk_id during an active battle increment that side's
score. Settlement records the winner; rewards/badges are optional hooks.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class PKBattle(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        FINISHED = "finished", "Finished"
        CANCELLED = "cancelled", "Cancelled"

    side_a_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pk_as_a")
    side_b_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pk_as_b")
    room_a_id = models.CharField(max_length=32, blank=True)
    room_b_id = models.CharField(max_length=32, blank=True)

    score_a = models.BigIntegerField(default=0)   # diamond value to side A
    score_b = models.BigIntegerField(default=0)

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="pk_wins")

    duration_seconds = models.PositiveIntegerField(default=300)
    started_at = models.DateTimeField(auto_now_add=True)
    ends_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.ends_at:
            self.ends_at = timezone.now() + timezone.timedelta(seconds=self.duration_seconds)
        super().save(*args, **kwargs)

    @property
    def is_live(self) -> bool:
        return self.status == self.Status.ACTIVE and timezone.now() < self.ends_at
