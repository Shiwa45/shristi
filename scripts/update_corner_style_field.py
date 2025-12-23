import os
import sys
import django
import json

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shirsti_printing.settings')
django.setup()

from apps.services.models import StaticProduct, ProductFormField

def update_corner_style_field():
    """Update Corner Style field to use image_grid type with image URLs"""
    
    # Find Standard Business Card product
    product = StaticProduct.objects.filter(name__iexact="Standard Business Card").first()
    
    if not product:
        print("Standard Business Card product not found!")
        return
    
    print(f"Found product: {product.name}")
    
    # Find Corner Style field
    corner_field = ProductFormField.objects.filter(
        static_product=product,
        field_name__icontains="corner"
    ).first()
    
    if not corner_field:
        print("Corner Style field not found!")
        return
    
    print(f"Found field: {corner_field.field_label}")
    
    # Update field type to image_grid
    corner_field.field_type = 'image_grid'
    
    # Update options to include image URLs
    new_options = [
        {
            "value": "Straight Corners",
            "label": "Straight Corners",
            "price_modifier": 0,
            "image_url": "/static/images/corner-styles/straight-corners.svg"
        },
        {
            "value": "Rounded Corners",
            "label": "Rounded Corners",
            "price_modifier": 0,
            "image_url": "/static/images/corner-styles/rounded-corners.svg"
        }
    ]
    
    corner_field.options = json.dumps(new_options)
    corner_field.save()
    
    print(f"✓ Updated '{corner_field.field_label}' to image_grid type")
    print(f"✓ Added image URLs to options")
    print("\nNew options:")
    for opt in new_options:
        print(f"  - {opt['label']}: {opt['image_url']}")

if __name__ == "__main__":
    update_corner_style_field()
