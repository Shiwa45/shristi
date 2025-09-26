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