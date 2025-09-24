# apps/services/models.py
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

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

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('services:category', kwargs={'slug': self.slug})


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

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('services:product_detail', kwargs={'slug': self.slug})

    @property
    def canvas_width_px(self):
        """Convert width from mm to pixels for canvas"""
        return int((self.width_mm / 25.4) * self.dpi)

    @property
    def canvas_height_px(self):
        """Convert height from mm to pixels for canvas"""
        return int((self.height_mm / 25.4) * self.dpi)

    @property
    def bleed_px(self):
        """Convert bleed from mm to pixels"""
        return int((self.bleed_mm / 25.4) * self.dpi)

    @property
    def safe_zone_px(self):
        """Convert safe zone from mm to pixels"""
        return int((self.safe_zone_mm / 25.4) * self.dpi)

    def get_canvas_config(self):
        """Get canvas configuration for design tool"""
        return {
            'width': self.canvas_width_px,
            'height': self.canvas_height_px,
            'bleed': self.bleed_px,
            'safe_zone': self.safe_zone_px,
            'dpi': self.dpi,
            'width_mm': self.width_mm,
            'height_mm': self.height_mm,
        }

    def calculate_price(self, quantity):
        """Calculate price based on quantity with volume discounts"""
        if self.price_per_unit <= 0:
            return None  # Quote-based pricing
        
        unit_price = float(self.price_per_unit)
        
        # Volume discounts
        if quantity >= 1000:
            unit_price *= 0.85  # 15% discount
        elif quantity >= 500:
            unit_price *= 0.90  # 10% discount
        elif quantity >= 100:
            unit_price *= 0.95  # 5% discount
        
        total_price = float(self.base_price) + (unit_price * quantity)
        
        return {
            'unit_price': round(unit_price, 2),
            'total_price': round(total_price, 2),
            'base_price': float(self.base_price),
            'savings': round(float(self.price_per_unit) * quantity - unit_price * quantity, 2) if quantity >= 100 else 0
        }


class ProductImage(models.Model):
    """Additional product images for gallery"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} - Image {self.order}"


class ProductSpecification(models.Model):
    """Additional product specifications"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='specifications')
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=200)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} - {self.name}"