from django.contrib import admin

from .models import Room, RoomBan, SeatState
from .room_types import RoomTheme, RoomThemeOwnership


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("room_id", "title", "owner", "room_type", "category",
                    "status", "theme", "seat_count")
    list_filter = ("room_type", "category", "status")
    search_fields = ("room_id", "title", "owner__username")
    raw_id_fields = ("owner",)


@admin.register(RoomTheme)
class RoomThemeAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "coin_cost", "is_default", "is_active", "sort_order")
    list_filter = ("is_default", "is_active")
    search_fields = ("key", "name")
    list_editable = ("coin_cost", "is_default", "is_active", "sort_order")


@admin.register(RoomBan)
class RoomBanAdmin(admin.ModelAdmin):
    list_display = ("room", "user", "created_by", "created_at")
    search_fields = ("room__room_id", "user__username")
    raw_id_fields = ("room", "user", "created_by")


admin.site.register(RoomThemeOwnership)
admin.site.register(SeatState)
