from django.contrib import admin

from .models import (
    DailyLoginReward, LoginStreak, RedeemCode, RedeemRedemption,
    Referral, Task, TaskProgress, UserVip, VipTier,
)
from .vip_loot import LootReward, LootTable


# ---- VIP (membership tokens / tiers) ----
@admin.register(VipTier)
class VipTierAdmin(admin.ModelAdmin):
    list_display = ("level", "name", "wealth_threshold", "monthly_coin_price")
    ordering = ("level",)
    search_fields = ("name",)


@admin.register(UserVip)
class UserVipAdmin(admin.ModelAdmin):
    list_display = ("user", "tier", "expires_at", "updated_at")
    list_filter = ("tier",)
    search_fields = ("user__username",)


# ---- Redeem codes (promo tokens) ----
@admin.register(RedeemCode)
class RedeemCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "coin_reward", "max_uses", "use_count",
                    "is_active", "expires_at")
    list_filter = ("is_active",)
    search_fields = ("code",)
    list_editable = ("is_active",)


# ---- Tasks & offers ----
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "cadence", "trigger_event",
                    "target_count", "coin_reward")
    list_filter = ("cadence",)
    search_fields = ("code", "title")
    list_editable = ("coin_reward",)


@admin.register(DailyLoginReward)
class DailyLoginRewardAdmin(admin.ModelAdmin):
    list_display = ("day_index", "coin_reward")
    ordering = ("day_index",)
    list_editable = ("coin_reward",)


# ---- Loot boxes (gacha offers) ----
class LootRewardInline(admin.TabularInline):
    model = LootReward
    extra = 1


@admin.register(LootTable)
class LootTableAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "ticket_cost", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
    list_editable = ("ticket_cost", "is_active")
    inlines = [LootRewardInline]


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ("inviter", "invitee", "code", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("code", "inviter__username", "invitee__username")


# read-mostly tracking models
for _m in (LoginStreak, TaskProgress, RedeemRedemption):
    admin.site.register(_m)
