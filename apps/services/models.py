# apps/services/models.py - Simplified with only StaticProduct

from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import json

class ServiceCategory(models.Model):
    ALLOWED_CATEGORIES = [
        'book-printing',
        'paper-boxes', 
        'marketing-material',
        'stationery'
    ]

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    image = models.ImageField(upload_to='categories/', blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    # Category-specific configuration
    has_sequential_form = models.BooleanField(
        default=False, 
        help_text="Enable sequential form progression for this category"
    )
    form_configuration = models.JSONField(
        default=dict,
        blank=True,
        help_text="Category-specific form configuration and settings"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = "Service Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        
        # Validate that only allowed categories can be active
        if self.is_active and self.slug not in self.ALLOWED_CATEGORIES:
            raise ValueError(f"Only the following categories are allowed: {', '.join(self.ALLOWED_CATEGORIES)}")
        
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('services:category', kwargs={'slug': self.slug})

    def get_category_specific_url(self):
        """Get URL for category-specific page"""
        if self.slug in self.ALLOWED_CATEGORIES:
            return reverse('services:category_specific', kwargs={'category_slug': self.slug})
        return self.get_absolute_url()

    def get_design_tool_count(self):
        """Get count of products with design tool enabled"""
        return self.static_products.filter(design_tool_enabled=True, is_active=True).count()

    def get_category_form_fields(self):
        """Get form fields for this category"""
        if self.slug in self.ALLOWED_CATEGORIES:
            return CategoryFormField.objects.filter(
                category=self.slug,
                is_active=True
            ).order_by('section_order', 'order')
        return CategoryFormField.objects.none()

    def get_form_sections(self):
        """Get organized form sections for this category"""
        fields = self.get_category_form_fields()
        sections = {}
        
        for field in fields:
            section_key = field.section
            if section_key not in sections:
                sections[section_key] = {
                    'name': field.get_section_display(),
                    'order': field.section_order,
                    'fields': []
                }
            sections[section_key]['fields'].append(field)
        
        # Sort sections by order
        return dict(sorted(sections.items(), key=lambda x: x[1]['order']))

    def get_pricing_rules(self):
        """Get pricing rules for this category"""
        if self.slug in self.ALLOWED_CATEGORIES:
            return CategoryPricingRule.objects.filter(
                category=self.slug,
                is_active=True
            ).order_by('-priority', 'rule_name')
        return CategoryPricingRule.objects.none()

    def is_category_specific(self):
        """Check if this category has category-specific configuration"""
        return self.slug in self.ALLOWED_CATEGORIES

    def get_form_configuration(self):
        """Parse and return form configuration"""
        if not self.form_configuration:
            return {}
        return self.form_configuration if isinstance(self.form_configuration, dict) else {}

    @classmethod
    def get_active_categories(cls):
        """Get only the 4 allowed active categories"""
        return cls.objects.filter(
            slug__in=cls.ALLOWED_CATEGORIES,
            is_active=True
        ).order_by('order', 'name')

    @classmethod
    def validate_category_limits(cls):
        """Ensure only allowed categories are active"""
        active_count = cls.objects.filter(is_active=True).count()
        active_allowed = cls.objects.filter(
            slug__in=cls.ALLOWED_CATEGORIES,
            is_active=True
        ).count()
        
        if active_count != active_allowed:
            # Deactivate any categories not in allowed list
            cls.objects.exclude(slug__in=cls.ALLOWED_CATEGORIES).update(is_active=False)
            return False
        return True


class StaticProduct(models.Model):
    """
    Static product model with predefined options and pricing
    Each product has its own static specifications and pricing tiers
    """

    # Basic Information
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='static_products')
    description = models.TextField()
    short_description = models.TextField(max_length=300)

    # Design Tool Integration
    design_tool_enabled = models.BooleanField(default=False, help_text="Enable design tool for this product")
    canvas_width = models.IntegerField(null=True, blank=True, help_text="Canvas width in pixels for design tool")
    canvas_height = models.IntegerField(null=True, blank=True, help_text="Canvas height in pixels for design tool")

    # Images and Media
    featured_image = models.ImageField(upload_to='products/featured/', blank=True, null=True, help_text="Main product image")
    hero_image = models.ImageField(upload_to='products/hero/', blank=True, null=True, help_text="Hero section image")

    # SEO
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    # Pricing Configuration
    base_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    price_unit = models.CharField(max_length=50, default="per piece", help_text="e.g., per piece, per page, per 100 pieces")

    # Static Options (JSON fields for predefined choices)
    available_sizes = models.JSONField(
        default=list,
        help_text="List of available sizes with price modifiers. Format: [{'name': 'A4', 'price_modifier': 0}, ...]"
    )
    available_papers = models.JSONField(
        default=list,
        help_text="List of paper types with price modifiers. Format: [{'name': '80 GSM', 'price_modifier': 25}, ...]"
    )
    available_finishes = models.JSONField(
        default=list,
        help_text="List of finishes with price modifiers. Format: [{'name': 'Matte', 'price_modifier': 50}, ...]"
    )
    available_bindings = models.JSONField(
        default=list,
        help_text="List of binding options with price modifiers. Format: [{'name': 'Saddle Stitch', 'price_modifier': 0}, ...]"
    )
    color_options = models.JSONField(
        default=list,
        help_text="List of color options with price modifiers. Format: [{'name': 'Full Color', 'price_modifier': 200}, ...]"
    )

    # Quantity-based pricing tiers
    quantity_tiers = models.JSONField(
        default=list,
        help_text="Quantity-based pricing tiers. Format: [{'min_qty': 100, 'max_qty': 249, 'discount_percent': 0}, ...]"
    )

    # Additional Services
    rush_order_available = models.BooleanField(default=True)
    rush_order_percentage = models.IntegerField(default=50, help_text="Rush order surcharge percentage")
    design_service_available = models.BooleanField(default=True)
    design_service_price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('999.00'))
    turnaround_time = models.CharField(max_length=100, blank=True, help_text="e.g., '3-5 business days'")

    # Product Features and Specifications
    key_features = models.JSONField(
        default=list,
        help_text="List of key features. Format: [{'title': 'High Quality', 'description': 'Premium materials'}, ...]"
    )
    specifications = models.JSONField(
        default=dict,
        help_text="Product specifications. Format: {'Material': '300 GSM Art Paper', 'Size': 'Custom sizes available'}"
    )

    # Status and Ordering
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.meta_title:
            self.meta_title = f"{self.name} - Shirsti Printing"
        if not self.meta_description:
            self.meta_description = f"Professional {self.name.lower()} printing services. {self.short_description}"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('services:product_detail', kwargs={'category_slug': self.category.slug, 'product_slug': self.slug})

    def calculate_price(self, quantity=100, size=None, paper=None, finish=None,
                       binding=None, color=None, rush_order=False, design_service=False):
        """Calculate price based on options"""
        base_price = float(self.base_price)

        # Apply modifiers
        if size and self.available_sizes:
            for size_option in self.available_sizes:
                if size_option.get('name') == size:
                    base_price += float(size_option.get('price_modifier', 0))
                    break

        if paper and self.available_papers:
            for paper_option in self.available_papers:
                if paper_option.get('name') == paper:
                    base_price += float(paper_option.get('price_modifier', 0))
                    break

        if finish and self.available_finishes:
            for finish_option in self.available_finishes:
                if finish_option.get('name') == finish:
                    base_price += float(finish_option.get('price_modifier', 0))
                    break

        if color and self.color_options:
            for color_option in self.color_options:
                if color_option.get('name') == color:
                    base_price += float(color_option.get('price_modifier', 0))
                    break

        # Calculate subtotal
        subtotal = base_price * quantity

        # Apply quantity discount
        if self.quantity_tiers:
            for tier in self.quantity_tiers:
                min_qty = tier.get('min_qty', 0)
                max_qty = tier.get('max_qty', float('inf'))
                if min_qty <= quantity <= max_qty:
                    discount_percent = tier.get('discount_percent', 0)
                    subtotal = subtotal * (1 - discount_percent / 100)
                    break

        # Apply rush order
        if rush_order and self.rush_order_available:
            subtotal = subtotal * (1 + self.rush_order_percentage / 100)

        # Add design service
        if design_service and self.design_service_available:
            subtotal += float(self.design_service_price)

        return Decimal(str(subtotal)).quantize(Decimal('0.01'))


class CategoryFormField(models.Model):
    """Category-specific form fields for sequential form configurations"""
    FIELD_TYPES = [
        ('text', 'Text Input'),
        ('number', 'Number Input'),
        ('select', 'Select Dropdown'),
        ('radio', 'Radio Buttons'),
        ('checkbox', 'Checkbox'),
        ('range', 'Range Slider'),
        ('file', 'File Upload'),
        ('conditional_group', 'Conditional Field Group'),
    ]

    CATEGORIES = [
        ('book-printing', 'Book Printing'),
        ('paper-boxes', 'Paper Boxes'),
        ('marketing-material', 'Marketing Material'),
        ('stationery', 'Stationery'),
    ]

    FIELD_SECTIONS = [
        # Book Printing Sections
        ('interior_color', 'Interior Color'),
        ('book_size_pages', 'Book Size And Page Count'),
        ('paper_type', 'Paper Type'),
        ('binding_type', 'Binding Type'),
        ('cover_finish', 'Cover Finish'),
        ('designing_formatting', 'Designing And Formatting'),
        ('isbn_allocation', 'ISBN Allocation'),
        
        # Paper Boxes Sections
        ('box_dimensions', 'Box Dimensions'),
        ('material_type', 'Material Type'),
        ('printing_options', 'Printing Options'),
        ('finishing_options', 'Finishing Options'),
        
        # Marketing Material Sections
        ('material_type_selection', 'Material Type Selection'),
        ('size_options', 'Size Options'),
        ('design_options', 'Design Options'),
        
        # Stationery Sections
        ('stationery_type', 'Stationery Type'),
        ('specifications', 'Specifications'),
        ('additional_services', 'Additional Services'),
        
        # Common Sections
        ('file_uploads', 'File Uploads'),
        ('quantity_pricing', 'Quantity & Pricing'),
    ]

    # Category and field identification
    category = models.CharField(max_length=50, choices=CATEGORIES)
    field_name = models.CharField(max_length=100, help_text="Internal field name (e.g., 'interior_color', 'paper_type')")
    field_label = models.CharField(max_length=200, help_text="Display label (e.g., 'Interior Color', 'Paper Type')")
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES, default='select')
    section = models.CharField(max_length=50, choices=FIELD_SECTIONS, help_text="Section to group this field under")

    # Display configuration
    is_required = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Display order within section")
    section_order = models.IntegerField(default=0, help_text="Order of the section itself")
    help_text = models.CharField(max_length=500, blank=True)
    placeholder = models.CharField(max_length=200, blank=True, help_text="Input placeholder text")
    description = models.TextField(blank=True, help_text="Section description text")

    # Field options and validation
    options = models.JSONField(
        default=list,
        blank=True,
        help_text='List of field options. Format: [{"value": "option1", "label": "Option 1", "price_modifier": 0, "description": ""}]'
    )
    default_value = models.CharField(max_length=200, blank=True)
    min_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Conditional display logic
    show_condition = models.JSONField(
        default=dict,
        blank=True,
        help_text='Condition for showing this field. Format: {"field": "interior_color", "value": "combine_color", "operator": "equals"}'
    )
    triggers_fields = models.JSONField(
        default=list,
        blank=True,
        help_text='Array of field names this field can trigger: ["bw_page_count", "color_page_count"]'
    )

    # Validation rules
    validation_rules = models.JSONField(
        default=dict,
        blank=True,
        help_text='Validation rules for the field. Format: {"min_pages_for_binding": 30, "allowed_file_types": ["pdf", "doc", "docx"]}'
    )

    # Layout and styling
    css_classes = models.CharField(max_length=200, blank=True, help_text="Additional CSS classes")
    grid_columns = models.IntegerField(default=1, help_text="Grid columns span (1-3)")

    # Pricing impact
    is_price_affecting = models.BooleanField(default=False, help_text="Does this field affect pricing calculations?")
    price_modifier_type = models.CharField(
        max_length=20,
        choices=[
            ('fixed', 'Fixed Amount'),
            ('percentage', 'Percentage'),
            ('per_unit', 'Per Unit'),
            ('conditional', 'Conditional Logic')
        ],
        default='fixed'
    )
    price_modifier_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    price_modifier_conditions = models.JSONField(
        default=dict,
        blank=True,
        help_text='Conditional pricing rules. Format: {"combine_color": {"bw_pages": 2.5, "color_pages": 8.0}}'
    )

    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'section_order', 'order']
        unique_together = ('category', 'field_name')
        verbose_name = "Category Form Field"
        verbose_name_plural = "Category Form Fields"

    def __str__(self):
        return f"{self.get_category_display()} - {self.field_label} ({self.field_name})"

    def get_options(self):
        """Parse and return field options"""
        if not self.options:
            return []
        return self.options if isinstance(self.options, list) else []

    def get_show_condition(self):
        """Parse and return show condition"""
        if not self.show_condition:
            return None
        return self.show_condition if isinstance(self.show_condition, dict) else None

    def get_triggered_fields(self):
        """Parse and return triggered fields"""
        if not self.triggers_fields:
            return []
        return self.triggers_fields if isinstance(self.triggers_fields, list) else []

    def get_validation_rules(self):
        """Parse and return validation rules"""
        if not self.validation_rules:
            return {}
        return self.validation_rules if isinstance(self.validation_rules, dict) else {}

    def should_show(self, form_data):
        """Check if this field should be displayed based on current form data"""
        condition = self.get_show_condition()
        if not condition:
            return True

        field_name = condition.get('field')
        expected_value = condition.get('value')
        operator = condition.get('operator', 'equals')

        if field_name not in form_data:
            return False

        actual_value = form_data[field_name]

        if operator == 'equals':
            return str(actual_value) == str(expected_value)
        elif operator == 'not_equals':
            return str(actual_value) != str(expected_value)
        elif operator == 'in':
            return actual_value in expected_value
        elif operator == 'not_in':
            return actual_value not in expected_value
        elif operator == 'greater_than':
            try:
                return float(actual_value) > float(expected_value)
            except (ValueError, TypeError):
                return False
        elif operator == 'less_than':
            try:
                return float(actual_value) < float(expected_value)
            except (ValueError, TypeError):
                return False

        return True

    def calculate_price_modifier(self, selected_value, form_data=None, quantity=1):
        """Calculate price modifier for selected value"""
        if not self.is_price_affecting:
            return Decimal('0.00')

        if self.price_modifier_type == 'conditional' and self.price_modifier_conditions:
            # Handle conditional pricing (e.g., combine color with different page rates)
            conditions = self.price_modifier_conditions
            if selected_value in conditions and form_data:
                condition_rules = conditions[selected_value]
                total_modifier = Decimal('0.00')
                
                for field_key, rate in condition_rules.items():
                    if field_key in form_data:
                        field_value = form_data[field_key]
                        try:
                            total_modifier += Decimal(str(rate)) * Decimal(str(field_value))
                        except (ValueError, TypeError):
                            continue
                
                return total_modifier
        
        # Handle option-based pricing
        options = self.get_options()
        for option in options:
            if option.get('value') == selected_value:
                modifier = Decimal(str(option.get('price_modifier', 0)))
                
                if self.price_modifier_type == 'per_unit':
                    return modifier * quantity
                elif self.price_modifier_type == 'percentage':
                    # Percentage modifiers need base price context
                    return modifier  # Will be applied as percentage in calculator
                else:  # fixed
                    return modifier

        return self.price_modifier_value

    def validate_field_value(self, value, form_data=None):
        """Validate field value against validation rules"""
        errors = []
        rules = self.get_validation_rules()
        
        if self.is_required and not value:
            errors.append(f"{self.field_label} is required")
            return errors
        
        if not value:
            return errors
        
        # Numeric validation
        if self.field_type == 'number':
            try:
                num_value = float(value)
                if self.min_value and num_value < float(self.min_value):
                    errors.append(f"{self.field_label} must be at least {self.min_value}")
                if self.max_value and num_value > float(self.max_value):
                    errors.append(f"{self.field_label} must be no more than {self.max_value}")
            except (ValueError, TypeError):
                errors.append(f"{self.field_label} must be a valid number")
        
        # Custom validation rules
        if 'min_pages_for_binding' in rules and form_data:
            min_pages = rules['min_pages_for_binding']
            page_count = form_data.get('page_count', 0)
            try:
                if int(page_count) < min_pages and value in ['paperback_perfect', 'hardcover']:
                    errors.append(f"{value.replace('_', ' ').title()} binding requires at least {min_pages} pages")
            except (ValueError, TypeError):
                pass
        
        if 'allowed_file_types' in rules and self.field_type == 'file':
            allowed_types = rules['allowed_file_types']
            # This would be validated on the frontend/backend during file upload
            pass
        
        return errors


class ProductFormField(models.Model):
    """Enhanced dynamic form fields for product quote forms with conditional logic"""
    FIELD_TYPES = [
        ('text', 'Text Input'),
        ('number', 'Number Input'),
        ('select', 'Select Dropdown'),
        ('radio', 'Radio Buttons'),
        ('checkbox', 'Checkbox'),
        ('range', 'Range Slider'),
        ('file', 'File Upload'),
        ('conditional_group', 'Conditional Field Group'),
    ]

    FIELD_SECTIONS = [
        ('product_specs', 'Product Specifications'),
        ('design_options', 'Design Options'),
        ('printing_options', 'Printing Options'),
        ('finishing_options', 'Finishing Options'),
        ('additional_services', 'Additional Services'),
        ('file_uploads', 'File Uploads'),
        ('quantity_pricing', 'Quantity & Pricing'),
    ]

    # Only StaticProduct reference now
    static_product = models.ForeignKey('StaticProduct', on_delete=models.CASCADE, related_name='form_fields')

    # Field identification
    field_name = models.CharField(max_length=100, help_text="Internal field name (e.g., 'interior_color', 'paper_type')")
    field_label = models.CharField(max_length=200, help_text="Display label (e.g., 'Interior Color', 'Paper Type')")
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES, default='select')
    field_section = models.CharField(max_length=20, choices=FIELD_SECTIONS, default='product_specs', help_text="Section to group this field under")

    # Display configuration
    is_required = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Display order within section")
    section_order = models.IntegerField(default=0, help_text="Order of the section itself")
    help_text = models.CharField(max_length=500, blank=True)
    placeholder = models.CharField(max_length=200, blank=True, help_text="Input placeholder text")

    # Field options and validation
    options = models.TextField(blank=True, help_text='JSON format: [{"value": "option1", "label": "Option 1", "price_modifier": 0, "description": ""}]')
    default_value = models.CharField(max_length=200, blank=True)
    min_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Conditional display logic
    show_condition = models.TextField(blank=True, help_text='JSON condition: {"field": "interior_color", "value": "combine_color", "operator": "equals"}')
    triggers_fields = models.TextField(blank=True, help_text='JSON array of field names this field can trigger: ["bw_page_count", "color_page_count"]')

    # Layout and styling
    css_classes = models.CharField(max_length=200, blank=True, help_text="Additional CSS classes")
    grid_columns = models.IntegerField(default=1, help_text="Grid columns span (1-3)")

    # Pricing impact
    is_price_affecting = models.BooleanField(default=False, help_text="Does this field affect pricing calculations?")
    price_modifier = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Base price modifier for this field")

    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['static_product', 'section_order', 'order']
        unique_together = ('static_product', 'field_name')

    def __str__(self):
        product_name = self.static_product.name if self.static_product else "Unknown Product"
        return f"{product_name} - {self.field_label} ({self.field_name})"

    def get_options(self):
        """Parse and return field options"""
        if not self.options:
            return []
        try:
            return json.loads(self.options)
        except (json.JSONDecodeError, TypeError):
            return []

    def get_show_condition(self):
        """Parse and return show condition"""
        if not self.show_condition:
            return None
        try:
            return json.loads(self.show_condition)
        except (json.JSONDecodeError, TypeError):
            return None

    def get_triggered_fields(self):
        """Parse and return triggered fields"""
        if not self.triggers_fields:
            return []
        try:
            return json.loads(self.triggers_fields)
        except (json.JSONDecodeError, TypeError):
            return []

    def should_show(self, form_data):
        """Check if this field should be displayed based on current form data"""
        condition = self.get_show_condition()
        if not condition:
            return True

        field_name = condition.get('field')
        expected_value = condition.get('value')
        operator = condition.get('operator', 'equals')

        if field_name not in form_data:
            return False

        actual_value = form_data[field_name]

        if operator == 'equals':
            return str(actual_value) == str(expected_value)
        elif operator == 'not_equals':
            return str(actual_value) != str(expected_value)
        elif operator == 'in':
            return actual_value in expected_value
        elif operator == 'not_in':
            return actual_value not in expected_value

        return True

    def calculate_price_modifier(self, selected_value, quantity=1):
        """Calculate price modifier for selected value"""
        if not self.is_price_affecting:
            return Decimal('0.00')

        options = self.get_options()
        for option in options:
            if option.get('value') == selected_value:
                modifier = Decimal(str(option.get('price_modifier', 0)))
                return modifier * quantity

        return self.price_modifier * quantity


class StaticProductImage(models.Model):
    """Additional images for static products"""
    product = models.ForeignKey(StaticProduct, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')
    alt_text = models.CharField(max_length=200, blank=True)
    caption = models.CharField(max_length=300, blank=True)
    is_featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} - Image {self.id}"


class StaticProductFAQ(models.Model):
    """Product-specific frequently asked questions"""
    product = models.ForeignKey(StaticProduct, on_delete=models.CASCADE, related_name='faqs')
    question = models.CharField(max_length=300)
    answer = models.TextField()
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} - {self.question[:50]}"


class StaticProductSample(models.Model):
    """Product samples and templates"""
    product = models.ForeignKey(StaticProduct, on_delete=models.CASCADE, related_name='samples')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    sample_file = models.FileField(upload_to='product_samples/')
    thumbnail = models.ImageField(upload_to='product_samples/thumbs/', blank=True)
    file_type = models.CharField(max_length=50, help_text="e.g., PDF, AI, PSD")
    file_size = models.CharField(max_length=20, blank=True)
    is_free = models.BooleanField(default=True)
    download_count = models.IntegerField(default=0)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} - {self.title}"


class StaticProductTestimonial(models.Model):
    """Customer testimonials for specific products"""
    product = models.ForeignKey(StaticProduct, on_delete=models.CASCADE, related_name='testimonials')
    customer_name = models.CharField(max_length=200)
    customer_company = models.CharField(max_length=200, blank=True)
    testimonial = models.TextField()
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], default=5)
    is_featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} - {self.customer_name}"


class CategoryPricingRule(models.Model):
    """Category-specific pricing rules for dynamic price calculations"""
    RULE_TYPES = [
        ('base_price', 'Base Price'),
        ('quantity_tier', 'Quantity Tier'),
        ('option_modifier', 'Option Modifier'),
        ('conditional_pricing', 'Conditional Pricing'),
        ('page_based_pricing', 'Page-Based Pricing'),
        ('dimension_based_pricing', 'Dimension-Based Pricing'),
    ]

    CATEGORIES = [
        ('book-printing', 'Book Printing'),
        ('paper-boxes', 'Paper Boxes'),
        ('marketing-material', 'Marketing Material'),
        ('stationery', 'Stationery'),
    ]

    # Rule identification
    category = models.CharField(max_length=50, choices=CATEGORIES)
    rule_name = models.CharField(max_length=100)
    rule_type = models.CharField(max_length=30, choices=RULE_TYPES)
    description = models.TextField(blank=True, help_text="Description of what this rule does")

    # Rule configuration
    conditions = models.JSONField(
        default=dict,
        help_text="Conditions for rule application. Format: {'field': 'interior_color', 'value': 'combine_color'}"
    )
    pricing_formula = models.JSONField(
        default=dict,
        help_text="Pricing calculation formula. Format: {'base_rate': 2.5, 'multiplier_field': 'page_count'}"
    )

    # Quantity-based rules
    min_quantity = models.IntegerField(null=True, blank=True, help_text="Minimum quantity for this rule")
    max_quantity = models.IntegerField(null=True, blank=True, help_text="Maximum quantity for this rule")
    discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Discount percentage for quantity tiers"
    )

    # Fixed pricing values
    fixed_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Fixed price amount for this rule"
    )
    price_per_unit = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Price per unit (e.g., per page, per square inch)"
    )

    # Priority and status
    priority = models.IntegerField(default=0, help_text="Rule priority (higher numbers = higher priority)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', '-priority', 'rule_name']
        verbose_name = "Category Pricing Rule"
        verbose_name_plural = "Category Pricing Rules"

    def __str__(self):
        return f"{self.get_category_display()} - {self.rule_name}"

    def get_conditions(self):
        """Parse and return rule conditions"""
        if not self.conditions:
            return {}
        return self.conditions if isinstance(self.conditions, dict) else {}

    def get_pricing_formula(self):
        """Parse and return pricing formula"""
        if not self.pricing_formula:
            return {}
        return self.pricing_formula if isinstance(self.pricing_formula, dict) else {}

    def applies_to(self, form_data, quantity=None):
        """Check if this rule applies to the given form data and quantity"""
        conditions = self.get_conditions()
        
        # Check quantity range
        if quantity is not None:
            if self.min_quantity and quantity < self.min_quantity:
                return False
            if self.max_quantity and quantity > self.max_quantity:
                return False
        
        # Check field conditions
        for field_name, expected_value in conditions.items():
            if field_name not in form_data:
                return False
            
            actual_value = form_data[field_name]
            
            # Handle different condition types
            if isinstance(expected_value, dict):
                operator = expected_value.get('operator', 'equals')
                value = expected_value.get('value')
                
                if operator == 'equals' and str(actual_value) != str(value):
                    return False
                elif operator == 'not_equals' and str(actual_value) == str(value):
                    return False
                elif operator == 'in' and actual_value not in value:
                    return False
                elif operator == 'greater_than':
                    try:
                        if float(actual_value) <= float(value):
                            return False
                    except (ValueError, TypeError):
                        return False
                elif operator == 'less_than':
                    try:
                        if float(actual_value) >= float(value):
                            return False
                    except (ValueError, TypeError):
                        return False
            else:
                # Simple equality check
                if str(actual_value) != str(expected_value):
                    return False
        
        return True

    def calculate_price(self, form_data, quantity=1, base_price=0):
        """Calculate price based on this rule"""
        if not self.applies_to(form_data, quantity):
            return Decimal('0.00')
        
        formula = self.get_pricing_formula()
        
        if self.rule_type == 'base_price':
            return Decimal(str(self.fixed_price or 0))
        
        elif self.rule_type == 'quantity_tier':
            if self.discount_percentage > 0:
                discount_amount = Decimal(str(base_price)) * (Decimal(str(self.discount_percentage)) / 100)
                return -discount_amount  # Negative for discount
            return Decimal('0.00')
        
        elif self.rule_type == 'option_modifier':
            return Decimal(str(self.fixed_price or 0))
        
        elif self.rule_type == 'conditional_pricing':
            # Handle complex conditional pricing (e.g., combine color with different page rates)
            total_price = Decimal('0.00')
            
            for field_key, rate in formula.items():
                if field_key in form_data:
                    try:
                        field_value = Decimal(str(form_data[field_key]))
                        rate_value = Decimal(str(rate))
                        total_price += field_value * rate_value
                    except (ValueError, TypeError):
                        continue
            
            return total_price
        
        elif self.rule_type == 'page_based_pricing':
            # Calculate based on page count
            page_count = form_data.get('page_count', 0)
            bw_pages = form_data.get('bw_page_count', 0)
            color_pages = form_data.get('color_page_count', 0)
            
            try:
                total_price = Decimal('0.00')
                
                if 'bw_rate' in formula and bw_pages:
                    total_price += Decimal(str(bw_pages)) * Decimal(str(formula['bw_rate']))
                
                if 'color_rate' in formula and color_pages:
                    total_price += Decimal(str(color_pages)) * Decimal(str(formula['color_rate']))
                
                if 'standard_rate' in formula and page_count:
                    total_price += Decimal(str(page_count)) * Decimal(str(formula['standard_rate']))
                
                return total_price
            except (ValueError, TypeError):
                return Decimal('0.00')
        
        elif self.rule_type == 'dimension_based_pricing':
            # Calculate based on dimensions (for paper boxes)
            length = form_data.get('length', 0)
            width = form_data.get('width', 0)
            height = form_data.get('height', 0)
            
            try:
                if 'area_rate' in formula:
                    area = Decimal(str(length)) * Decimal(str(width))
                    return area * Decimal(str(formula['area_rate']))
                elif 'volume_rate' in formula:
                    volume = Decimal(str(length)) * Decimal(str(width)) * Decimal(str(height))
                    return volume * Decimal(str(formula['volume_rate']))
            except (ValueError, TypeError):
                return Decimal('0.00')
        
        return Decimal(str(self.price_per_unit or 0)) * quantity


# Additional utility models for shipping and pricing tiers
class PricingTier(models.Model):
    """Quantity-based pricing tiers for products"""
    product = models.ForeignKey(StaticProduct, on_delete=models.CASCADE, related_name='pricing_tiers')
    min_quantity = models.IntegerField(validators=[MinValueValidator(1)])
    max_quantity = models.IntegerField(null=True, blank=True, help_text="Leave blank for unlimited")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        ordering = ['min_quantity']
        unique_together = ('product', 'min_quantity')

    def __str__(self):
        max_qty = self.max_quantity or "∞"
        return f"{self.product.name}: {self.min_quantity}-{max_qty} ({self.discount_percentage}% off)"


class ShippingOption(models.Model):
    """Shipping options for products"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    delivery_days_min = models.IntegerField()
    delivery_days_max = models.IntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.delivery_days_min}-{self.delivery_days_max} days)"