from django.contrib import admin

from .gifts import Gift, GiftEvent, GiftRecipient
from .models import LedgerEntry, Transaction, Wallet


@admin.register(Gift)
class GiftAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "tier", "coin_cost", "diamond_value",
                    "animation_type", "is_active", "sort_order")
    list_filter = ("tier", "is_active", "animation_type")
    search_fields = ("code", "name")
    list_editable = ("coin_cost", "diamond_value", "is_active", "sort_order")
    ordering = ("tier", "coin_cost")
    fieldsets = (
        (None, {"fields": ("code", "name", "tier", "is_active", "sort_order")}),
        ("Pricing", {"fields": ("coin_cost", "diamond_value")}),
        ("Assets", {"fields": ("icon_url", "animation_url", "animation_type")}),
    )


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("user", "coin_balance", "diamond_balance",
                    "lifetime_coins_spent", "lifetime_diamonds_earned", "updated_at")
    search_fields = ("user__username",)
    readonly_fields = ("lifetime_coins_spent", "lifetime_diamonds_earned", "updated_at")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "status", "initiator", "created_at", "idempotency_key")
    list_filter = ("type", "status", "created_at")
    search_fields = ("idempotency_key", "initiator__username")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False  # created by services, never by hand

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("id", "transaction", "wallet", "currency", "amount",
                    "balance_after", "is_system")
    list_filter = ("currency", "is_system")
    search_fields = ("wallet__user__username",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(GiftEvent)
class GiftEventAdmin(admin.ModelAdmin):
    list_display = ("id", "gift", "sender", "combo", "recipient_count",
                    "total_coin_cost", "created_at")
    list_filter = ("created_at",)
    search_fields = ("sender__username", "gift__code")
    date_hierarchy = "created_at"


admin.site.register(GiftRecipient)
