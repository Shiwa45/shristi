from django.core.management.base import BaseCommand
from apps.services.models import ServiceCategory, Product

class Command(BaseCommand):
    help = 'Seed initial categories and products for printing business.'

    def handle(self, *args, **options):
        categories = [
            ("Book Printing", "book-printing"),
            ("Paper Boxes", "paper-boxes"),
            ("Marketing Material", "marketing-material"),
            ("Stationery", "stationery"),
        ]
        cat_objs = {}
        for name, slug in categories:
            cat, _ = ServiceCategory.objects.get_or_create(name=name, defaults={"slug": slug, "is_active": True})
            cat_objs[name] = cat
            self.stdout.write(self.style.SUCCESS(f'Category: {name}'))

        products = [
            ("Children's Book Printing", "Book Printing", False),
            ("Comic Book Printing", "Book Printing", False),
            ("Coffee Table Books", "Book Printing", False),
            ("Coloring Book Printing", "Book Printing", False),
            ("Art Book Printing", "Book Printing", False),
            ("Annual Reports", "Book Printing", False),
            ("Year Book Printing", "Book Printing", False),
            ("On Demand Books", "Book Printing", False),
            ("Paper Boxes", "Paper Boxes", False),
            ("Medical Paper Boxes", "Paper Boxes", False),
            ("Cosmetic Paper Boxes", "Paper Boxes", False),
            ("Retail Paper Boxes", "Paper Boxes", False),
            ("Folding Carton Boxes", "Paper Boxes", False),
            ("Corrugated Boxes", "Paper Boxes", False),
            ("Kraft Boxes", "Paper Boxes", False),
            ("Brochures", "Marketing Material", True),
            ("Catalogue", "Marketing Material", False),
            ("Poster", "Marketing Material", False),
            ("Flyers", "Marketing Material", True),
            ("Dangler", "Marketing Material", False),
            ("Standees", "Marketing Material", False),
            ("Pen Drives", "Marketing Material", False),
            ("Business Cards", "Stationery", True),
            ("Letter Head", "Stationery", True),
            ("Envelopes", "Stationery", False),
            ("Bill Book", "Stationery", True),
            ("ID Cards", "Stationery", False),
            ("Sticker", "Stationery", True),
            ("Document Printing", "Stationery", False),
        ]
        from apps.services.models import ProductPricing

        for name, cat, has_tool in products:
            prod, created = Product.objects.get_or_create(
                name=name,
                category=cat_objs[cat],
                defaults={
                    "has_design_tool": has_tool,
                    "is_active": True,
                    "is_featured": False,
                    "slug": name.lower().replace(" ", "-").replace("'", ""),
                    "width_mm": 100.0,
                    "height_mm": 150.0,
                    "bleed_mm": 3.0,
                    "safe_zone_mm": 5.0,
                    "dpi": 300,
                    "base_price": 10.0,
                    "price_per_unit": 1.0,
                    "minimum_quantity": 1
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Product: {name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Product already exists: {name}'))

            # Seed ProductPricing for Flash Cards demo
            if name.lower() == 'business cards':
                pricing_data = [
                    {"size": "A6", "paper_type": "Standard", "finish": "Matte", "min_quantity": 100, "price_per_unit": 2.0},
                    {"size": "A6", "paper_type": "Standard", "finish": "Glossy", "min_quantity": 100, "price_per_unit": 2.2},
                    {"size": "A6", "paper_type": "Premium", "finish": "Matte", "min_quantity": 100, "price_per_unit": 2.5},
                    {"size": "A6", "paper_type": "Premium", "finish": "Glossy", "min_quantity": 100, "price_per_unit": 2.7},
                    {"size": "A5", "paper_type": "Standard", "finish": "Matte", "min_quantity": 100, "price_per_unit": 3.0},
                    {"size": "A5", "paper_type": "Premium", "finish": "Glossy", "min_quantity": 100, "price_per_unit": 3.5},
                ]
                for pdata in pricing_data:
                    ProductPricing.objects.get_or_create(
                        product=prod,
                        size=pdata["size"],
                        paper_type=pdata["paper_type"],
                        finish=pdata["finish"],
                        min_quantity=pdata["min_quantity"],
                        defaults={"price_per_unit": pdata["price_per_unit"]}
                    )
        self.stdout.write(self.style.SUCCESS('Seeding complete.'))
