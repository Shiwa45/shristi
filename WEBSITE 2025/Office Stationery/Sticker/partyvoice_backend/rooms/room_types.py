"""
rooms/room_types.py — Room type templates + theme catalog (WePlay-style).

A "room type" is a template that decides the seat layout and any special UI
(e.g. an auction has a host + a stage; a wedding has two special bride/groom
seats). A "theme" is a purchasable cosmetic background a room owner can apply.

These are config-driven so new types/themes ship without schema changes.
"""

from django.conf import settings
from django.db import models


# ---- Room type templates (static config, not DB rows) ----
# Each defines: label, seat layout (rows of counts), special seat indices,
# and a default theme key. The Flutter client reads this from the room detail.
ROOM_TYPE_TEMPLATES = {
    "standard": {
        "label": "Standard",
        "seat_rows": [1, 4, 4],          # host + 8 audience
        "special_seats": {},             # index -> role label
        "default_theme": "aurora",
        "blurb": "Classic voice room",
    },
    "wedding": {
        "label": "Wedding",
        "seat_rows": [2, 4, 4],          # bride+groom on top, guests below
        "special_seats": {0: "Groom", 1: "Bride"},
        "default_theme": "rose_gold",
        "blurb": "Host a ceremony with rings & blessings",
    },
    "auction": {
        "label": "Auction",
        "seat_rows": [1, 3, 3, 3],       # auctioneer + bidders
        "special_seats": {0: "Auctioneer"},
        "default_theme": "midnight_gold",
        "blurb": "Bid live with an auctioneer stage",
    },
    "party": {
        "label": "Party / Music",
        "seat_rows": [1, 4, 4],
        "special_seats": {0: "DJ"},
        "default_theme": "neon_pulse",
        "blurb": "Karaoke, music & celebration",
    },
    "gaming": {
        "label": "Gaming",
        "seat_rows": [1, 4, 4],
        "special_seats": {0: "Host"},
        "default_theme": "arena",
        "blurb": "Play mini-games together",
    },
    "dating": {
        "label": "Dating",
        "seat_rows": [1, 2, 2, 2],       # host + paired seats
        "special_seats": {0: "Host"},
        "default_theme": "blush",
        "blurb": "Meet someone new",
    },
}


def room_type_template(room_type: str) -> dict:
    return ROOM_TYPE_TEMPLATES.get(room_type, ROOM_TYPE_TEMPLATES["standard"])


def seat_count_for_type(room_type: str) -> int:
    rows = room_type_template(room_type)["seat_rows"]
    return sum(rows) - 1  # exclude the host/first seat from "audience" count


class RoomTheme(models.Model):
    """A purchasable room background theme. `assets` carries client render hints
    (gradient stops, image URL, accent colors) so the Flutter client can paint
    it without a code change per theme."""
    key = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=60)
    coin_cost = models.PositiveIntegerField(default=0)   # 0 = free/default
    preview_url = models.URLField(blank=True)
    # e.g. {"type":"gradient","colors":["#10256B","#071233"],"accent":"#FFC940",
    #       "image_url":"https://.../wedding.png","overlay":0.3}
    assets = models.JSONField(default=dict)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)
    sort_order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.key})"


class RoomThemeOwnership(models.Model):
    """Which themes a user owns (bought or granted). Default themes are free to
    everyone and need no ownership row."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="room_themes")
    theme = models.ForeignKey(RoomTheme, on_delete=models.CASCADE, related_name="owners")
    acquired_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "theme")
