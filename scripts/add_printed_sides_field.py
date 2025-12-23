import os
import sys
import django
import json

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shirsti_printing.settings')
django.setup()

from apps.services.models import StaticProduct, ProductFormField
from django.utils.text import slugify

def add_printed_sides_field():
    """Add Printed Sides field to Corporate Letter Head"""
    
    # Find Corporate Letter Head product
    product = StaticProduct.objects.filter(name__iexact="Corporate Letter Head").first()
    
    if not product:
        print("Corporate Letter Head product not found!")
        return
    
    print(f"Found product: {product.name}")
    
    # Check if field already exists
    existing_field = ProductFormField.objects.filter(
        static_product=product,
        field_name="printed_sides"
    ).first()
    
    if existing_field:
        print(f"Field 'Printed Sides' already exists. Updating...")
        existing_field.delete()
    
    # Get the current max order
    max_order = ProductFormField.objects.filter(static_product=product).aggregate(
        max_order=models.Max('order')
    )['max_order'] or 0
    
    # Create Printed Sides field
    options = [
        {
            "value": "Single Side",
            "label": "Single Side",
            "price_modifier": 0
        },
        {
            "value": "Both Sides",
            "label": "Both Sides",
            "price_modifier": 0
        }
    ]
    
    field = ProductFormField.objects.create(
        static_product=product,
        field_name='printed_sides',
        field_label='Printed Sides',
        field_type='select',
        order=max_order + 1,
        is_required=True,
        is_price_affecting=True,
        options=json.dumps(options)
    )
    
    print(f"✓ Added 'Printed Sides' field to {product.name}")
    print(f"  - Order: {field.order}")
    print(f"  - Options: Single Side, Both Sides")

if __name__ == "__main__":
    from django.db import models
    add_printed_sides_field()
