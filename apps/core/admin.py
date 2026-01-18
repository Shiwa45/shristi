# apps/core/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    HomepageSlider,
    Page,
    ContactSubmission,
    Testimonial,
    FAQCategory,
    FAQ,
    NoDesignSection,
    NoDesignFeature,
    SiteSetting,
    SiteNavLink,
    FooterLinkGroup,
    FooterLink,
    SocialLink,
)

@admin.register(HomepageSlider)
class HomepageSliderAdmin(admin.ModelAdmin):
    list_display = ('title', 'subtitle', 'image_preview', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'created_at')
    list_editable = ('is_active', 'order')
    search_fields = ('title', 'subtitle', 'description')
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'subtitle', 'description', 'image')
        }),
        ('Call to Actions', {
            'fields': ('primary_cta_text', 'primary_cta_url', 'secondary_cta_text', 'secondary_cta_url')
        }),
        ('Background Styling', {
            'fields': ('background_gradient_from', 'background_gradient_via', 'background_gradient_to'),
            'classes': ('collapse',)
        }),
        ('Legacy Fields', {
            'fields': ('cta_text', 'cta_url'),
            'classes': ('collapse',)
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


class NoDesignFeatureInline(admin.TabularInline):
    model = NoDesignFeature
    extra = 1
    fields = ('text', 'icon_class', 'is_active', 'order')


@admin.register(NoDesignSection)
class NoDesignSectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'highlight_text', 'is_active', 'order', 'updated_at')
    list_filter = ('is_active', 'updated_at')
    list_editable = ('is_active', 'order')
    search_fields = ('title', 'highlight_text', 'description')

    fieldsets = (
        ('Content', {
            'fields': ('title', 'highlight_text', 'description')
        }),
        ('Call to Action', {
            'fields': ('cta_text', 'cta_url')
        }),
        ('Image', {
            'fields': ('image', 'image_static_path', 'image_alt_text')
        }),
        ('Settings', {
            'fields': ('is_active', 'order')
        }),
    )

    inlines = [NoDesignFeatureInline]


class SiteNavLinkInline(admin.TabularInline):
    model = SiteNavLink
    extra = 1
    fields = ('label', 'url', 'position', 'is_active', 'order')


class SocialLinkInline(admin.TabularInline):
    model = SocialLink
    extra = 1
    fields = ('label', 'url', 'icon_svg', 'is_active', 'order')


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'contact_email', 'contact_phone', 'is_active', 'updated_at')
    list_filter = ('is_active', 'updated_at')
    list_editable = ('is_active',)
    search_fields = ('site_name', 'contact_email', 'contact_phone')

    fieldsets = (
        ('Branding', {
            'fields': ('site_name', 'logo', 'logo_static_path', 'logo_alt_text')
        }),
        ('Footer About', {
            'fields': ('footer_about_title', 'footer_about_text')
        }),
        ('Services Video', {
            'fields': ('services_video_url', 'services_video_poster')
        }),
        ('Contact Info', {
            'fields': ('contact_heading', 'contact_phone', 'contact_email', 'contact_address')
        }),
        ('Business Hours', {
            'fields': ('business_hours_heading', 'business_hours')
        }),
        ('Copyright', {
            'fields': ('copyright_text',)
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
    )

    inlines = [SiteNavLinkInline, SocialLinkInline]


class FooterLinkInline(admin.TabularInline):
    model = FooterLink
    extra = 1
    fields = ('label', 'url', 'is_active', 'order')


@admin.register(FooterLinkGroup)
class FooterLinkGroupAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'order')
    list_filter = ('is_active',)
    list_editable = ('is_active', 'order')
    search_fields = ('title',)

    fieldsets = (
        ('Content', {
            'fields': ('site_settings', 'title')
        }),
        ('Settings', {
            'fields': ('is_active', 'order')
        }),
    )

    inlines = [FooterLinkInline]


@admin.register(FooterLink)
class FooterLinkAdmin(admin.ModelAdmin):
    list_display = ('label', 'group', 'is_active', 'order')
    list_filter = ('is_active',)
    list_editable = ('is_active', 'order')
    search_fields = ('label',)
