# scripts/seed_product_pricing.py
# Run with: python manage.py shell < scripts/seed_product_pricing.py

from apps.services.models import Product, ProductPricing
from decimal import Decimal

# Sample data for seeding
PAPER_TYPES = [
    "70gsm Maplitho",
    "80gsm Maplitho",
    "100gsm Art Paper",
    "130gsm Art Paper",
    "170gsm Art Paper",
    "300gsm Art Card",
]
SIZES = ["A4", "A5", "8.5 x 11", "Custom"]
COLORS = ["Black & White", "Full Color"]
FINISHES = ["Matte", "Glossy"]
BINDINGS = ["Perfect", "Spiral", "Saddle Stitched"]

for product in Product.objects.filter(is_active=True):
    for paper in PAPER_TYPES:
        for size in SIZES:
            for color in COLORS:
                for finish in FINISHES:
                    for binding in BINDINGS:
                        ProductPricing.objects.get_or_create(
                            product=product,
                            size=size,
                            paper_type=paper,
                            colors=color,
                            finish=finish,
                            binding_type=binding,
                            min_quantity=100,
                            defaults={
                                'page_count': 100,
                                'price_per_unit': Decimal('10.00'),
                                'setup_cost': Decimal('100.00'),
                                'volume_discount_percentage': Decimal('5.0'),
                                'turnaround_days': 5,
                                'is_active': True,
                            }
                        )
print("Sample ProductPricing data seeded!")
