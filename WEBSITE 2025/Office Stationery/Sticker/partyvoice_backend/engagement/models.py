"""
engagement/models.py — VIP, daily login, tasks/achievements, referrals.

These drive retention and are the coin *sources* that balance the gift sink.
All reward grants flow through economy.services.credit() with idempotency keys
derived from (user, reward, period) so a reward can never be double-claimed.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


# ----------------------------- VIP -----------------------------
class VipTier(models.Model):
    """Config-driven VIP tiers V1..V13. Perks stored as JSON for flexibility."""
    level = models.PositiveSmallIntegerField(unique=True)  # 1..13
    name = models.CharField(max_length=30)
    # cumulative wealth (coins spent) needed to reach this tier, OR purchasable
    wealth_threshold = models.BigIntegerField(default=0)
    monthly_coin_price = models.PositiveIntegerField(default=0)  # 0 = not purchasable

    perks = models.JSONField(default=dict)
    # e.g. {"daily_coins": 200, "free_loot_boxes": 2, "double_xp": true,
    #       "name_color": "#FFD700", "entrance_effect": "flames",
    #       "profile_visit_tracking": true, "chat_bubble": "gold"}

    class Meta:
        ordering = ["level"]

    def __str__(self):
        return f"V{self.level} {self.name}"


class UserVip(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vip")
    tier = models.ForeignKey(VipTier, on_delete=models.PROTECT, null=True, blank=True)
    # for purchased VIP; null for wealth-derived
    expires_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_active(self) -> bool:
        if self.tier is None:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True


# ----------------------- Daily login -----------------------
class DailyLoginReward(models.Model):
    """Escalating streak rewards; day_index 1..7 then loops/holds."""
    day_index = models.PositiveSmallIntegerField(unique=True)
    coin_reward = models.PositiveIntegerField()

    class Meta:
        ordering = ["day_index"]


class LoginStreak(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="login_streak")
    current_streak = models.PositiveIntegerField(default=0)
    last_claim_date = models.DateField(null=True, blank=True)


# --------------------- Tasks / achievements ---------------------
class Task(models.Model):
    class Cadence(models.TextChoices):
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
        ONCE = "once", "One-time (achievement)"

    code = models.SlugField(max_length=50, unique=True)
    title = models.CharField(max_length=80)
    cadence = models.CharField(max_length=8, choices=Cadence.choices)
    # event the task listens for, e.g. "gift_sent", "room_joined", "minutes_in_room"
    trigger_event = models.CharField(max_length=40)
    target_count = models.PositiveIntegerField(default=1)
    coin_reward = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)


class TaskProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="task_progress")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="progress")
    period_key = models.CharField(max_length=20)   # e.g. 2026-06-18 for daily
    count = models.PositiveIntegerField(default=0)
    claimed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "task", "period_key")


# ------------------------- Referrals -------------------------
class Referral(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        QUALIFIED = "qualified", "Qualified"  # invitee hit milestone
        REWARDED = "rewarded", "Rewarded"

    inviter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="referrals_made")
    invitee = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="referred_by")
    code = models.CharField(max_length=20, db_index=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    rewarded_at = models.DateTimeField(null=True, blank=True)


class RedeemCode(models.Model):
    code = models.CharField(max_length=32, unique=True, db_index=True)
    coin_reward = models.PositiveIntegerField(default=0)
    max_uses = models.PositiveIntegerField(default=1)
    use_count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    redeemed_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="RedeemRedemption", related_name="redeemed_codes")

    @property
    def is_redeemable(self) -> bool:
        if not self.is_active or self.use_count >= self.max_uses:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True


class RedeemRedemption(models.Model):
    code = models.ForeignKey(RedeemCode, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    redeemed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("code", "user")
