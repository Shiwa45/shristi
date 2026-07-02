from django.contrib import admin
from django.utils.html import format_html
from .models import QuoteRequest, QuoteRequestItem, Order, OrderItem, Cart, CartItem, Coupon


class QuoteRequestItemInline(admin.TabularInline):
    model = QuoteRequestItem
    extra = 0
    readonly_fields = ('static_product', 'description', 'quantity', 'specifications_display')
    fields = ('static_product', 'description', 'quantity', 'specifications_display')
    can_delete = False

    def specifications_display(self, obj):
        if not obj.specifications:
            return '—'
        lines = ''.join(
            f'<tr><td style="padding:2px 8px;font-weight:600;color:#555;">{k.replace("_"," ").title()}</td>'
            f'<td style="padding:2px 8px;">{v}</td></tr>'
            for k, v in obj.specifications.items()
        )
        return format_html('<table style="font-size:12px;border-collapse:collapse;">{}</table>', format_html(lines))
    specifications_display.short_description = 'Specifications'


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = (
        'quote_number', 'customer_name', 'customer_email', 'customer_phone',
        'product_name_display', 'quantity', 'status_badge', 'quoted_amount_display', 'created_at',
    )
    list_filter = ('status', 'created_at')
    search_fields = ('quote_number', 'customer_name', 'customer_email', 'customer_phone', 'description')
    ordering = ('-created_at',)
    readonly_fields = (
        'quote_number', 'user', 'customer_name', 'customer_email', 'customer_phone',
        'company_name', 'description', 'quantity', 'created_at', 'updated_at',
    )
    fieldsets = (
        ('Quote Info', {
            'fields': ('quote_number', 'status', 'created_at', 'updated_at'),
        }),
        ('Customer', {
            'fields': ('user', 'customer_name', 'customer_email', 'customer_phone', 'company_name'),
        }),
        ('Request Details', {
            'fields': ('description', 'quantity', 'budget_range'),
        }),
        ('Admin Response', {
            'fields': ('quoted_amount', 'quote_notes', 'quote_valid_until'),
            'description': 'Fill these in to send a quotation back to the customer.',
        }),
    )
    inlines = [QuoteRequestItemInline]
    date_hierarchy = 'created_at'
    list_per_page = 30

    def status_badge(self, obj):
        colours = {
            'pending':   ('#92400e', '#fef3c7'),
            'in_review': ('#1e40af', '#dbeafe'),
            'quoted':    ('#065f46', '#d1fae5'),
            'accepted':  ('#065f46', '#d1fae5'),
            'rejected':  ('#991b1b', '#fee2e2'),
            'expired':   ('#374151', '#f3f4f6'),
        }
        fg, bg = colours.get(obj.status, ('#374151', '#f3f4f6'))
        return format_html(
            '<span style="background:{};color:{};padding:3px 10px;border-radius:12px;'
            'font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;">{}</span>',
            bg, fg, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'

    def product_name_display(self, obj):
        item = obj.items.select_related('static_product').first()
        if item:
            return item.description
        return '—'
    product_name_display.short_description = 'Product'

    def quoted_amount_display(self, obj):
        if obj.quoted_amount:
            return format_html('<strong>₹{}</strong>', obj.quoted_amount)
        return format_html('<span style="color:#9ca3af;">Pending</span>')
    quoted_amount_display.short_description = 'Quoted Amount'
    quoted_amount_display.admin_order_field = 'quoted_amount'

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('items__static_product')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer_name', 'customer_email', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('order_number', 'customer_name', 'customer_email')
    ordering = ('-created_at',)
    readonly_fields = ('order_number', 'created_at', 'updated_at')
    list_per_page = 30


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'is_active', 'valid_from', 'valid_until', 'used_count')
    list_filter = ('is_active', 'discount_type')
    search_fields = ('code', 'description')
    ordering = ('-created_at',)
