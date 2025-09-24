# apps/core/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import HomepageSlider, Page, ContactSubmission, Testimonial, FAQCategory, FAQ

@admin.register(HomepageSlider)
class HomepageSliderAdmin(admin.ModelAdmin):
    list_display = ('title', 'image_preview', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'created_at')
    list_editable = ('is_active', 'order')
    search_fields = ('title', 'description')
    prepopulated_fields = {'cta_url': ('title',)}
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'description', 'image')
        }),
        ('Call to Action', {
            'fields': ('cta_text', 'cta_url')
        }),
        ('Settings', {
            'fields': ('is_active', 'order')
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 30px; object-fit: cover;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = "Preview"


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_published', 'show_in_menu', 'updated_at')
    list_filter = ('is_published', 'show_in_menu', 'created_at')
    list_editable = ('is_published', 'show_in_menu')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'content', 'meta_description')
        }),
        ('Menu Settings', {
            'fields': ('show_in_menu', 'menu_order')
        }),
        ('Publishing', {
            'fields': ('is_published',)
        }),
    )


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'is_read', 'is_replied', 'created_at')
    list_filter = ('is_read', 'is_replied', 'created_at')
    list_editable = ('is_read', 'is_replied')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('created_at', 'ip_address')
    
    fieldsets = (
        ('Contact Info', {
            'fields': ('name', 'email', 'phone', 'subject')
        }),
        ('Message', {
            'fields': ('message',)
        }),
        ('Status', {
            'fields': ('is_read', 'is_replied', 'admin_notes')
        }),
        ('Meta', {
            'fields': ('created_at', 'ip_address'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'rating', 'is_active', 'is_featured', 'order')
    list_filter = ('rating', 'is_active', 'is_featured', 'created_at')
    list_editable = ('is_active', 'is_featured', 'order')
    search_fields = ('name', 'company', 'testimonial')
    
    fieldsets = (
        ('Person Info', {
            'fields': ('name', 'company', 'designation', 'avatar')
        }),
        ('Testimonial', {
            'fields': ('testimonial', 'rating')
        }),
        ('Settings', {
            'fields': ('is_active', 'is_featured', 'order')
        }),
    )


@admin.register(FAQCategory)
class FAQCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon', 'is_active', 'order')
    list_filter = ('is_active',)
    list_editable = ('is_active', 'order')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


class FAQInline(admin.TabularInline):
    model = FAQ
    extra = 1
    fields = ('question', 'answer', 'is_active', 'order')


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'is_active', 'order')
    list_filter = ('category', 'is_active', 'created_at')
    list_editable = ('is_active', 'order')
    search_fields = ('question', 'answer')
    
    fieldsets = (
        ('Content', {
            'fields': ('category', 'question', 'answer')
        }),
        ('Settings', {
            'fields': ('is_active', 'order')
        }),
    )


# Add inline to FAQCategoryAdmin
FAQCategoryAdmin.inlines = [FAQInline]