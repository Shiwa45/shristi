# apps/services/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import ServiceCategory, Product, ProductImage, ProductSpecification

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'product_count', 'is_active', 'order')
    list_filter = ('is_active',)
    list_editable = ('is_active', 'order')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'order')


class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecification
    extra = 1
    fields = ('name', 'value', 'order')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'image_preview', 'price_per_unit', 'has_design_tool', 'is_active', 'is_featured')
    list_filter = ('category', 'has_design_tool', 'allows_upload', 'is_active', 'is_featured', 'created_at')
    list_editable = ('is_active', 'is_featured')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('canvas_width_px', 'canvas_height_px', 'created_at', 'updated_at')
    inlines = [ProductImageInline, ProductSpecificationInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category', 'description', 'image')
        }),
        ('Design Specifications', {
            'fields': (
                ('width_mm', 'height_mm'),
                ('bleed_mm', 'safe_zone_mm'),
                'dpi',
                ('canvas_width_px', 'canvas_height_px'),
            )
        }),
        ('Features', {
            'fields': ('has_design_tool', 'allows_upload')
        }),
        ('Pricing', {
            'fields': (
                ('base_price', 'price_per_unit'),
                'minimum_quantity',
            )
        }),
        ('Settings', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = "Preview"

    def canvas_width_px(self, obj):
        return f"{obj.canvas_width_px} px"
    canvas_width_px.short_description = "Canvas Width (px)"

    def canvas_height_px(self, obj):
        return f"{obj.canvas_height_px} px"
    canvas_height_px.short_description = "Canvas Height (px)"


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image_preview', 'alt_text', 'order')
    list_filter = ('product__category',)
    search_fields = ('product__name', 'alt_text')
    list_editable = ('order',)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = "Preview"


@admin.register(ProductSpecification)
class ProductSpecificationAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'value', 'order')
    list_filter = ('product__category',)
    search_fields = ('product__name', 'name', 'value')
    list_editable = ('order',)


# Customize admin site header
admin.site.site_header = "Shirsti Printing Company Admin"
admin.site.site_title = "Shirsti Admin"
admin.site.index_title = "Welcome to Shirsti Printing Administration"