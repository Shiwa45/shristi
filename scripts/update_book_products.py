import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shirsti_printing.settings')
django.setup()

from apps.services.models import StaticProduct, ServiceCategory

def run():
    try:
        category = ServiceCategory.objects.get(name="Book Printing")
    except ServiceCategory.DoesNotExist:
        print("Category 'Book Printing' not found.")
        return

    # Target list of products to keep/create
    target_products = [
        "Children's Book Printing",
        "Comic Book Printing",
        "Coffee Table Book Printing",
        "Coloring Book Printing",
        "Art Book Printing",
        "Annual Reports Printing",
        "Year Book Printing",
        "on Demand Books Printing"
    ]

    # Mapping of old names to new names (best guess based on similarity)
    rename_map = {
        "Children's Books": "Children's Book Printing",
        "Comic Books": "Comic Book Printing",
        "Coffee Table Books": "Coffee Table Book Printing",
        "Coloring Books": "Coloring Book Printing",
        "Art Books": "Art Book Printing",
        "Annual Reports": "Annual Reports Printing",
        "Yearbooks": "Year Book Printing",
        "On-Demand Books": "on Demand Books Printing",
    }

    print("Updating products...")

    # 1. Rename existing products
    for old_name, new_name in rename_map.items():
        try:
            product = StaticProduct.objects.get(category=category, name=old_name)
            product.name = new_name
            product.slug = None # Trigger slug regeneration
            product.save()
            print(f"Renamed: '{old_name}' -> '{new_name}'")
        except StaticProduct.DoesNotExist:
            pass

    # 2. Create missing products
    for name in target_products:
        obj, created = StaticProduct.objects.get_or_create(
            category=category,
            name=name,
            defaults={
                "description": f"High quality {name}",
                "short_description": f"Professional {name} services",
                "base_price": 100.00,
                "is_active": True
            }
        )
        if created:
            print(f"Created: '{name}'")

    # 3. Delete products not in the target list
    products_to_delete = StaticProduct.objects.filter(category=category).exclude(name__in=target_products)
    for product in products_to_delete:
        print(f"Deleting: '{product.name}'")
        product.delete()

    print("\nFinal Product List:")
    for p in StaticProduct.objects.filter(category=category).order_by('name'):
        print(f"- {p.name}")

if __name__ == "__main__":
    run()
