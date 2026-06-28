# apps/orders/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
import uuid
from decimal import Decimal

User = get_user_model()


class Cart(models.Model):
    """Shopping cart model - supports both logged-in users and anonymous sessions"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_key']),
        ]

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username}"
        return f"Anonymous Cart ({self.session_key})"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def total_with_tax(self):
        # Add GST calculation if needed
        return self.subtotal


class CartItem(models.Model):
    """Individual items in the shopping cart"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    static_product = models.ForeignKey('services.StaticProduct', on_delete=models.CASCADE, null=True, blank=True)
    
    # Design integration
    user_design = models.ForeignKey(
        'templates_mgmt.UserDesign', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    uploaded_file = models.FileField(upload_to='cart/uploads/', blank=True, null=True)
    
    # Quantity and pricing
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Product specifications (size, paper type, etc.)
    specifications = models.JSONField(default=dict, blank=True)

    # Design data from the design studio (Fabric.js canvas JSON, keyed by side)
    design_data = models.JSONField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['cart', 'static_product', 'user_design']

    def __str__(self):
        return f"{self.static_product.name} x {self.quantity}"

    @property
    def total_price(self):
        return self.unit_price * self.quantity

    def save(self, *args, **kwargs):
        if not self.unit_price:
            self.unit_price = self.static_product.base_price
        super().save(*args, **kwargs)


class Order(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('confirmed', 'Confirmed'),
        ('in_production', 'In Production'),
        ('quality_check', 'Quality Check'),
        ('ready', 'Ready for Pickup/Delivery'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    # Basic order information
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Customer information
    customer_name = models.CharField(max_length=255, default='Unknown Customer')
    customer_email = models.EmailField(default='unknown@example.com')
    customer_phone = models.CharField(max_length=20, default='0000000000')
    
    # Billing address
    billing_address_line1 = models.CharField(max_length=255, blank=True, null=True)
    billing_address_line2 = models.CharField(max_length=255, blank=True)
    billing_city = models.CharField(max_length=100, default='Unknown City')
    billing_state = models.CharField(max_length=100, default='Unknown State')
    billing_pincode = models.CharField(max_length=10, default='000000')
    billing_country = models.CharField(max_length=100, default='India')
    
    # Shipping address
    shipping_same_as_billing = models.BooleanField(default=True)
    shipping_address_line1 = models.CharField(max_length=255, blank=True)
    shipping_address_line2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=100, blank=True)
    shipping_state = models.CharField(max_length=100, blank=True)
    shipping_pincode = models.CharField(max_length=10, blank=True)
    shipping_country = models.CharField(max_length=100, blank=True)
    
    # Order totals
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Additional information
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)  # For admin use
    
    # Coupon information
    coupon_code = models.CharField(max_length=50, blank=True)
    coupon_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    estimated_delivery_date = models.DateField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['order_number']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Order {self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        """Generate unique order number"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d')
        random_part = str(uuid.uuid4().hex)[:6].upper()
        return f"SP{timestamp}{random_part}"

    @property
    def can_cancel(self):
        return self.status in ['draft', 'pending', 'paid', 'confirmed']

    @property
    def is_completed(self):
        return self.status in ['completed', 'delivered']


class OrderItem(models.Model):
    """Individual items in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    static_product = models.ForeignKey('services.StaticProduct', on_delete=models.CASCADE, null=True, blank=True)
    
    # Design reference
    user_design = models.ForeignKey(
        'templates_mgmt.UserDesign', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    uploaded_file = models.FileField(upload_to='orders/files/', blank=True, null=True)
    
    # Product details at time of order
    product_name = models.CharField(max_length=255, default='Unknown Product')  # Store name at time of order
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Additional specifications
    specifications = models.JSONField(
        default=dict, 
        blank=True, 
        help_text="Product specifications like size, paper type, etc."
    )
    
    # Production tracking
    production_status = models.CharField(max_length=50, default='pending')
    production_notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"

    def save(self, *args, **kwargs):
        if not self.product_name:
            self.product_name = self.static_product.name
        if not self.total_price:
            self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class OrderStatusHistory(models.Model):
    """Track all status changes for orders"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, default='pending')
    notes = models.TextField(blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Order status histories'

    def __str__(self):
        return f"Order {self.order.order_number}: {self.old_status} → {self.new_status}"


class QuoteRequest(models.Model):
    """Custom quote requests from customers"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('in_review', 'Under Review'),
        ('quoted', 'Quote Sent'),
        ('accepted', 'Quote Accepted'),
        ('rejected', 'Quote Rejected'),
        ('expired', 'Expired'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quote_requests')
    quote_number = models.CharField(max_length=20, unique=True, default='Q0000')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Customer information
    customer_name = models.CharField(max_length=255, default='Unknown Customer')
    customer_email = models.EmailField(default='unknown@example.com')
    customer_phone = models.CharField(max_length=20, default='0000000000')
    company_name = models.CharField(max_length=255, blank=True)
    
    # Quote details
    description = models.TextField()
    requirements = models.TextField(blank=True)
    quantity = models.PositiveIntegerField()
    budget_range = models.CharField(max_length=100, blank=True)
    
    # Quote response
    quoted_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quote_notes = models.TextField(blank=True)
    quote_valid_until = models.DateField(null=True, blank=True)
    
    # Files
    reference_files = models.FileField(upload_to='quotes/files/', blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    quoted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Quote {self.quote_number}"

    def save(self, *args, **kwargs):
        if not self.quote_number:
            self.quote_number = self.generate_quote_number()
        super().save(*args, **kwargs)

    def generate_quote_number(self):
        """Generate unique quote number"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d')
        random_part = str(uuid.uuid4().hex)[:4].upper()
        return f"QT{timestamp}{random_part}"


class QuoteRequestItem(models.Model):
    """Individual items in a quote request"""
    quote_request = models.ForeignKey(QuoteRequest, on_delete=models.CASCADE, related_name='items')
    static_product = models.ForeignKey('services.StaticProduct', on_delete=models.CASCADE, null=True, blank=True)
    
    description = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    specifications = models.JSONField(default=dict, blank=True)
    
    # Files for this item
    design_file = models.FileField(upload_to='quotes/designs/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.description} x {self.quantity}"


class Coupon(models.Model):
    """Discount coupons"""
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount'),
    ]

    code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255, blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Usage limits
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    
    # Validity
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    
    # Minimum order amount
    minimum_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.code

    @property
    def is_valid(self):
        from django.utils import timezone
        now = timezone.now()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_until and
            (self.usage_limit is None or self.used_count < self.usage_limit)
        )

    def apply_discount(self, amount):
        """Calculate discount amount for given order amount"""
        if not self.is_valid or amount < self.minimum_amount:
            return Decimal('0.00')
        
        if self.discount_type == 'percentage':
            return amount * (self.discount_value / 100)
        else:  # fixed_amount
            return min(self.discount_value, amount)


class Quote(models.Model):
    """Professional quotes generated from cart"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent to Customer'),
        ('viewed', 'Viewed by Customer'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quotes')
    quote_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Cart snapshot at time of quote generation
    cart_snapshot = models.JSONField(help_text="Complete cart state when quote was generated")

    # Quote totals
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)

    # Quote validity
    valid_until = models.DateTimeField()

    # Notes and communication
    customer_notes = models.TextField(blank=True, help_text="Customer requirements or notes")
    internal_notes = models.TextField(blank=True, help_text="Internal notes for production")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    viewed_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['quote_number']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Quote {self.quote_number}"

    def save(self, *args, **kwargs):
        if not self.quote_number:
            self.quote_number = self.generate_quote_number()
        super().save(*args, **kwargs)

    def generate_quote_number(self):
        """Generate unique quote number"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d')
        random_part = str(uuid.uuid4().hex)[:6].upper()
        return f"QT{timestamp}{random_part}"

    @property
    def is_valid(self):
        from django.utils import timezone
        return timezone.now() <= self.valid_until and self.status not in ['expired', 'rejected']

    @property
    def can_accept(self):
        return self.status in ['sent', 'viewed'] and self.is_valid


class CouponUsage(models.Model):
    """Track coupon usage"""
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usage_records')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['coupon', 'order']

    def __str__(self):
        return f"Coupon {self.coupon.code} used by {self.user.username}"