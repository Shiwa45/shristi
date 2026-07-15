"""
accounts/models.py — User identity for Phase 1.

A custom user keyed by a stable public id. The `zego_user_id` maps 1:1 to the
ZEGOCLOUD userID so RTC sessions are traceable back to a Django account.
Wallet/economy fields are intentionally NOT here — those arrive in Phase 2.
"""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # public, non-sequential id used in URLs and as the ZEGO userID basis
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # auth method bookkeeping (Phase 1 supports phone OTP + OAuth shells)
    phone = models.CharField(max_length=32, blank=True, null=True, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def zego_user_id(self) -> str:
        # ZEGO userIDs must be stable strings; hyphen-free for safety
        return self.public_id.hex

    def __str__(self):
        return f"{self.username} ({self.public_id})"


class Profile(models.Model):
    GENDER_CHOICES = [("u", "Unspecified"), ("m", "Male"), ("f", "Female")]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=40)
    avatar_url = models.URLField(blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default="u")
    bio = models.CharField(max_length=160, blank=True)
    region = models.CharField(max_length=8, blank=True)   # ISO country code
    language = models.CharField(max_length=8, default="en")

    # lightweight progression (full XP/level economy is Phase 2+)
    level = models.PositiveIntegerField(default=1)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name or self.user.username
