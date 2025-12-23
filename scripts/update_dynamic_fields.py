import os
import sys
import json
import django
from django.utils.text import slugify

# Add valid project path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shirsti_printing.settings")
django.setup()

from apps.services.models import StaticProduct, ProductFormField, ServiceCategory

# Path to the JSON file
# Checking both scrapper dir (source) and project root (user claim)
JSON_PATHS = [
    os.path.join(project_root, "kraftix_products.json"),
    "/home/shiwansh/scrapper/kraftix_products.json"
]

ALLOWED_CATEGORIES_SLUGS = ['marketing-material', 'paper-boxes', 'stationery']
SKIP_CATEGORIES_SLUGS = ['book-printing']

# Strict whitelist based on user feedback to avoid "Custom Size" etc as products
VALID_PRODUCT_NAMES = [
    'Address Labels', 'Banner Media', 'Barcode Labels', 'Bi-fold Brochure', 
    'Black & White Bill Book', 'Button Badges', 'Certificates', 'Circle Stickers', 
    'Colour Bill Book', 'Corporate Letter Head', 'Custom Paper Boxes', 
    'Custom Stickers', 'Document Printing', 'Envelopes 10x 4.5', 
    'Envelopes A-3', 'Envelopes A-4', 'Envelopes A-5', 'Envelopes A-6', 'Event ID Cards', 'Hang Tags', 
    'Kraft Paper Product Box', 'Multicolour Lanyards', 'PVC ID Cards', 'Paper Bag', 
    'Premium Flex', 'Product Labels', 'Rectangle Stickers', 
    'Square Stickers', 'Standard Business Card', 'Standard Letter Head', 'TEXTURE BUSINESS CARD', 
    'Tent Card', 'Tri-fold Brochure', 'Warning Labels'
]

def get_json_data():
    for path in JSON_PATHS:
        if os.path.exists(path):
            print(f"Loading data from: {path}")
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    print("Error: kraftix_products.json not found in expected locations.")
    return None

def update_fields():
    data = get_json_data()
    if not data:
        return

    updated_count = 0
    skipped_count = 0
    not_found_count = 0

    print("Starting update process...")

    # 1. Clean up ALL products in target categories that are NOT in the whitelist
    # This ensures "Black & White" etc are wiped even if not in JSON
    print("\n--- Cleaning Non-Whitelisted Products ---")
    candidates = StaticProduct.objects.filter(category__slug__in=ALLOWED_CATEGORIES_SLUGS).exclude(category__slug__in=SKIP_CATEGORIES_SLUGS)
    for prod in candidates:
        is_valid = False
        for valid_name in VALID_PRODUCT_NAMES:
            if prod.name.lower() == valid_name.lower():
                is_valid = True
                break
        
        if not is_valid:
            print(f"Cleaning invalid product: {prod.name}")
            ProductFormField.objects.filter(static_product=prod).delete()
            skipped_count += 1

    print("\n--- Updating Valid Products from JSON ---")
    for entry in data:
        raw_name = entry.get('title')
        fields = entry.get('fields', [])
        
        if not raw_name:
            continue

        # Find product
        products = StaticProduct.objects.filter(name__iexact=raw_name)
        if not products.exists():
             # Fuzzy match logic
             all_candidates = StaticProduct.objects.exclude(category__slug='book-printing')
             matched_product = None
             for cand in sorted(all_candidates, key=lambda p: len(p.name), reverse=True):
                 if cand.name.lower() in raw_name.lower() or raw_name.lower() in cand.name.lower():
                     matched_product = cand
                     break
            
             if matched_product:
                 products = [matched_product]

        if not products:
            print(f"Product not found in DB: {raw_name}")
            not_found_count += 1
            continue

        for product in products:
            # Check category
            cat_slug = product.category.slug
            if cat_slug in SKIP_CATEGORIES_SLUGS or cat_slug not in ALLOWED_CATEGORIES_SLUGS:
                print(f"Skipping product '{product.name}' in category '{cat_slug}'")
                skipped_count += 1
                continue
            
            # Extra Safety: Check against whitelist
            # Use fuzzy check again: is the found product name roughly in our valid list?
            is_valid = False
            for valid_name in VALID_PRODUCT_NAMES:
                if product.name.lower() == valid_name.lower():
                    is_valid = True
                    break
            
            if not is_valid:
                 print(f"Skipping '{product.name}' - Not in valid allow-list. WIPING FIELDS.")
                 skipped_count += 1
                 # CRITICAL FIX: Delete fields if product is not in valid list
                 # This cleans up products like "Black & White" or "Custom Size" that got fields by mistake
                 ProductFormField.objects.filter(static_product=product).delete()
                 continue

            print(f"Updating fields for: {product.name} ({cat_slug})")
            # Clean up existing fields to prevent duplicates/orphans from bad scrapes
            print(f"  - Cleaning old fields for {product.name}...")
            ProductFormField.objects.filter(static_product=product).delete()
            
            for i, field_data in enumerate(fields):
                label = field_data['name']
                options_list = field_data['options']
                
                # Sanitize Label/Name
                # "Size 1" -> "size-1"
                # "Unknown Dropdown" -> skip?
                if "unknown" in label.lower():
                    continue

                field_slug = slugify(label).replace('-', '_') # standard python snake_case preference for field names
                
                # Prepare Options JSON
                # Format: [{"value": "option1", "label": "Option 1", "price_modifier": 0, "description": ""}]
                formatted_options = []
                for opt in options_list:
                    opt_val = slugify(str(opt))
                    formatted_options.append({
                        "value": opt_val,
                        "label": str(opt).strip(),
                        "price_modifier": 0, # Default to 0 as we don't have scraped pricing logic per option yet
                        "description": ""
                    })

                # Update or Create Field
                # We use field_label as a key part of identity or field_name?
                # Using field_name (slug) as the unique identifier per product
                
                # Defaults
                defaults = {
                    "field_label": label,
                    "field_type": "select",
                    "field_section": "product_specs", # Default section
                    "is_required": True,
                    "order": i * 10,
                    "options": json.dumps(formatted_options),
                    "is_active": True
                }

                obj, created = ProductFormField.objects.update_or_create(
                    static_product=product,
                    field_name=field_slug,
                    defaults=defaults
                )
                
                action = "Created" if created else "Updated"
                # print(f"  - {action} field: {label} ({len(formatted_options)} options)")
            
            updated_count += 1

    print("\n--- Summary ---")
    print(f"Products Updated: {updated_count}")
    print(f"Products Skipped (Category): {skipped_count}")
    print(f"Products Not Found: {not_found_count}")

if __name__ == "__main__":
    update_fields()
