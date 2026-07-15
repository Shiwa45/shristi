"""
social/families.py — Families / clans.

Creation costs coins (reference WePlay: ~12,800). Role hierarchy:
manager > assistant_manager > senior > member. Family level (1-11) unlocks
perks: family voice rooms (9+), custom titles (10), custom frames (11), etc.
Family funds accumulate from member contributions and gate level-ups.
"""

from django.conf import settings
from django.db import models


FAMILY_CREATION_COST = 12800  # coins


class Family(models.Model):
    name = models.CharField(max_length=40, unique=True)
    logo_url = models.URLField(blank=True)
    notice = models.CharField(max_length=200, blank=True)

    level = models.PositiveSmallIntegerField(default=1)   # 1..11
    funds = models.BigIntegerField(default=0)             # accumulated contributions
    exp = models.BigIntegerField(default=0)               # toward next level

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="founded_families")
    created_at = models.DateTimeField(auto_now_add=True)

    # cosmetics unlocked by level
    custom_title = models.CharField(max_length=20, blank=True)   # lvl 10+
    custom_frame = models.CharField(max_length=40, blank=True)   # lvl 11+

    @property
    def can_have_voice_room(self) -> bool:
        return self.level >= 9

    @property
    def member_capacity(self) -> int:
        # capacity scales with level
        return 20 + self.level * 10

    def __str__(self):
        return f"{self.name} (L{self.level})"


class FamilyMember(models.Model):
    class Role(models.IntegerChoices):
        MEMBER = 0, "Member"
        SENIOR = 1, "Senior"
        ASSISTANT = 2, "Assistant manager"
        MANAGER = 3, "Manager"

    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name="members")
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="family_membership")
    role = models.IntegerField(choices=Role.choices, default=Role.MEMBER)
    contribution = models.BigIntegerField(default=0)   # lifetime coins contributed
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["family", "-contribution"])]

    @property
    def can_manage(self) -> bool:
        return self.role >= self.Role.ASSISTANT

    def __str__(self):
        return f"{self.user_id} @ {self.family_id} ({self.get_role_display()})"


class FamilyJoinRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name="join_requests")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="family_requests")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("family", "user")
