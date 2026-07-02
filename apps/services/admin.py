
from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json
from .models import (
    ServiceCategory,
    StaticProduct,
    StaticProductImage,
    StaticProductFAQ,
    StaticProductSample,
    StaticProductTestimonial,
    ProductFormField,
    ProductFieldOption,
    BookPrintingPricing,
    ServiceInfoBlock,
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


class ProductFormFieldForm(forms.ModelForm):
    options = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 5, 'class': 'vLargeTextField'}),
        help_text='LEGACY / ADVANCED — you normally do not need this. Manage options and '
                  'their prices using the "Options & pricing" grid below. This raw JSON is '
                  'only used as a fallback when no option rows exist.'
    )
    show_condition = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'vLargeTextField'}),
        help_text='JSON format: {"field": "color_mode", "value": "full_color", "operator": "equals"}'
    )
    triggers_fields = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'vLargeTextField'}),
        help_text='JSON format: ["bw_page_count", "color_page_count"]'
    )

    class Meta:
        model = ProductFormField
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Format JSON fields for display (pretty print)
        if self.instance and self.instance.pk:
            for field_name in ['options', 'show_condition', 'triggers_fields']:
                raw_value = getattr(self.instance, field_name, '')
                if raw_value:
                    try:
                        parsed = json.loads(raw_value)
                        self.fields[field_name].initial = json.dumps(parsed, indent=2)
                    except (TypeError, ValueError, json.JSONDecodeError):
                        self.fields[field_name].initial = raw_value

    def clean_options(self):
        value = self.cleaned_data.get('options', '').strip()
        if not value:
            return ''
        try:
            # Validate JSON format
            json.loads(value)
            return value
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f"Invalid JSON format: {e}") from e

    def clean_show_condition(self):
        value = self.cleaned_data.get('show_condition', '').strip()
        if not value:
            return ''
        try:
            # Validate JSON format
            json.loads(value)
            return value
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f"Invalid JSON format: {e}") from e

    def clean_triggers_fields(self):
        value = self.cleaned_data.get('triggers_fields', '').strip()
        if not value:
            return ''
        try:
            # Validate JSON format
            json.loads(value)
            return value
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f"Invalid JSON format: {e}") from e


class ProductFormFieldInline(admin.StackedInline):
    model = ProductFormField
    form = ProductFormFieldForm
    extra = 0
class ProductFormFieldInline(admin.StackedInline):
    model = ProductFormField
    form = ProductFormFieldForm
    extra = 0
    # classes = ('collapse',) # Removed to show all fields by default
    fieldsets = (
        ('Field Basics', {
            'fields': ('field_section', 'field_name', 'field_label', 'field_type', 'order', 'section_order', 'is_required')
        }),
        ('Display & Help', {
            'fields': ('help_text', 'placeholder', 'css_classes', 'grid_columns')
        }),
        ('Options & Defaults', {
            'fields': ('options', 'default_value', 'min_value', 'max_value')
        }),
        ('Conditional Logic', {
            'fields': ('show_condition', 'triggers_fields')
        }),
        ('Pricing Impact', {
            'fields': ('is_price_affecting', 'price_modifier')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


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
    fields = ('title', 'description', 'thumbnail', 'sample_file', 'file_type', 'order', 'is_active')


class ProductTestimonialInline(admin.TabularInline):
    model = StaticProductTestimonial
    extra = 1
    fields = ('customer_name', 'customer_company', 'testimonial', 'rating', 'order', 'is_active')


class ServiceInfoBlockInline(admin.TabularInline):
    model = ServiceInfoBlock
    extra = 1
    fields = ('title', 'body', 'bullet_points', 'order', 'is_active')

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
    
    inlines = [
        ProductFormFieldInline,
        ProductImageInline,
        ProductFAQInline,
        ProductSampleInline,
        ProductTestimonialInline,
        ServiceInfoBlockInline,
    ]
    
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
        if obj.thumbnail:
            return format_html('<img src="{}" style="max-height: 50px;" />', obj.thumbnail.url)
        return "No image"
    image_preview.short_description = 'Preview'


@admin.register(StaticProductTestimonial)
class StaticProductTestimonialAdmin(admin.ModelAdmin):
    list_display = ('product', 'customer_name', 'customer_company', 'rating', 'order', 'is_active')
    list_filter = ('product__category', 'rating', 'is_active')
    search_fields = ('product__name', 'customer_name', 'customer_company', 'testimonial')
    list_editable = ('order', 'is_active')
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing
            return ('created_at',)
        return ()


class ProductFieldOptionInline(admin.TabularInline):
    """Clean per-option grid: one row per choice, with an editable Price column."""
    model = ProductFieldOption
    extra = 1
    fields = ('label', 'value', 'price_modifier', 'image_preview', 'image_url', 'order', 'is_active')
    readonly_fields = ('image_preview',)
    ordering = ('order', 'id')

    def image_preview(self, obj):
        if obj and obj.image_url:
            return format_html('<img src="{}" style="max-height:40px;border:1px solid #eee;border-radius:4px;" />', obj.image_url)
        return format_html('<span style="color:#aaa;">—</span>')
    image_preview.short_description = 'Preview'


@admin.register(ProductFormField)
class ProductFormFieldAdmin(admin.ModelAdmin):
    form = ProductFormFieldForm
    inlines = [ProductFieldOptionInline]
    list_display = (
        'field_label', 'static_product', 'field_section', 'field_type',
        'option_summary', 'is_required', 'is_active',
    )
    list_filter = ('field_section', 'field_type', 'is_required', 'is_active', 'static_product__category')
    search_fields = ('field_label', 'field_name', 'static_product__name')
    ordering = ('static_product', 'section_order', 'order')
    autocomplete_fields = ('static_product',)

    fieldsets = (
        ('Field', {
            'fields': (
                'static_product', 'field_label', 'field_name', 'field_type',
                'field_section', 'is_required', 'help_text',
            ),
            'description': 'Edit the options and their prices in the "Options & pricing" grid at the bottom of this page.',
        }),
        ('Layout & ordering', {
            'fields': ('order', 'section_order', 'grid_columns', 'placeholder', 'css_classes'),
            'classes': ('collapse',),
        }),
        ('Number / range limits', {
            'fields': ('default_value', 'min_value', 'max_value'),
            'classes': ('collapse',),
        }),
        ('Conditional logic', {
            'fields': ('show_condition', 'triggers_fields'),
            'classes': ('collapse',),
        }),
        ('Advanced (legacy raw JSON — normally ignore)', {
            'fields': ('options', 'is_price_affecting', 'price_modifier'),
            'classes': ('collapse',),
        }),
        ('Status', {
            'fields': ('is_active',),
        }),
    )

    def option_summary(self, obj):
        rows = obj.field_options.all()
        if not rows:
            return format_html('<span style="color:#aaa;">no options</span>')
        parts = []
        for o in rows:
            if o.price_modifier and o.price_modifier != 0:
                parts.append(format_html('{} <b style="color:#7000fe;">(+₹{})</b>', o.label, o.price_modifier))
            else:
                parts.append(format_html('{}', o.label))
        return format_html(' &nbsp;·&nbsp; '.join(['{}'] * len(parts)), *parts)
    option_summary.short_description = 'Options (price)'

    class Media:
        js = ('admin/js/json_editor.js',)


@admin.register(ProductFieldOption)
class ProductFieldOptionAdmin(admin.ModelAdmin):
    """Flat, spreadsheet-style view of every option with inline-editable prices."""
    list_display = ('label', 'field', 'product_name', 'price_modifier', 'order', 'is_active')
    list_editable = ('price_modifier', 'order', 'is_active')
    list_filter = ('field__static_product__category', 'field__static_product', 'field__field_section')
    search_fields = ('label', 'value', 'field__field_label', 'field__static_product__name')
    ordering = ('field__static_product', 'field', 'order')
    list_per_page = 50
    autocomplete_fields = ('field',)

    def product_name(self, obj):
        return obj.field.static_product.name if obj.field and obj.field.static_product else '—'
    product_name.short_description = 'Product'
    product_name.admin_order_field = 'field__static_product__name'


@admin.register(BookPrintingPricing)
class BookPrintingPricingAdmin(admin.ModelAdmin):
    """Backup editor. The friendly editor lives at /services/manage/pricing/book-printing/."""

    def changelist_view(self, request, extra_context=None):
        from django.shortcuts import redirect
        # Always jump straight to the single editable row.
        obj = BookPrintingPricing.load()
        return redirect(f'./{obj.pk}/change/')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# Custom admin site configuration
admin.site.site_header = "Shristi Printing Admin"
admin.site.site_title = "Shristi Printing"
admin.site.index_title = "Welcome to Shristi Printing Administration"
