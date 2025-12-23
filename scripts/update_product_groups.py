import os
import sys
import django
import json
from django.utils.text import slugify

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shirsti_printing.settings')
django.setup()

from apps.services.models import StaticProduct, ServiceCategory, ProductFormField

def get_group_defaults(group_or_product_name, category_name):
    # Normalize name for matching
    key = group_or_product_name.lower().strip() if group_or_product_name else ""
    
    defaults = {
        "available_papers": [],
        "available_finishes": [],
        "quantity_tiers": [],
        "specifications": {}
    }

    # === STATIONERY ===
    if "business card" in key:
        defaults["available_papers"] = [
            {'name': 'Standard Cardstock (300 GSM)', 'price_modifier': 0},
            {'name': 'Premium Matte (350 GSM)', 'price_modifier': 50},
            {'name': 'Textured Paper', 'price_modifier': 100},
            {'name': 'Non-Tearable', 'price_modifier': 150},
        ]
        defaults["available_finishes"] = [
            {'name': 'Matte Lamination', 'price_modifier': 20},
            {'name': 'Gloss Lamination', 'price_modifier': 20},
            {'name': 'Velvet Lamination', 'price_modifier': 50},
            {'name': 'Gold Foil (Front)', 'price_modifier': 200},
        ]
        defaults["quantity_tiers"] = [
            {'min_qty': 100, 'max_qty': 499, 'discount_percent': 0},
            {'min_qty': 500, 'max_qty': 999, 'discount_percent': 10},
            {'min_qty': 1000, 'max_qty': 5000, 'discount_percent': 20},
        ]
        defaults["specifications"] = {"Size": "3.5 x 2 inches", "Print": "Front & Back Full Color"}

    elif "letter head" in key:
        defaults["available_papers"] = [
            {'name': '100 GSM Alabaster', 'price_modifier': 0},
            {'name': '120 GSM Royal Bond', 'price_modifier': 40},
            {'name': '100 GSM Sunshine', 'price_modifier': 20},
        ]
        defaults["quantity_tiers"] = [
            {'min_qty': 100, 'max_qty': 499, 'discount_percent': 0},
            {'min_qty': 500, 'max_qty': 999, 'discount_percent': 10},
        ]
        defaults["specifications"] = {"Size": "A4", "Print": "Single Side Color"}

    elif "envelopes" in key:
        defaults["available_papers"] = [
            {'name': '100 GSM Super Print', 'price_modifier': 0},
            {'name': '120 GSM Sunshine', 'price_modifier': 30},
        ]
        defaults["specifications"] = {"Adhesive": "Peel and Seal", "Window": "Optional"}

    elif "bill book" in key:
        defaults["specifications"] = {
            "Size": "A5", "Copies": "Duplicate (1+1) / Triplicate (1+2)", 
            "Binding": "Book Binding / Pad Binding"
        }

    elif "id cards" in key:
        defaults["specifications"] = {"Material": "PVC Plastic", "Thickness": "0.76mm", "Lanyard": "16mm Multicolor"}

    # === MARKETING MATERIAL ===
    elif "brochure" in key:
        defaults["available_papers"] = [
            {'name': '130 GSM Gloss Art', 'price_modifier': 0},
            {'name': '170 GSM Matte Art', 'price_modifier': 30},
        ]
        defaults["available_finishes"] = [{'name': 'Center Pinning', 'price_modifier': 0}]
        defaults["specifications"] = {"Fold": "Bi-Fold / Tri-Fold", "Size": "A4 Open"}

    elif "poster" in key:
        defaults["available_papers"] = [
            {'name': '170 GSM Art Paper', 'price_modifier': 0},
            {'name': '300 GSM Art Card', 'price_modifier': 50},
        ]
        defaults["available_finishes"] = [{'name': 'Lamination', 'price_modifier': 20}, {'name': 'Tape Mounting', 'price_modifier': 10}]
        defaults["specifications"] = {"Print": "High Resolution Digital", "Usage": "Indoor/Outdoor"}

    elif "flyer" in key or "leaflet" in key:
        defaults["available_papers"] = [
            {'name': '90 GSM Art Paper', 'price_modifier': 0},
            {'name': '130 GSM Gloss', 'price_modifier': 20},
        ]
        defaults["specifications"] = {"Size": "A5 / A4", "Print": "Both Side Color"}

    elif "sticker" in key or "label" in key:
        defaults["available_papers"] = [
            {'name': 'Chromolabel (Paper)', 'price_modifier': 0},
            {'name': 'Transparent PVC', 'price_modifier': 50},
            {'name': 'White Vinyl', 'price_modifier': 60},
        ]
        defaults["available_finishes"] = [{'name': 'Kiss Cut', 'price_modifier': 10}, {'name': 'Die Cut', 'price_modifier': 20}]
        defaults["specifications"] = {"Adhesive": "Strong", "Form": "Sheet / Roll"}

    elif "dangler" in key:
        defaults["available_papers"] = [{'name': '300 GSM Card', 'price_modifier': 0}, {'name': 'Sunboard', 'price_modifier': 150}]

    elif "standee" in key:
        defaults["specifications"] = {"Size": "6x3 Feet / 5x2.5 Feet", "Stand": "Aluminum Roll-up"}

    # === PAPER BOXES ===
    elif "paper box" in key or "carton" in key:
        defaults["available_papers"] = [
            {'name': '350 GSM Duplex', 'price_modifier': 0},
            {'name': 'Virgin SBS', 'price_modifier': 50},
            {'name': 'Kraft Board', 'price_modifier': 20},
        ]
        defaults["available_finishes"] = [{'name': 'Drip Off', 'price_modifier': 100}, {'name': 'Foiling', 'price_modifier': 200}]
        defaults["quantity_tiers"] = [
             {'min_qty': 1000, 'max_qty': 4999, 'discount_percent': 0}, 
             {'min_qty': 5000, 'max_qty': 10000, 'discount_percent': 10}
        ]
        defaults["specifications"] = {"Style": "Reverse Tuck End / Crash Lock Bottom"}
        
    elif "hang tag" in key:
        defaults["available_papers"] = [{'name': '350 GSM Matte', 'price_modifier': 0}]
        defaults["available_finishes"] = [{'name': 'Punching', 'price_modifier': 0}, {'name': 'String', 'price_modifier': 10}]

    elif "paper bag" in key:
        defaults["available_papers"] = [{'name': 'Kraft Paper', 'price_modifier': 0}, {'name': 'Art Paper', 'price_modifier': 50}]
        defaults["specifications"] = {"Handle": "Rope / Twisted Paper", "Gusset": "Yes"}

    # === FALLBACK ===
    else:
        # Fallback to generic defaults if no match
        defaults["quantity_tiers"] = [{'min_qty': 100, 'max_qty': 1000, 'discount_percent': 10}]
        defaults["specifications"] = {"Note": "Standard Specification"}

    return defaults

def create_dynamic_fields(product, defaults):
    """Create ProductFormField objects from defaults"""
    # Clear existing fields to avoid duplication during re-runs
    ProductFormField.objects.filter(static_product=product).delete()
    print(f"Creating dynamic fields for {product.name}...")

    # 1. Paper Type Field
    if defaults['available_papers']:
        paper_options = []
        for p in defaults['available_papers']:
            paper_options.append({
                "value": p['name'], 
                "label": p['name'], 
                "price_modifier": p['price_modifier']
            })
        
        ProductFormField.objects.create(
            static_product=product,
            field_name='paper', # Changed from paper_type to match api expectations (maybe generic 'paper')
            field_label='Paper Type',
            field_type='select',
            field_section='product_specs',
            order=1,
            is_required=True,
            is_price_affecting=True,
            options=json.dumps(paper_options)
        )
        print(f" - Added 'Paper Type' field with {len(paper_options)} options")

    # 2. Finish Field
    if defaults['available_finishes']:
        finish_options = []
        for f in defaults['available_finishes']:
            finish_options.append({
                "value": f['name'], 
                "label": f['name'], 
                "price_modifier": f['price_modifier']
            })
            
        ProductFormField.objects.create(
            static_product=product,
            field_name='finish',
            field_label='Finishing',
            field_type='select', # or radio
            field_section='finishing_options',
            order=2,
            is_required=False,
            is_price_affecting=True,
            options=json.dumps(finish_options)
        )
        print(f" - Added 'Finishing' field with {len(finish_options)} options")

    # 3. Quantity Field (Simple Input for now, to enable calc)
    # The API reads 'quantity' from request params. The form needs an input named 'quantity'.
    ProductFormField.objects.create(
        static_product=product,
        field_name='quantity',
        field_label='Quantity',
        field_type='number',
        field_section='quantity_pricing',
        order=10,
        is_required=True,
        default_value='100',
        min_value=1,
        help_text="Enter required quantity"
    )
    print(" - Added 'Quantity' field")

def update_category(category_name, structure):
    print(f"\nUpdating {category_name} Groups...")
    try:
        category = ServiceCategory.objects.get(name=category_name)
        valid_products = set()

        for product_name, group_name, order in structure:
            try:
                # Determine relevant name for defaults
                main_service_name = group_name if group_name else product_name
                defaults = get_group_defaults(main_service_name, category_name)

                # Try to find by name first
                product = StaticProduct.objects.filter(
                    category=category, 
                    name__iexact=product_name
                ).first()
                
                if not product:
                    # Check if slug exists
                    base_slug = slugify(product_name)
                    slug = base_slug
                    counter = 1
                    while StaticProduct.objects.filter(slug=slug).exists():
                        slug = f"{base_slug}-{counter}"
                        counter += 1

                    product = StaticProduct.objects.create(
                        category=category,
                        name=product_name,
                        slug=slug,
                        description=f"High quality {product_name}",
                        short_description=f"Professional {product_name}",
                        base_price=100.00,
                        is_active=True
                    )
                    print(f"Created: {product_name}")
                
                # Update fields
                product.name = product_name
                product.group_name = group_name if group_name else ""
                product.group_order = order
                
                # Update JSON fields (legacy support / API calc)
                product.available_papers = defaults["available_papers"]
                product.available_finishes = defaults["available_finishes"]
                product.quantity_tiers = defaults["quantity_tiers"]
                product.specifications = defaults["specifications"]
                
                product.save()
                
                # CREATE Dynamic Form Fields
                create_dynamic_fields(product, defaults)
                
                valid_products.add(product.id)
                
                group_msg = f"group '{group_name}'" if group_name else "standalone"
                print(f"Assigned '{product.name}' to {group_msg}")
                
            except Exception as e:
                print(f"Error processing {product_name}: {e}")
                # Print full trace for debug
                import traceback
                traceback.print_exc()

        # Delete products not in the list
        products_to_delete = StaticProduct.objects.filter(category=category).exclude(id__in=valid_products)
        count = products_to_delete.count()
        if count > 0:
            print(f"Deleting {count} old products from {category_name}...")
            for p in products_to_delete:
                print(f"Deleting: {p.name}")
            products_to_delete.delete()
        else:
            print(f"No old products to delete in {category_name}.")

    except ServiceCategory.DoesNotExist:
        print(f"Category '{category_name}' not found")

def run():
    # Stationery Structure
    stationery_structure = [
        ("Standard Business Card", "Business Card", 1),
        ("TEXTURE BUSINESS CARD", "Business Card", 1),
        ("Standard Letter Head", "Letter Head", 2),
        ("Corporate Letter Head", "Letter Head", 2),
        ("Envelopes 10x 4.5", "Envelopes", 3),
        ("Envelopes A-5", "Envelopes", 3),
        ("Envelopes A-6", "Envelopes", 3),
        ("Envelopes A-4", "Envelopes", 3),
        ("Envelopes A-3", "Envelopes", 3),
        ("Black & White Bill Book", "Bill Book", 4),
        ("Colour Bill Book", "Bill Book", 4),
        ("Event ID Cards", "ID Cards", 5),
        ("PVC ID Cards", "ID Cards", 5),
        ("Multicolour Lanyards", "ID Cards", 5),
        ("Document Printing", None, 6),
    ]

    # Marketing Material Structure
    marketing_structure = [
        ("Bi-fold Brochure", "Brochures", 1),
        ("Tri-fold Brochure", "Brochures", 1),
        ("Certificates", None, 2),
        ("Size A-4", "Poster", 3),
        ("Size A-3", "Poster", 3),
        ("Custom Size", "Poster", 3),
        ("Black & White", "Flyers & Leaflets", 4),
        ("Colour", "Flyers & Leaflets", 4),
        ("Normal Shape", "Dangler", 5),
        ("Classic Shape", "Dangler", 5),
        ("Round Shape", "Dangler", 5),
        ("Custom/Any Other Shape", "Dangler", 5),
        ("Premium Flex", "Standees", 6),
        ("Banner Media", "Standees", 6),
        ("Button Badges", None, 7),
        ("Tent Card", None, 8),
    ]

    # Paper Boxes Structure
    paper_boxes_structure = [
        ("Custom Paper Boxes", None, 1),
        ("Kraft Paper Product Box", None, 2),
        ("Hang Tags", None, 3),
        ("Address Labels", "Sticker/Labels", 4),
        ("Barcode Labels", "Sticker/Labels", 4),
        ("Circle Stickers", "Sticker/Labels", 4),
        ("Custom Stickers", "Sticker/Labels", 4),
        ("Product Labels", "Sticker/Labels", 4),
        ("Rectangle Stickers", "Sticker/Labels", 4),
        ("Square Stickers", "Sticker/Labels", 4),
        ("Warning Labels", "Sticker/Labels", 4),
        ("Paper Bag", None, 5),
    ]

    update_category("Stationery", stationery_structure)
    update_category("Marketing Material", marketing_structure)
    update_category("Paper Boxes", paper_boxes_structure)

if __name__ == "__main__":
    run()
