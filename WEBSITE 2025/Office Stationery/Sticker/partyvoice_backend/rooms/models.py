"""
rooms/models.py — Voice room + seat state (Phase 1 core).

Django is the source of truth for room lifecycle and seat ownership even
though audio media lives in ZEGOCLOUD. The Live Audio Room Kit renders seats;
this model authorizes and records who is allowed where.
"""

import secrets

from django.conf import settings
from django.db import models


def _gen_room_id() -> str:
    # short, URL-safe, collision-resistant room id used as the ZEGO roomID
    return secrets.token_hex(8)


class Room(models.Model):
    class Type(models.TextChoices):
        PUBLIC = "public", "Public"
        PRIVATE = "private", "Private (password)"
        EVENT = "event", "Event"

    class Status(models.TextChoices):
        LIVE = "live", "Live"
        CLOSED = "closed", "Closed"

    class Category(models.TextChoices):
        CHAT = "chat", "Chat"
        MUSIC = "music", "Music"
        GAMES = "games", "Games"
        DATING = "dating", "Dating"

    class RoomType(models.TextChoices):
        STANDARD = "standard", "Standard"
        WEDDING = "wedding", "Wedding"
        AUCTION = "auction", "Auction"
        PARTY = "party", "Party / Music"
        GAMING = "gaming", "Gaming"
        DATING_TYPE = "dating", "Dating"

    room_id = models.CharField(max_length=32, unique=True, default=_gen_room_id, db_index=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_rooms")
    admins = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="admin_rooms")

    title = models.CharField(max_length=60)
    type = models.CharField(max_length=10, choices=Type.choices, default=Type.PUBLIC)
    room_type = models.CharField(max_length=12, choices=RoomType.choices, default=RoomType.STANDARD, db_index=True)
    category = models.CharField(max_length=10, choices=Category.choices, default=Category.CHAT)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.LIVE, db_index=True)

    # password is hashed (set/verify via methods); blank for public rooms
    password_hash = models.CharField(max_length=128, blank=True)

    theme = models.CharField(max_length=40, blank=True)     # background/skin key
    cover_url = models.URLField(blank=True)
    seat_count = models.PositiveSmallIntegerField(default=8)  # excludes host seat

    # denormalized live counter, kept fresh by the consumer for cheap listing
    occupant_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "category"]),
            models.Index(fields=["status", "-occupant_count"]),  # hot-room sort
        ]

    def set_password(self, raw: str):
        from django.contrib.auth.hashers import make_password
        self.password_hash = make_password(raw) if raw else ""

    def check_password(self, raw: str) -> bool:
        from django.contrib.auth.hashers import check_password
        if not self.password_hash:
            return True
        return check_password(raw, self.password_hash)

    @property
    def is_locked(self) -> bool:
        return self.type == self.Type.PRIVATE and bool(self.password_hash)

    def __str__(self):
        return f"{self.title} [{self.room_id}]"


class SeatState(models.Model):
    """One row per seat index in a room. Index 0 is conventionally the host."""
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="seats")
    index = models.PositiveSmallIntegerField()
    occupant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="occupied_seats",
    )
    muted = models.BooleanField(default=False)   # host-muted
    locked = models.BooleanField(default=False)  # seat closed by host

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("room", "index")
        ordering = ["index"]

    def __str__(self):
        who = self.occupant_id or "empty"
        return f"{self.room.room_id} seat#{self.index} -> {who}"


class RoomBan(models.Model):
    """Room-scoped ban; account/device bans are a Phase 5 T&S concern."""
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="bans")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="room_bans")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("room", "user")


# Room-type templates + theme models live in room_types.py for readability;
# import them here so Django's app loader registers them under the rooms app.
from rooms.room_types import RoomTheme, RoomThemeOwnership  # noqa: E402,F401

# Auction + spin-game models live in their own modules for readability; import
# them here so Django's app loader registers them under the rooms app.
from rooms.auctions import AuctionBid, AuctionLot  # noqa: E402,F401
from rooms.spin_game import SpinBet, SpinRound  # noqa: E402,F401
