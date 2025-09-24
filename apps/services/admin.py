# apps/services/admin.py - Enhanced admin interface

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Min, Max
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    ServiceCategory, Product, ProductPricing, 
    ProductImage, ProductSpecification, PricingTier
)

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'product_count', 'is_active', 'is_featured', 'order']
    list_filter = ['is_active', 'is_featured', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active', 'is_featured', 'order']
    
    def product_count(self, obj):
        count = obj.products.filter(is_active=True).count()
        if count > 0:
            url = reverse('admin:services_product_changelist') + f'?category__id__exact={obj.id}'
            return format_html('<a href="{}">{} products</a>', url, count)
        return '0 products'
    product_count.short_description = 'Active Products'

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'caption', 'order', 'is_featured']
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 100px;" />', obj.image.url)
        return 'No image'
    image_preview.short_description = 'Preview'

class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecification
    extra = 1
    fields = ['name', 'value', 'icon', 'order', 'is_highlighted']

class ProductPricingInline(admin.TabularInline):
    model = ProductPricing
    extra = 1
    fields = [
        'size', 'paper_type', 'finish', 'colors', 
        'min_quantity', 'price_per_unit', 'setup_cost',
        'volume_discount_percentage', 'turnaround_days', 'is_active'
    ]
    readonly_fields = ['created_at']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'price_range_display', 'has_design_tool', 
        'is_active', 'is_featured', 'pricing_tiers_count', 'created_at'
    ]
    list_filter = [
        'category', 'has_design_tool', 'allows_upload', 
        'is_active', 'is_featured', 'created_at'
    ]
    search_fields = ['name', 'description', 'keywords']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active', 'is_featured']
    readonly_fields = ['created_at', 'updated_at', 'price_summary']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category', 'description', 'short_description', 'image')
        }),
        ('Design Specifications', {
            'fields': ('width_mm', 'height_mm', 'bleed_mm', 'safe_zone_mm', 'dpi'),
            'classes': ('collapse',)
        }),
        ('Features', {
            'fields': ('has_design_tool', 'allows_upload', 'allows_custom_size')
        }),
        ('Default Pricing', {
            'fields': ('base_price', 'price_per_unit', 'minimum_quantity'),
            'description': 'These are fallback values used when no specific pricing exists.'
        }),
        ('SEO & Meta', {
            'fields': ('meta_title', 'meta_description', 'keywords'),
            'classes': ('collapse',)
        }),
        ('Status & Organization', {
            'fields': ('is_active', 'is_featured', 'order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Pricing Summary', {
            'fields': ('price_summary',),
            'classes': ('collapse',)
        })
    )
    
    inlines = [ProductImageInline, ProductSpecificationInline, ProductPricingInline]
    
    def price_range_display(self, obj):
        price_range = obj.get_price_range()
        if price_range['min'] == price_range['max']:
            return f"₹{price_range['min']}"
        return f"₹{price_range['min']} - ₹{price_range['max']}"
    price_range_display.short_description = 'Price Range'
    
    def pricing_tiers_count(self, obj):
        count = obj.pricings.filter(is_active=True).count()
        if count > 0:
            return format_html(
                '<span style="color: green;">{} tiers</span>', count
            )
        return format_html('<span style="color: red;">No pricing</span>')
    pricing_tiers_count.short_description = 'Pricing Tiers'
    
    def price_summary(self, obj):
        pricings = obj.pricings.filter(is_active=True).order_by('min_quantity')
        if not pricings.exists():
            return "No pricing configured"
        
        html = "<table style='width: 100%; border-collapse: collapse;'>"
        html += "<tr style='background: #f0f0f0;'><th style='border: 1px solid #ddd; padding: 8px;'>Specs</th><th style='border: 1px solid #ddd; padding: 8px;'>Min Qty</th><th style='border: 1px solid #ddd; padding: 8px;'>Price/Unit</th><th style='border: 1px solid #ddd; padding: 8px;'>Setup</th></tr>"
        
        for pricing in pricings[:10]:  # Show first 10 pricing tiers
            specs = []
            if pricing.size: specs.append(pricing.size)
            if pricing.paper_type: specs.append(pricing.paper_type)
            if pricing.finish: specs.append(pricing.finish)
            if pricing.colors: specs.append(pricing.colors)
            
            spec_text = " | ".join(specs) if specs else "Standard"
            
            html += f"<tr><td style='border: 1px solid #ddd; padding: 8px;'>{spec_text}</td>"
            html += f"<td style='border: 1px solid #ddd; padding: 8px; text-align: center;'>{pricing.min_quantity}</td>"
            html += f"<td style='border: 1px solid #ddd; padding: 8px; text-align: right;'>₹{pricing.price_per_unit}</td>"
            html += f"<td style='border: 1px solid #ddd; padding: 8px; text-align: right;'>₹{pricing.setup_cost}</td></tr>"
        
        if pricings.count() > 10:
            html += f"<tr><td colspan='4' style='border: 1px solid #ddd; padding: 8px; text-align: center; font-style: italic;'>... and {pricings.count() - 10} more pricing tiers</td></tr>"
        
        html += "</table>"
        return mark_safe(html)
    price_summary.short_description = 'Pricing Overview'

@admin.register(ProductPricing)
class ProductPricingAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'specifications_display', 'min_quantity', 'max_quantity',
        'price_per_unit', 'setup_cost', 'volume_discount_percentage', 
        'turnaround_days', 'is_active', 'is_featured'
    ]
    list_filter = [
        'product__category', 'size', 'paper_type', 'finish', 'colors',
        'is_active', 'is_featured', 'turnaround_days'
    ]
    search_fields = [
        'product__name', 'size', 'paper_type', 'binding_type', 
        'finish', 'colors', 'notes'
    ]
    list_editable = ['is_active', 'is_featured', 'price_per_unit']
    readonly_fields = ['created_at', 'updated_at', 'pricing_calculator']
    
    fieldsets = (
        ('Product & Specifications', {
            'fields': ('product', 'size', 'paper_type', 'binding_type', 'finish', 'colors')
        }),
        ('Quantity & Pricing', {
            'fields': ('min_quantity', 'max_quantity', 'price_per_unit', 'setup_cost')
        }),
        ('Discounts & Modifiers', {
            'fields': ('volume_discount_percentage', 'rush_order_multiplier')
        }),
        ('Service Details', {
            'fields': ('turnaround_days', 'notes')
        }),
        ('Status & Features', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Pricing Calculator', {
            'fields': ('pricing_calculator',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def specifications_display(self, obj):
        specs = []
        if obj.size: specs.append(obj.size)
        if obj.paper_type: specs.append(obj.paper_type)
        if obj.finish: specs.append(obj.finish)
        if obj.colors: specs.append(obj.colors)
        return " | ".join(specs) if specs else "Standard"
    specifications_display.short_description = 'Specifications'
    
    def pricing_calculator(self, obj):
        if not obj.id:
            return "Save the pricing first to see calculator"
        
        quantities = [100, 250, 500, 1000, 2500, 5000]
        html = "<div style='background: #f9f9f9; padding: 15px; border-radius: 5px;'>"
        html += "<h4>Price Calculator Preview</h4>"
        html += "<table style='width: 100%; border-collapse: collapse;'>"
        html += "<tr style='background: #e9e9e9;'><th style='border: 1px solid #ddd; padding: 8px;'>Quantity</th><th style='border: 1px solid #ddd; padding: 8px;'>Unit Price</th><th style='border: 1px solid #ddd; padding: 8px;'>Total Price</th><th style='border: 1px solid #ddd; padding: 8px;'>Savings</th></tr>"
        
        for qty in quantities:
            if qty >= obj.min_quantity and (not obj.max_quantity or qty <= obj.max_quantity):
                calc = obj.calculate_total_price(qty)
                if calc:
                    savings_color = "green" if calc['savings'] > 0 else "black"
                    html += f"<tr>"
                    html += f"<td style='border: 1px solid #ddd; padding: 8px; text-align: center;'>{qty:,}</td>"
                    html += f"<td style='border: 1px solid #ddd; padding: 8px; text-align: right;'>₹{calc['unit_price']}</td>"
                    html += f"<td style='border: 1px solid #ddd; padding: 8px; text-align: right;'>₹{calc['total_price']:,}</td>"
                    html += f"<td style='border: 1px solid #ddd; padding: 8px; text-align: right; color: {savings_color};'>₹{calc['savings']:,}</td>"
                    html += f"</tr>"
        
        html += "</table></div>"
        return mark_safe(html)
    pricing_calculator.short_description = 'Price Calculator'

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'image_preview', 'alt_text', 'order', 'is_featured']
    list_filter = ['product__category', 'is_featured']
    search_fields = ['product__name', 'alt_text', 'caption']
    list_editable = ['order', 'is_featured']
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 150px; object-fit: cover;" />',
                obj.image.url
            )
        return 'No image'
    image_preview.short_description = 'Preview'

@admin.register(ProductSpecification)
class ProductSpecificationAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'value', 'icon', 'order', 'is_highlighted']
    list_filter = ['product__category', 'is_highlighted']
    search_fields = ['product__name', 'name', 'value']
    list_editable = ['order', 'is_highlighted']

@admin.register(PricingTier)
class PricingTierAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_preview', 'description', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    
    def color_preview(self, obj):
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc; border-radius: 3px;"></div>',
            obj.color
        )
    color_preview.short_description = 'Color'

# Custom admin actions
@admin.action(description='Duplicate selected pricing rules')
def duplicate_pricing_rules(modeladmin, request, queryset):
    for pricing in queryset:
        pricing.pk = None
        pricing.is_active = False  # Make duplicates inactive by default
        pricing.save()

ProductPricingAdmin.actions = [duplicate_pricing_rules]

# Admin site customization
admin.site.site_header = "Shirsti Printing Administration"
admin.site.site_title = "Shirsti Printing Admin"
admin.site.index_title = "Welcome to Shirsti Printing Administration"