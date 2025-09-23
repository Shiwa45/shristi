# apps/services/admin.py
from django.contrib import admin
from .models import ServiceCategory, Product

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'order')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active', 'order')
    ordering = ('order',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'has_design_tool', 'is_active', 'is_featured', 'base_price')
    list_filter = ('category', 'has_design_tool', 'is_active', 'is_featured', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active', 'is_featured', 'has_design_tool')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'slug', 'category', 'description', 'image')
        }),
        ('Design Specifications', {
            'fields': ('width_mm', 'height_mm', 'bleed_mm', 'safe_zone_mm', 'dpi')
        }),
        ('Features', {
            'fields': ('has_design_tool', 'allows_upload')
        }),
        ('Pricing', {
            'fields': ('base_price', 'price_per_unit', 'minimum_quantity')
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


