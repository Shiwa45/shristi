
from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    ServiceCategory, StaticProduct, StaticProductImage,
    StaticProductFAQ, StaticProductSample, StaticProductTestimonial
)

# apps/services/admin.py - Updated for Static Products

class StaticProductForm(forms.ModelForm):
    class Meta:
        model = StaticProduct
        fields = [
            'name', 'slug', 'category', 'description', 'short_description',
            'design_tool_enabled', 'canvas_width', 'canvas_height',
            'featured_image', 'hero_image', 'meta_title', 'meta_description',
            'base_price', 'price_unit', 'available_sizes', 'available_papers',
            'available_finishes', 'available_bindings', 'color_options',
            'quantity_tiers', 'rush_order_available', 'rush_order_percentage',
            'design_service_available', 'design_service_price',
            'key_features', 'specifications', 'is_active', 'is_featured', 'order'
        ]


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'is_featured', 'order', 'product_count')
    list_filter = ('is_active', 'is_featured')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active', 'is_featured', 'order')

    def product_count(self, obj):
        count = obj.static_products.filter(is_active=True).count()
        if count > 0:
            url = reverse('admin:services_staticproduct_changelist')
            return format_html('<a href="{}?category__id__exact={}">{} products</a>', url, obj.id, count)
        return '0 products'
    product_count.short_description = 'Active Products'


class ProductImageInline(admin.TabularInline):
    model = StaticProductImage
    extra = 1
    fields = ('image', 'alt_text', 'caption', 'order', 'is_featured')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px;" />', obj.image.url)
        return "No image"
    image_preview.short_description = 'Preview'


class ProductFAQInline(admin.TabularInline):
    model = StaticProductFAQ
    extra = 1
    fields = ('question', 'answer', 'order', 'is_active')


class ProductSampleInline(admin.TabularInline):
    model = StaticProductSample
    extra = 1
    fields = ('title', 'description', 'image', 'file', 'order', 'is_active')


class ProductTestimonialInline(admin.TabularInline):
    model = StaticProductTestimonial
    extra = 1
    fields = ('customer_name', 'customer_company', 'content', 'rating', 'order', 'is_active')

@admin.register(StaticProduct)
class StaticProductAdmin(admin.ModelAdmin):
    form = StaticProductForm
    list_display = (
        'name', 'category', 'base_price', 'price_unit', 
        'design_tool_enabled', 'is_active', 'is_featured', 'order'
    )
    list_filter = (
        'category', 'design_tool_enabled', 'is_active', 
        'is_featured', 'rush_order_available', 'design_service_available'
    )
    search_fields = ('name', 'description', 'short_description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active', 'is_featured', 'order')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category', 'description', 'short_description')
        }),
        ('Images', {
            'fields': ('featured_image', 'hero_image')
        }),
        ('Design Tool Configuration', {
            'fields': ('design_tool_enabled', 'canvas_width', 'canvas_height'),
            'classes': ('collapse',)
        }),
        ('SEO Settings', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Pricing Configuration', {
            'fields': (
                'base_price', 'price_unit', 'available_sizes', 'available_papers',
                'available_finishes', 'available_bindings', 'color_options', 'quantity_tiers'
            ),
            'description': 'Configure static pricing options. Use JSON format for lists.'
        }),
        ('Additional Services', {
            'fields': (
                'rush_order_available', 'rush_order_percentage',
                'design_service_available', 'design_service_price'
            )
        }),
        ('Product Details', {
            'fields': ('key_features', 'specifications'),
            'classes': ('collapse',)
        }),
        ('Status and Ordering', {
            'fields': ('is_active', 'is_featured', 'order')
        }),
    )
    
    inlines = [ProductImageInline, ProductFAQInline, ProductSampleInline, ProductTestimonialInline]
    
    # Temporarily remove readonly fields to debug
    # def get_readonly_fields(self, request, obj=None):
    #     if obj:  # editing an existing object
    #         return ('slug',)
    #     return ()
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
        js = ('admin/js/json_editor.js',)


@admin.register(StaticProductImage)
class StaticProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'alt_text', 'order', 'is_featured', 'image_preview')
    list_filter = ('product__category', 'is_featured')
    search_fields = ('product__name', 'alt_text', 'caption')
    list_editable = ('order', 'is_featured')
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 60px;" />', obj.image.url)
        return "No image"
    image_preview.short_description = 'Preview'


@admin.register(StaticProductFAQ)
class StaticProductFAQAdmin(admin.ModelAdmin):
    list_display = ('product', 'question_short', 'order', 'is_active')
    list_filter = ('product__category', 'is_active')
    search_fields = ('product__name', 'question', 'answer')
    list_editable = ('order', 'is_active')
    
    def question_short(self, obj):
        return obj.question[:50] + '...' if len(obj.question) > 50 else obj.question
    question_short.short_description = 'Question'


@admin.register(StaticProductSample)
class StaticProductSampleAdmin(admin.ModelAdmin):
    list_display = ('product', 'title', 'order', 'is_active', 'image_preview')
    list_filter = ('product__category', 'is_active')
    search_fields = ('product__name', 'title', 'description')
    list_editable = ('order', 'is_active')
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px;" />', obj.image.url)
        return "No image"
    image_preview.short_description = 'Preview'


@admin.register(StaticProductTestimonial)
class StaticProductTestimonialAdmin(admin.ModelAdmin):
    list_display = ('product', 'customer_name', 'customer_company', 'rating', 'order', 'is_active')
    list_filter = ('product__category', 'rating', 'is_active')
    search_fields = ('product__name', 'customer_name', 'customer_company', 'content')
    list_editable = ('order', 'is_active')
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing
            return ('created_at',)
        return ()


# Custom admin site configuration
admin.site.site_header = "Shirsti Printing Admin"
admin.site.site_title = "Shirsti Printing"
admin.site.index_title = "Welcome to Shirsti Printing Administration"