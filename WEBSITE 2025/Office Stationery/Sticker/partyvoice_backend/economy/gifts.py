"""
economy/gifts.py — Gift catalog + gift-send records.

Gifts cost coins (sender) and award diamonds (recipient). The diamond award is
typically a fraction of the coin cost (the platform take-rate is the spread).
Animations are delivered as asset URLs (SVGA/Lottie) the client plays.
"""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Gift(models.Model):
    class Tier(models.TextChoices):
        BASIC = "basic", "Basic"
        ANIMATED = "animated", "Animated"
        LUXURY = "luxury", "Luxury"

    code = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=60)
    tier = models.CharField(max_length=10, choices=Tier.choices, default=Tier.BASIC)

    coin_cost = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    # diamonds awarded to recipient; <= coin_cost (spread = platform revenue)
    diamond_value = models.PositiveIntegerField(validators=[MinValueValidator(0)])

    icon_url = models.URLField(blank=True)
    animation_url = models.URLField(blank=True)   # SVGA/Lottie
    animation_type = models.CharField(max_length=10, default="svga")

    is_active = models.BooleanField(default=True, db_index=True)
    sort_order = models.IntegerField(default=0)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.diamond_value > self.coin_cost:
            raise ValidationError("diamond_value cannot exceed coin_cost.")

    def __str__(self):
        return f"{self.name} ({self.coin_cost}c)"


class GiftEvent(models.Model):
    """
    An instance of a gift being sent. May target multiple recipients (e.g.
    'gift all seats') — one GiftEvent, N recipient credits in the ledger.
    """
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="gifts_sent")
    gift = models.ForeignKey(Gift, on_delete=models.PROTECT, related_name="events")
    room_id = models.CharField(max_length=32, db_index=True, blank=True)

    recipient_count = models.PositiveIntegerField(default=1)
    combo = models.PositiveIntegerField(default=1)  # combo multiplier

    total_coin_cost = models.PositiveIntegerField()
    transaction = models.ForeignKey(
        "economy.Transaction", on_delete=models.PROTECT, related_name="gift_events")

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["room_id", "-created_at"])]

    def __str__(self):
        return f"GiftEvent<{self.id}> {self.gift.code} x{self.recipient_count}"


class GiftRecipient(models.Model):
    event = models.ForeignKey(GiftEvent, on_delete=models.CASCADE, related_name="recipients")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="gifts_received")
    diamonds_awarded = models.PositiveIntegerField()

    class Meta:
        unique_together = ("event", "user")
