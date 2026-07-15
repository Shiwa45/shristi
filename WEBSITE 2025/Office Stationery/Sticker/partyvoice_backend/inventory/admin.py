from django.contrib import admin

from .models import CosmeticItem, InventoryItem


@admin.register(CosmeticItem)
class CosmeticItemAdmin(admin.ModelAdmin):
    list_display = [f.name for f in CosmeticItem._meta.fields][:6]
    search_fields = ("code", "name") if any(f.name == "code" for f in CosmeticItem._meta.fields) else ()


admin.site.register(InventoryItem)
