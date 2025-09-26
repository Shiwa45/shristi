# apps/services/models.py - Enhanced version with better pricing

from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from decimal import Decimal

class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    image = models.ImageField(upload_to='categories/', blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = "Service Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('services:category', kwargs={'slug': self.slug})
    
    def get_design_tool_count(self):
        """Get count of products with design tool enabled"""
        return self.products.filter(has_design_tool=True, is_active=True).count()

class Product(models.Model):
    # Hero section content (admin-editable)
    hero_title = models.CharField(max_length=200, blank=True, help_text="Hero section main title")
    hero_subtitle = models.CharField(max_length=300, blank=True, help_text="Hero section subtitle/description")
    hero_image = models.ImageField(upload_to='products/hero/', blank=True, null=True, help_text="Hero section main image")
    hero_quote = models.CharField(max_length=300, blank=True, help_text="Hero section quote or tagline")

    # Sample data for paper and color selection grids
    sample_paper_image = models.ImageField(upload_to='products/sample_paper/', blank=True, null=True, help_text="Sample image for paper selection grid")
    sample_color_image = models.ImageField(upload_to='products/sample_color/', blank=True, null=True, help_text="Sample image for color selection grid")
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='products')
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True, help_text="Brief product description")
    
    # Design specifications
    width_mm = models.FloatField(help_text="Width in millimeters", validators=[MinValueValidator(1)])
    height_mm = models.FloatField(help_text="Height in millimeters", validators=[MinValueValidator(1)])
    bleed_mm = models.FloatField(default=3.0, help_text="Bleed size in millimeters", validators=[MinValueValidator(0)])
    safe_zone_mm = models.FloatField(default=5.0, help_text="Safe zone in millimeters", validators=[MinValueValidator(0)])
    dpi = models.IntegerField(default=300, help_text="Print resolution", validators=[MinValueValidator(72)])
    
    # Features
    has_design_tool = models.BooleanField(default=False, help_text="Enable design tool for this product")
    allows_upload = models.BooleanField(default=True, help_text="Allow file uploads")
    allows_custom_size = models.BooleanField(default=False, help_text="Allow custom sizing")
    
    # Pricing fallbacks (used when no ProductPricing exists)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Base setup cost")
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Default price per unit")
    minimum_quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    
    # SEO and Meta
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    keywords = models.CharField(max_length=500, blank=True, help_text="Comma-separated keywords")
    
    # Media
    image = models.ImageField(upload_to='products/', blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # New fields for richer product details
    video_url = models.URLField(blank=True, null=True, help_text="Optional product video URL")
    datasheet_file = models.FileField(upload_to="product_datasheets/", blank=True, null=True, help_text="Optional product datasheet PDF")
    sample_file = models.FileField(upload_to="product_samples/", blank=True, null=True, help_text="Optional downloadable sample file")
    og_image = models.ImageField(upload_to="product_og_images/", blank=True, null=True, help_text="Open Graph image for social sharing")
    bulk_discount_text = models.CharField(max_length=255, blank=True, null=True, help_text="Text describing bulk discount offer")
    express_production = models.BooleanField(default=False, help_text="Whether express production is available")
    trust_badges = models.CharField(max_length=255, blank=True, null=True, help_text="Comma-separated trust badge names or image URLs")

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.meta_title:
            self.meta_title = f"{self.name} - Custom Printing Services"
        if not self.short_description and self.description:
            self.short_description = self.description[:297] + "..." if len(self.description) > 300 else self.description
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('services:product_detail', kwargs={'slug': self.slug})

    def get_starting_price(self):
        """Get the lowest price for this product"""
        pricing = self.pricings.filter(is_active=True).order_by('price_per_unit').first()
        if pricing:
            return pricing.price_per_unit
        return self.price_per_unit

    def get_price_range(self):
        """Get price range for this product"""
        pricings = self.pricings.filter(is_active=True)
        if pricings.exists():
            min_price = pricings.order_by('price_per_unit').first().price_per_unit
            max_price = pricings.order_by('-price_per_unit').first().price_per_unit
            return {'min': min_price, 'max': max_price}
        return {'min': self.price_per_unit, 'max': self.price_per_unit}

class ProductPricing(models.Model):
    """Enhanced pricing model with more flexibility"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='pricings')
    
    # Product specifications (expanded)
    size = models.CharField(max_length=100, blank=True, help_text="e.g., A4, A5, Custom")
    page_count = models.PositiveIntegerField(default=1, help_text="Number of pages")
    paper_type = models.CharField(max_length=100, blank=True, help_text="e.g., 70gsm, 80gsm, Art Paper")
    binding_type = models.CharField(max_length=100, blank=True, help_text="e.g., Perfect, Spiral, Saddle Stitched, Hard Cover, Soft Cover")
    finish = models.CharField(max_length=100, blank=True, help_text="e.g., Matte, Glossy, Velvet")
    colors = models.CharField(max_length=20, blank=True, help_text="e.g., Black & White, Full Color, 4+4, 4+0")
    print_sides = models.CharField(max_length=20, blank=True, help_text="Single-sided, Double-sided")
    cover_finish = models.CharField(max_length=50, blank=True, help_text="e.g., Matte, Glossy, Velvet")
    design_service = models.BooleanField(default=False, help_text="Include design/formatting service")
    isbn_allocation = models.BooleanField(default=False, help_text="ISBN allocation included")
    optional_finishing = models.CharField(max_length=100, blank=True, help_text="e.g., Lamination, UV, Foiling")
    
    # Quantity and pricing
    min_quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    max_quantity = models.PositiveIntegerField(null=True, blank=True, help_text="Leave blank for unlimited")
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    setup_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="One-time setup cost")
    
    # Discounts and modifiers
    volume_discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Percentage discount for this tier")
    rush_order_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.00, help_text="Rush order price multiplier")
    
    # Delivery/Shipping
    delivery_speed = models.CharField(max_length=50, blank=True, help_text="e.g., Standard, Express")
    delivery_location = models.CharField(max_length=100, blank=True, help_text="For location-based pricing")
    
    # Additional options
    turnaround_days = models.PositiveIntegerField(default=5, help_text="Standard turnaround time in days")
    notes = models.TextField(blank=True, help_text="Additional notes or conditions")
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Feature this pricing tier")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Product Pricing'
        verbose_name_plural = 'Product Pricings'
        unique_together = ('product', 'size', 'paper_type', 'binding_type', 'finish', 'colors', 'min_quantity')
        ordering = ['product', 'min_quantity']

    def __str__(self):
        parts = [self.product.name]
        if self.size:
            parts.append(self.size)
        if self.paper_type:
            parts.append(self.paper_type)
        if self.finish:
            parts.append(self.finish)
        if self.colors:
            parts.append(self.colors)
        parts.append(f"Min: {self.min_quantity}")
        parts.append(f"Rs.{self.price_per_unit}")
        return " | ".join(parts)

    def calculate_total_price(self, quantity, rush_order=False, include_setup=True):
        """Calculate total price for given quantity"""
        if quantity < self.min_quantity:
            return None
        
        if self.max_quantity and quantity > self.max_quantity:
            return None
        
        # Base calculation
        unit_price = float(self.price_per_unit)
        
        # Apply volume discount
        if self.volume_discount_percentage > 0:
            unit_price = unit_price * (1 - float(self.volume_discount_percentage) / 100)
        
        # Apply rush order multiplier
        if rush_order:
            unit_price = unit_price * float(self.rush_order_multiplier)
        
        total_price = unit_price * quantity
        
        # Add setup cost
        if include_setup:
            total_price += float(self.setup_cost)
        
        return {
            'unit_price': round(unit_price, 2),
            'subtotal': round(unit_price * quantity, 2),
            'setup_cost': float(self.setup_cost),
            'total_price': round(total_price, 2),
            'savings': round((float(self.price_per_unit) - unit_price) * quantity, 2) if self.volume_discount_percentage > 0 else 0,
            'turnaround_days': self.turnaround_days if not rush_order else max(1, self.turnaround_days - 2)
        }

    def get_price_breakdown(self, quantity, rush_order=False):
        """Get detailed price breakdown"""
        calculation = self.calculate_total_price(quantity, rush_order, include_setup=True)
        if not calculation:
            return None
        
        return {
            'base_unit_price': float(self.price_per_unit),
            'discounted_unit_price': calculation['unit_price'],
            'quantity': quantity,
            'subtotal': calculation['subtotal'],
            'setup_cost': calculation['setup_cost'],
            'total_price': calculation['total_price'],
            'savings': calculation['savings'],
            'volume_discount': float(self.volume_discount_percentage),
            'rush_order': rush_order,
            'turnaround_days': calculation['turnaround_days']
        }

class ProductImage(models.Model):
    """Additional product images for gallery"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')
    alt_text = models.CharField(max_length=200, blank=True)
    caption = models.CharField(max_length=300, blank=True)
    order = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.product.name} - Image {self.order}"

    def save(self, *args, **kwargs):
        if not self.alt_text:
            self.alt_text = f"{self.product.name} image"
        super().save(*args, **kwargs)

class ProductSpecification(models.Model):
    """Additional product specifications"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='specifications')
    name = models.CharField(max_length=100, help_text="e.g., Material, Dimensions")
    value = models.CharField(max_length=200, help_text="e.g., 300gsm Art Paper, 105x148mm")
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    order = models.IntegerField(default=0)
    is_highlighted = models.BooleanField(default=False, help_text="Show prominently")

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.product.name} - {self.name}: {self.value}"

class PricingTier(models.Model):
    """Predefined pricing tiers for easy management"""
    name = models.CharField(max_length=100, help_text="e.g., Economy, Standard, Premium")
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default="#6B7280", help_text="Hex color code")
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


# --- New Models for Product Details ---

class ProductFeature(models.Model):
    product = models.ForeignKey('Product', related_name='features', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=100, blank=True, help_text="Optional icon class or image URL")

    def __str__(self):
        return f"{self.product.name} - {self.title}"


class ProductProcess(models.Model):
    product = models.ForeignKey('Product', related_name='processes', on_delete=models.CASCADE)
    step_number = models.PositiveIntegerField()
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="product_processes/", blank=True, null=True)

    class Meta:
        ordering = ['step_number']

    def __str__(self):
        return f"{self.product.name} - Step {self.step_number}: {self.title}"


class ProductFAQ(models.Model):
    product = models.ForeignKey('Product', related_name='faqs', on_delete=models.CASCADE)
    question = models.CharField(max_length=255)
    answer = models.TextField()

    def __str__(self):
        return f"{self.product.name} FAQ: {self.question}"


class ProductTestimonial(models.Model):
    product = models.ForeignKey('Product', related_name='testimonials', on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=100)
    content = models.TextField()
    rating = models.PositiveSmallIntegerField(default=5)
    date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.product.name} Testimonial by {self.customer_name}"


class ProductSample(models.Model):
    product = models.ForeignKey('Product', related_name='samples', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    file = models.FileField(upload_to="product_samples/", blank=True, null=True)
    image = models.ImageField(upload_to="product_sample_images/", blank=True, null=True)

    def __str__(self):
        return f"{self.product.name} Sample: {self.title}"


class ShippingOption(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    estimated_days = models.PositiveIntegerField(help_text="Estimated delivery days")
    is_express = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class ProductFormField(models.Model):
    """Dynamic form fields for product quote forms"""
    FIELD_TYPES = [
        ('text', 'Text Input'),
        ('number', 'Number Input'),
        ('select', 'Select Dropdown'),
        ('radio', 'Radio Buttons'),
        ('checkbox', 'Checkbox'),
        ('range', 'Range Slider'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='form_fields')
    field_name = models.CharField(max_length=100, help_text="Internal field name (e.g., 'color', 'paper_type')")
    field_label = models.CharField(max_length=200, help_text="Display label (e.g., 'Color', 'Paper Type')")
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES, default='select')
    is_required = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Display order")
    help_text = models.CharField(max_length=300, blank=True)
    
    # For select/radio options (JSON format)
    options = models.TextField(blank=True, help_text='JSON format: [{"value": "option1", "label": "Option 1", "price_modifier": 0}]')
    
    # Default value
    default_value = models.CharField(max_length=200, blank=True)
    
    # Validation
    min_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Conditional display
    show_condition = models.CharField(max_length=200, blank=True, help_text="JSON condition for when to show this field")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'field_name']
        unique_together = ('product', 'field_name')

    def __str__(self):
        return f"{self.product.name} - {self.field_label}"
    
    def get_options(self):
        """Parse JSON options"""
        if self.options:
            try:
                import json
                return json.loads(self.options)
            except json.JSONDecodeError:
                return []
        return []