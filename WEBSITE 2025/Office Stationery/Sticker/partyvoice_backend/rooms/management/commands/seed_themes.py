"""Seed default room themes (one per room type) + a few premium ones."""
from django.core.management.base import BaseCommand

from rooms.room_types import RoomTheme

THEMES = [
    # key, name, cost, default, assets
    ("aurora", "Aurora", 0, True,
     {"type": "gradient", "colors": ["#10256B", "#071233"], "accent": "#FFC940"}),
    ("rose_gold", "Rose Gold", 0, True,
     {"type": "gradient", "colors": ["#5B2A4A", "#2A0E22"], "accent": "#FFB6C1"}),
    ("midnight_gold", "Midnight Gold", 0, True,
     {"type": "gradient", "colors": ["#1A1A2E", "#0A0A14"], "accent": "#FFD700"}),
    ("neon_pulse", "Neon Pulse", 0, True,
     {"type": "gradient", "colors": ["#2B0B5E", "#0E0322"], "accent": "#3FE08F"}),
    ("arena", "Arena", 0, True,
     {"type": "gradient", "colors": ["#0E2A3A", "#04141C"], "accent": "#4D7BFF"}),
    ("blush", "Blush", 0, True,
     {"type": "gradient", "colors": ["#5A2A3A", "#2A0E18"], "accent": "#FF8FA3"}),
    # premium (purchasable)
    ("galaxy", "Galaxy", 2000, False,
     {"type": "gradient", "colors": ["#1B0A4E", "#05021A"], "accent": "#A78BFA"}),
    ("sunset", "Sunset Beach", 1500, False,
     {"type": "gradient", "colors": ["#7A2E2E", "#2A0E0E"], "accent": "#FFA94D"}),
    ("emerald", "Emerald Court", 1800, False,
     {"type": "gradient", "colors": ["#0A3A2A", "#041A12"], "accent": "#34D399"}),
]


class Command(BaseCommand):
    help = "Seed default + premium room themes"

    def handle(self, *args, **opts):
        created = 0
        for i, (key, name, cost, default, assets) in enumerate(THEMES):
            _, made = RoomTheme.objects.update_or_create(
                key=key,
                defaults={"name": name, "coin_cost": cost, "is_default": default,
                          "assets": assets, "sort_order": i, "is_active": True},
            )
            created += 1 if made else 0
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(THEMES)} themes ({created} new)."))
