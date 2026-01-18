# apps/core/models.py
from django.db import models
from django.urls import reverse

class HomepageSlider(models.Model):
    """Homepage slider/banner management"""
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True, help_text="Subtitle/tagline")
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='sliders/')

    # Call to actions
    primary_cta_text = models.CharField(max_length=50, blank=True, help_text="Primary button text")
    primary_cta_url = models.CharField(max_length=200, blank=True, help_text="Primary button link")
    secondary_cta_text = models.CharField(max_length=50, blank=True, help_text="Secondary button text")
    secondary_cta_url = models.CharField(max_length=200, blank=True, help_text="Secondary button link")

    # Background gradients
    background_gradient_from = models.CharField(max_length=50, default='from-blue-50', help_text="Tailwind gradient from class")
    background_gradient_via = models.CharField(max_length=50, default='via-indigo-50', help_text="Tailwind gradient via class")
    background_gradient_to = models.CharField(max_length=50, default='to-purple-50', help_text="Tailwind gradient to class")

    # Legacy fields (for backward compatibility)
    cta_text = models.CharField(max_length=50, blank=True, help_text="Legacy button text")
    cta_url = models.CharField(max_length=200, blank=True, help_text="Legacy button link")

    # Settings
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Display order")

    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Homepage Slider"
        verbose_name_plural = "Homepage Sliders"

    def __str__(self):
        return self.title


class Page(models.Model):
    """Static pages like About, Privacy Policy, etc."""
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    meta_description = models.CharField(max_length=160, blank=True)
    
    # Settings
    is_published = models.BooleanField(default=True)
    show_in_menu = models.BooleanField(default=False)
    menu_order = models.IntegerField(default=0)
    
    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['menu_order']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('core:page', kwargs={'slug': self.slug})


class ContactSubmission(models.Model):
    """Contact form submissions"""
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    
    # Status tracking
    is_read = models.BooleanField(default=False)
    is_replied = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True)
    
    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject}"


class Testimonial(models.Model):
    """Customer testimonials"""
    name = models.CharField(max_length=100)
    company = models.CharField(max_length=100, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(upload_to='testimonials/', blank=True)
    
    # Content
    testimonial = models.TextField()
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], default=5)
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    # Meta
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return f"{self.name} - {self.rating} stars"


class FAQCategory(models.Model):
    """FAQ categories"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = "FAQ Category"
        verbose_name_plural = "FAQ Categories"

    def __str__(self):
        return self.name


class FAQ(models.Model):
    """Frequently Asked Questions"""
    category = models.ForeignKey(FAQCategory, on_delete=models.CASCADE, related_name='faqs')
    question = models.CharField(max_length=300)
    answer = models.TextField()
    
    # Settings
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question


class NoDesignSection(models.Model):
    """Homepage 'No Design? No Problem' section"""
    title = models.CharField(max_length=200, default="No Design?")
    highlight_text = models.CharField(max_length=200, default="No Problem!")
    description = models.TextField()
    cta_text = models.CharField(max_length=100, default="Get Free Design")
    cta_url = models.CharField(max_length=200, blank=True, help_text="Leave blank to use the contact page")
    image = models.ImageField(upload_to='home_sections/', blank=True, null=True)
    image_static_path = models.CharField(max_length=200, default="img/no_design.png")
    image_alt_text = models.CharField(max_length=200, default="Professional Design Team")
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Display order")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = "No Design Section"
        verbose_name_plural = "No Design Sections"

    def __str__(self):
        return f"{self.title} {self.highlight_text}".strip()


class NoDesignFeature(models.Model):
    """Feature list for the No Design section"""
    section = models.ForeignKey(NoDesignSection, on_delete=models.CASCADE, related_name='features')
    text = models.CharField(max_length=200)
    icon_class = models.CharField(max_length=100, default="fas fa-check")
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = "No Design Feature"
        verbose_name_plural = "No Design Features"

    def __str__(self):
        return self.text


class SiteSetting(models.Model):
    """Global site settings for header and footer"""
    site_name = models.CharField(max_length=200, default="Shirsti Printing Company")
    logo = models.ImageField(upload_to='site/', blank=True, null=True)
    logo_static_path = models.CharField(max_length=200, default="images/logo.png")
    logo_alt_text = models.CharField(max_length=200, default="Shirsti Printing")

    contact_phone = models.CharField(max_length=50, default="+91 123 456 7890")
    contact_email = models.EmailField(default="info@shirstiprinting.com")
    contact_address = models.TextField(default="123 Print Street\nNew Delhi, India")

    footer_about_title = models.CharField(max_length=200, default="Shirsti Printing Company")
    footer_about_text = models.TextField(
        default=(
            "Your trusted partner for professional printing services. From business cards to large format "
            "printing, we deliver quality results that make an impression."
        )
    )

    contact_heading = models.CharField(max_length=100, default="Contact Info")
    business_hours_heading = models.CharField(max_length=100, default="Business Hours:")
    business_hours = models.TextField(
        default="Monday - Friday: 9:00 AM - 6:00 PM\nSaturday: 9:00 AM - 2:00 PM\nSunday: Closed"
    )
    copyright_text = models.CharField(
        max_length=200,
        default="&copy; 2024 Shrishti Printing Company. All rights reserved.",
    )
    services_video_url = models.URLField(blank=True, help_text="Single video URL used on service pages")
    services_video_poster = models.ImageField(upload_to='site/', blank=True, null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Setting"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return self.site_name


class SiteNavLink(models.Model):
    """Navigation links managed in site settings"""
    POSITION_CHOICES = [
        ('before_services', 'Before Services'),
        ('after_services', 'After Services'),
    ]

    site_settings = models.ForeignKey(SiteSetting, on_delete=models.CASCADE, related_name='nav_links')
    label = models.CharField(max_length=100)
    url = models.CharField(max_length=200)
    position = models.CharField(max_length=20, choices=POSITION_CHOICES, default='before_services')
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['position', 'order']
        verbose_name = "Site Nav Link"
        verbose_name_plural = "Site Nav Links"

    def __str__(self):
        return self.label


class FooterLinkGroup(models.Model):
    """Footer link group such as Quick Links or Legal"""
    site_settings = models.ForeignKey(SiteSetting, on_delete=models.CASCADE, related_name='footer_link_groups')
    title = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = "Footer Link Group"
        verbose_name_plural = "Footer Link Groups"

    def __str__(self):
        return self.title


class FooterLink(models.Model):
    """Footer links within a group"""
    group = models.ForeignKey(FooterLinkGroup, on_delete=models.CASCADE, related_name='links')
    label = models.CharField(max_length=100)
    url = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = "Footer Link"
        verbose_name_plural = "Footer Links"

    def __str__(self):
        return self.label


class SocialLink(models.Model):
    """Social links shown in the footer"""
    site_settings = models.ForeignKey(SiteSetting, on_delete=models.CASCADE, related_name='social_links')
    label = models.CharField(max_length=100)
    url = models.CharField(max_length=200, default="#")
    icon_svg = models.TextField()
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = "Social Link"
        verbose_name_plural = "Social Links"

    def __str__(self):
        return self.label
