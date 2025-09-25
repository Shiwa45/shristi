
# scripts/reset_and_seed_services.py
# Run with: python manage.py shell -c "exec(open('scripts/reset_and_seed_services.py').read())"
"""
This script will:
1. Delete all Product, ProductPricing, and related data for the services app.
2. Seed new products and pricing as per the attached pricing sheet (book sizes, paper types, color/BW, shipping).
"""

from apps.services.models import ServiceCategory, Product, ProductPricing
from decimal import Decimal

# --- PURGE ---
print("Deleting all ProductPricing and Product data...")
ProductPricing.objects.all().delete()
Product.objects.all().delete()
ServiceCategory.objects.all().delete()
print("All old data deleted.")


# --- SEED CATEGORIES & PRODUCTS ---
category_name = "Book Printing"
cat, _ = ServiceCategory.objects.get_or_create(name=category_name, defaults={"slug": "book-printing", "is_active": True})

PRODUCT_SPECS = [
    ("A4 Book Printing", 210.0, 297.0, "A4"),
    ("Letter Book Printing", 216.0, 279.0, "Letter"),
    ("Executive Book Printing", 178.0, 254.0, "Executive"),
    ("A5 Book Printing", 148.0, 210.0, "A5"),
]

products = {}
for prod_name, width, height, size_code in PRODUCT_SPECS:
    prod, _ = Product.objects.get_or_create(
        name=prod_name,
        category=cat,
        defaults={
            "has_design_tool": True,
            "is_active": True,
            "is_featured": False,
            "slug": prod_name.lower().replace(" ", "-"),
            "width_mm": width,
            "height_mm": height,
            "bleed_mm": 3.0,
            "safe_zone_mm": 5.0,
            "dpi": 300,
            "description": f"{prod_name} service.",
            "short_description": f"{prod_name} service.",
            "base_price": 0.0,
            "price_per_unit": 0.0,
            "minimum_quantity": 1,
        }
    )
    products[size_code] = prod

# --- SEED PRICING (main rows from Excel) ---
PRICING_DATA = [
    # (size, paper_type, color_type, rate, shipping_per_page)
    ("A4", "75 gsm", "B/W Standard", 1.1, 0.1),
    ("A4", "75 gsm", "B/W Premium", 1.3, 0.13),
    ("A4", "75 gsm", "Color Standard", 2.5, 0.1),
    ("A4", "75 gsm", "Color Premium", 2.7, 0.13),
    ("A4", "100 gsm", "B/W Standard", 1.35, 0.13),
    ("A4", "100 gsm", "B/W Premium", 1.55, 0.13),
    ("A4", "100 gsm", "Color Standard", 2.7, 0.13),
    ("A4", "100 gsm", "Color Premium", 2.9, 0.13),
    ("A4", "100 gsm Art Paper", "B/W Standard", 1.8, 0.13),
    ("A4", "100 gsm Art Paper", "B/W Premium", 2.0, 0.13),
    ("A4", "100 gsm Art Paper", "Color Standard", 2.9, 0.13),
    ("A4", "100 gsm Art Paper", "Color Premium", 3.1, 0.13),
    ("A4", "130 gsm Art Paper", "B/W Standard", 2.1, 0.17),
    ("A4", "130 gsm Art Paper", "B/W Premium", 2.3, 0.17),
    ("A4", "130 gsm Art Paper", "Color Standard", 3.15, 0.17),
    ("A4", "130 gsm Art Paper", "Color Premium", 3.3, 0.17),
    # Letter
    ("Letter", "75 gsm", "B/W Standard", 1.1, 0.1),
    ("Letter", "75 gsm", "B/W Premium", 1.3, 0.13),
    ("Letter", "75 gsm", "Color Standard", 2.5, 0.1),
    ("Letter", "75 gsm", "Color Premium", 2.7, 0.13),
    ("Letter", "100 gsm", "B/W Standard", 1.35, 0.13),
    ("Letter", "100 gsm", "B/W Premium", 1.55, 0.13),
    ("Letter", "100 gsm", "Color Standard", 2.7, 0.13),
    ("Letter", "100 gsm", "Color Premium", 2.9, 0.13),
    ("Letter", "100 gsm Art Paper", "B/W Standard", 1.8, 0.13),
    ("Letter", "100 gsm Art Paper", "B/W Premium", 2.0, 0.13),
    ("Letter", "100 gsm Art Paper", "Color Standard", 2.9, 0.13),
    ("Letter", "100 gsm Art Paper", "Color Premium", 3.1, 0.13),
    ("Letter", "130 gsm Art Paper", "B/W Standard", 2.1, 0.17),
    ("Letter", "130 gsm Art Paper", "B/W Premium", 2.3, 0.17),
    ("Letter", "130 gsm Art Paper", "Color Standard", 3.15, 0.17),
    ("Letter", "130 gsm Art Paper", "Color Premium", 3.3, 0.17),
    # Executive
    ("Executive", "75 gsm", "B/W Standard", 1.1, 0.1),
    ("Executive", "75 gsm", "B/W Premium", 1.3, 0.13),
    ("Executive", "75 gsm", "Color Standard", 2.5, 0.1),
    ("Executive", "75 gsm", "Color Premium", 2.7, 0.13),
    ("Executive", "100 gsm", "B/W Standard", 1.35, 0.13),
    ("Executive", "100 gsm", "B/W Premium", 1.55, 0.13),
    ("Executive", "100 gsm", "Color Standard", 2.7, 0.13),
    ("Executive", "100 gsm", "Color Premium", 2.9, 0.13),
    ("Executive", "100 gsm Art Paper", "B/W Standard", 1.8, 0.13),
    ("Executive", "100 gsm Art Paper", "B/W Premium", 2.0, 0.13),
    ("Executive", "100 gsm Art Paper", "Color Standard", 2.9, 0.13),
    ("Executive", "100 gsm Art Paper", "Color Premium", 3.1, 0.13),
    ("Executive", "130 gsm Art Paper", "B/W Standard", 2.1, 0.17),
    ("Executive", "130 gsm Art Paper", "B/W Premium", 2.3, 0.17),
    ("Executive", "130 gsm Art Paper", "Color Standard", 3.15, 0.17),
    ("Executive", "130 gsm Art Paper", "Color Premium", 3.3, 0.17),
    # A5
    ("A5", "75 gsm", "B/W Standard", 0.6, 0.05),
    ("A5", "75 gsm", "B/W Premium", 0.75, 0.07),
    ("A5", "75 gsm", "Color Standard", 1.25, 0.05),
    ("A5", "75 gsm", "Color Premium", 1.35, 0.07),
    ("A5", "100 gsm", "B/W Standard", 0.75, 0.07),
    ("A5", "100 gsm", "B/W Premium", 0.9, 0.07),
    ("A5", "100 gsm", "Color Standard", 1.35, 0.07),
    ("A5", "100 gsm", "Color Premium", 1.45, 0.07),
    ("A5", "100 gsm Art Paper", "B/W Standard", 0.9, 0.07),
    ("A5", "100 gsm Art Paper", "B/W Premium", 1.1, 0.07),
    ("A5", "100 gsm Art Paper", "Color Standard", 1.45, 0.07),
    ("A5", "100 gsm Art Paper", "Color Premium", 1.6, 0.07),
    ("A5", "130 gsm Art Paper", "B/W Standard", 1.1, 0.09),
    ("A5", "130 gsm Art Paper", "B/W Premium", 1.25, 0.09),
    ("A5", "130 gsm Art Paper", "Color Standard", 1.58, 0.09),
    ("A5", "130 gsm Art Paper", "Color Premium", 1.75, 0.09),
]

for size, paper, color, rate, shipping in PRICING_DATA:
    prod = products.get(size)
    if prod:
        # Use 'Standard' for empty fields to avoid overlap with special rows
        ProductPricing.objects.create(
            product=prod,
            size=size,
            paper_type=paper or "Standard",
            colors=color or "Standard",
            price_per_unit=Decimal(str(rate)),
            setup_cost=Decimal("0.00"),
            min_quantity=1,
            page_count=1,
            binding_type="Standard",
            finish="Standard",
            delivery_speed="Standard",
            notes=f"Shipping per page: {shipping}",
            is_active=True,
        )

# --- SEED BINDING OPTIONS FOR EACH PRODUCT ---
BINDINGS = [
    ("A4", "Paperback (Perfect)", 40, 32, 800),
    ("A4", "Spiral Binding", 40, 20, 470),
    ("A4", "Hardcover", 150, 32, 800),
    ("A4", "Saddle Stitch", 25, 8, 48),
    ("A4", "Wire-O Bound", 150, 32, 300),
    ("Letter", "Paperback (Perfect)", 40, 32, 800),
    ("Letter", "Spiral Binding", 40, 20, 470),
    ("Letter", "Hardcover", 150, 32, 800),
    ("Letter", "Saddle Stitch", 25, 8, 48),
    ("Letter", "Wire-O Bound", 150, 32, 300),
    ("Executive", "Paperback (Perfect)", 40, 32, 800),
    ("Executive", "Spiral Binding", 40, 20, 470),
    ("Executive", "Hardcover", 150, 32, 800),
    ("Executive", "Saddle Stitch", 25, 8, 48),
    ("Executive", "Wire-O Bound", 150, 32, 300),
    ("A5", "Paperback (Perfect)", 30, 32, 800),
    ("A5", "Spiral Binding", 30, 20, 470),
    ("A5", "Hardcover", 80, 32, 800),
    ("A5", "Saddle Stitch", 20, 8, 48),
    ("A5", "Wire-O Bound", 80, 32, 300),
]
for size, binding, rate, min_pages, max_pages in BINDINGS:
    prod = products.get(size)
    if prod:
        ProductPricing.objects.create(
            product=prod,
            size=size,
            binding_type=binding,
            price_per_unit=Decimal(str(rate)),
            min_quantity=1,
            page_count=min_pages,
            max_quantity=max_pages,
            colors="Binding Option",
            paper_type="Binding Option",
            finish=binding,
            delivery_speed="Standard",
            notes=f"Binding for {size}: {min_pages} to {max_pages} pages",
            is_active=True,
        )

# --- SEED DESIGN & FORMATTING SUPPORT FOR EACH PRODUCT ---
DESIGN_SUPPORT = [
    ("A4", 50),
    ("Letter", 50),
    ("Executive", 50),
    ("A5", 40),
]
for size, rate in DESIGN_SUPPORT:
    prod = products.get(size)
    if prod:
        ProductPricing.objects.create(
            product=prod,
            size=size,
            design_service=True,
            price_per_unit=Decimal(str(rate)),
            min_quantity=1,
            page_count=1,
            colors="Design Support",
            paper_type="Design Support",
            binding_type="Design Support",
            finish="Design Support",
            delivery_speed="Standard",
            notes="Designing and Formatting Support",
            is_active=True,
        )

# --- SEED COVER PAGE DESIGN & ISBN FOR EACH PRODUCT ---
for size, prod in products.items():
    ProductPricing.objects.create(
        product=prod,
        size="All",
        design_service=True,
        price_per_unit=Decimal("1500"),
        min_quantity=1,
        page_count=1,
        colors="Cover Page Design",
        paper_type="Cover Page Design",
        binding_type="Cover Page Design",
        finish="Cover Page Design",
        delivery_speed="Standard",
        notes="Cover page design price (one time for all book)",
        is_active=True,
    )
    ProductPricing.objects.create(
        product=prod,
        size="All",
        isbn_allocation=True,
        price_per_unit=Decimal("1500"),
        min_quantity=1,
        page_count=1,
        colors="ISBN Allocation",
        paper_type="ISBN Allocation",
        binding_type="ISBN Allocation",
        finish="ISBN Allocation",
        delivery_speed="Standard",
        notes="ISBN allocation (one time for all book)",
        is_active=True,
    )

# --- SEED BULK DISCOUNTS FOR EACH PRODUCT ---
BULK_DISCOUNTS = [
    (25, 0),
    (50, 2),
    (75, 4),
    (100, 6),
    (150, 8),
    (200, 10),
    (250, 12),
    (300, 14),
]
for size, prod in products.items():
    for qty, discount in BULK_DISCOUNTS:
        ProductPricing.objects.create(
            product=prod,
            size="All",
            min_quantity=qty,
            price_per_unit=Decimal("0.00"),
            volume_discount_percentage=Decimal(str(discount)),
            page_count=1,
            colors=f"Bulk Discount {qty}",
            paper_type=f"Bulk Discount {qty}",
            binding_type=f"Bulk Discount {qty}",
            finish=f"Bulk Discount {qty}",
            delivery_speed="Standard",
            notes=f"Bulk discount for {qty} books: {discount}%",
            is_active=True,
        )

print("Seeded main pricing rows as per the Excel sheet.")

# --- SEED BINDING OPTIONS ---
BINDINGS = [
    ("A4", "Paperback (Perfect)", 40, 32, 800),
    ("A4", "Spiral Binding", 40, 20, 470),
    ("A4", "Hardcover", 150, 32, 800),
    ("A4", "Saddle Stitch", 25, 8, 48),
    ("A4", "Wire-O Bound", 150, 32, 300),
    ("Letter", "Paperback (Perfect)", 40, 32, 800),
    ("Letter", "Spiral Binding", 40, 20, 470),
    ("Letter", "Hardcover", 150, 32, 800),
    ("Letter", "Saddle Stitch", 25, 8, 48),
    ("Letter", "Wire-O Bound", 150, 32, 300),
    ("Executive", "Paperback (Perfect)", 40, 32, 800),
    ("Executive", "Spiral Binding", 40, 20, 470),
    ("Executive", "Hardcover", 150, 32, 800),
    ("Executive", "Saddle Stitch", 25, 8, 48),
    ("Executive", "Wire-O Bound", 150, 32, 300),
    ("A5", "Paperback (Perfect)", 30, 32, 800),
    ("A5", "Spiral Binding", 30, 20, 470),
    ("A5", "Hardcover", 80, 32, 800),
    ("A5", "Saddle Stitch", 20, 8, 48),
    ("A5", "Wire-O Bound", 80, 32, 300),
]
for size, binding, rate, min_pages, max_pages in BINDINGS:
    ProductPricing.objects.create(
        product=prod,
        size=size,
        binding_type=binding,
        price_per_unit=Decimal(str(rate)),
        min_quantity=1,
        page_count=min_pages,
        max_quantity=max_pages,
        colors="",
        paper_type="",
        finish="",
        delivery_speed="Standard",
        notes=f"Binding for {size}: {min_pages} to {max_pages} pages",
        is_active=True,
    )

# --- SEED DESIGN & FORMATTING SUPPORT ---
DESIGN_SUPPORT = [
    ("A4", 50),
    ("Letter", 50),
    ("Executive", 50),
    ("A5", 40),
]
for size, rate in DESIGN_SUPPORT:
    ProductPricing.objects.create(
        product=prod,
        size=size,
        design_service=True,
        price_per_unit=Decimal(str(rate)),
        min_quantity=1,
        page_count=1,
        colors="",
        paper_type="",
        binding_type="",
        finish="",
        delivery_speed="Standard",
        notes="Designing and Formatting Support",
        is_active=True,
    )

# --- SEED COVER PAGE DESIGN & ISBN ---
ProductPricing.objects.create(
    product=prod,
    size="All",
    design_service=True,
    price_per_unit=Decimal("1500"),
    min_quantity=1,
    page_count=1,
    colors="",
    paper_type="",
    binding_type="Cover Page Design",
    finish="",
    delivery_speed="Standard",
    notes="Cover page design price (one time for all book)",
    is_active=True,
)
ProductPricing.objects.create(
    product=prod,
    size="All",
    isbn_allocation=True,
    price_per_unit=Decimal("1500"),
    min_quantity=1,
    page_count=1,
    colors="",
    paper_type="",
    binding_type="ISBN Allocation",
    finish="",
    delivery_speed="Standard",
    notes="ISBN allocation (one time for all book)",
    is_active=True,
)

# --- SEED BULK DISCOUNTS ---
BULK_DISCOUNTS = [
    (25, 0),
    (50, 2),
    (75, 4),
    (100, 6),
    (150, 8),
    (200, 10),
    (250, 12),
    (300, 14),
]
for qty, discount in BULK_DISCOUNTS:
    ProductPricing.objects.create(
        product=prod,
        size="All",
        min_quantity=qty,
        price_per_unit=Decimal("0.00"),
        volume_discount_percentage=Decimal(str(discount)),
        page_count=1,
        colors="",
        paper_type="",
        binding_type="",
        finish="",
        delivery_speed="Standard",
        notes=f"Bulk discount for {qty} books: {discount}%",
        is_active=True,
    )

print("Seeded all bindings, design, cover, ISBN, and bulk discounts as per the Excel sheet.")
