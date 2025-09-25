# scripts/cleanup_product_pricing.py
# Run with: python manage.py shell < scripts/cleanup_product_pricing.py

from apps.services.models import ProductPricing

# Only keep these paper types
KEEP_PAPER_TYPES = [
    "70gsm Maplitho",
    "100gsm Art Paper",
    "300gsm Art Card",
]

# Delete all ProductPricing entries with paper types not in the keep list
ProductPricing.objects.exclude(paper_type__in=KEEP_PAPER_TYPES).delete()
print("Cleaned up ProductPricing: only 3 paper types remain.")
