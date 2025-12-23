import os
import sys
import django
import json

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shirsti_printing.settings')
django.setup()

from apps.services.models import StaticProduct, ProductFormField

def check_product(name):
    print(f"\n--- Checking Product: {name} ---")
    product = StaticProduct.objects.filter(name__iexact=name).first()
    if not product:
        print("Product not found!")
        return
    
    fields = ProductFormField.objects.filter(static_product=product).order_by('order')
    if not fields.exists():
        print("No dynamic fields found.")
        return

    for f in fields:
        print(f"Field: {f.field_label} ({f.field_type})")
        if f.options:
            try:
                opts = json.loads(f.options)
                for o in opts:
                    print(f"  - {o['label']} (+{o.get('price_modifier', 0)})")
            except:
                print(f"  [Invalid JSON options]: {f.options}")

def run():
    # Check 3 distinct types to see if they are identical
    check_product("Size A-4")             # Should be Poster
    check_product("Size A-3")             # User specifically mentioned "s3 size"
    check_product("Custom Paper Boxes")   # Should be Paper Box
    check_product("Bi-fold Brochure")

if __name__ == "__main__":
    run()
