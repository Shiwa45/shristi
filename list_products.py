
import os
import django
import sys

sys.path.append('/home/shiwansh/shristi')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shirsti_printing.settings')
django.setup()

from apps.services.models import StaticProduct

products = StaticProduct.objects.all()[:5]
for p in products:
    print(f"Product: {p.name}")
    print(f"Category: {p.category.slug}")
    print(f"Slug: {p.slug}")
    print(f"URL: /services/{p.category.slug}/{p.slug}/") # Assuming this pattern based on templates
    print("-" * 20)
