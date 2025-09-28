# apps/templates_mgmt/admin.py
from django.contrib import admin
from .models import TemplateCategory, DesignTemplate, UserDesign, StaticProductTemplate

@admin.register(TemplateCategory)
class TemplateCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active',)

@admin.register(DesignTemplate)
class DesignTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active', 'is_premium', 'download_count', 'created_at')
    list_filter = ('category', 'is_active', 'is_premium', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('is_active', 'is_premium')
    readonly_fields = ('download_count', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description', 'category')
        }),
        ('Files', {
            'fields': ('thumbnail', 'preview_image', 'svg_file', 'json_data')
        }),
        ('Specifications', {
            'fields': ('width_mm', 'height_mm', 'bleed_mm', 'safe_zone_mm')
        }),
        ('Settings', {
            'fields': ('is_active', 'is_premium')
        }),
        ('Stats', {
            'fields': ('download_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(UserDesign)
class UserDesignAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'static_product', 'is_public', 'created_at')
    list_filter = ('static_product', 'is_public', 'created_at')
    search_fields = ('name', 'user__email', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'name', 'static_product')
        }),
        ('Design Data', {
            'fields': ('canvas_data', 'preview_image')
        }),
        ('Specifications', {
            'fields': ('width_mm', 'height_mm', 'bleed_mm', 'safe_zone_mm')
        }),
        ('Settings', {
            'fields': ('is_public',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StaticProductTemplate)
class StaticProductTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'static_product', 'category', 'is_active', 'is_premium', 'is_featured', 'usage_count', 'order')
    list_filter = ('static_product', 'category', 'is_active', 'is_premium', 'is_featured', 'created_at')
    search_fields = ('name', 'description', 'tags')
    list_editable = ('is_active', 'is_premium', 'is_featured', 'order')
    readonly_fields = ('usage_count', 'created_at', 'updated_at')

    fieldsets = (
        ('Basic Info', {
            'fields': ('static_product', 'name', 'description', 'category', 'tags')
        }),
        ('Template Files', {
            'fields': ('template_data', 'thumbnail', 'preview_image')
        }),
        ('Settings', {
            'fields': ('is_active', 'is_premium', 'is_featured', 'order')
        }),
        ('Stats', {
            'fields': ('usage_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


