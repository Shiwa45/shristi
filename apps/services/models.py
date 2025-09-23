# apps/services/models.py
from django.db import models

class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name_plural = "Service Categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='products')
    description = models.TextField()
    
    # Design specifications
    width_mm = models.FloatField(help_text="Width in millimeters")
    height_mm = models.FloatField(help_text="Height in millimeters")
    bleed_mm = models.FloatField(default=3.0, help_text="Bleed size in millimeters")
    safe_zone_mm = models.FloatField(default=5.0, help_text="Safe zone in millimeters")
    dpi = models.IntegerField(default=300, help_text="Print resolution")
    
    # Features
    has_design_tool = models.BooleanField(default=False, help_text="Enable design tool for this product")
    allows_upload = models.BooleanField(default=True, help_text="Allow file uploads")
    
    # Pricing
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    minimum_quantity = models.IntegerField(default=1)
    
    # Meta
    image = models.ImageField(upload_to='products/', blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


