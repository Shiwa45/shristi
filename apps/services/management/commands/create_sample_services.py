from django.core.management.base import BaseCommand
from apps.services.models import ServiceCategory, Product

class Command(BaseCommand):
    help = 'Create sample service categories and products for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample service categories and products...')
        
        # Create Book Printing category
        book_printing, created = ServiceCategory.objects.get_or_create(
            slug='book-printing',
            defaults={
                'name': 'Book Printing',
                'description': 'Professional book printing services',
                'is_active': True,
                'is_featured': True,
                'order': 1
            }
        )
        
        # Create Paper Boxes category
        paper_boxes, created = ServiceCategory.objects.get_or_create(
            slug='paper-boxes',
            defaults={
                'name': 'Paper Boxes',
                'description': 'Custom paper box solutions',
                'is_active': True,
                'is_featured': False,
                'order': 2
            }
        )
        
        # Create Marketing Materials category
        marketing, created = ServiceCategory.objects.get_or_create(
            slug='marketing-materials',
            defaults={
                'name': 'Marketing Materials',
                'description': 'Professional marketing materials',
                'is_active': True,
                'is_featured': True,
                'order': 3
            }
        )
        
        # Create Stationery category
        stationery, created = ServiceCategory.objects.get_or_create(
            slug='stationery',
            defaults={
                'name': 'Stationery',
                'description': 'Custom stationery products',
                'is_active': True,
                'is_featured': False,
                'order': 4
            }
        )
        
        # Create sample products for Book Printing
        book_products = [
            ("Children's Book Printing", 'childrens-book-printing', True),
            ('Comic Book Printing', 'comic-book-printing', False),
            ('Coffee Table Books', 'coffee-table-books', False),
            ('Coloring Book Printing', 'coloring-book-printing', False),
        ]
        
        for name, slug, featured in book_products:
            Product.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'category': book_printing,
                    'description': f'Professional {name.lower()} services',
                    'width_mm': 210,
                    'height_mm': 297,
                    'is_active': True,
                    'is_featured': featured,
                    'price_per_unit': 50.00
                }
            )
        
        # Create sample products for Paper Boxes
        box_products = [
            ('Medical Paper Boxes', 'medical-paper-boxes', False),
            ('Cosmetic Paper Boxes', 'cosmetic-paper-boxes', False),
            ('Retail Paper Boxes', 'retail-paper-boxes', False),
            ('Folding Carton Boxes', 'folding-carton-boxes', False),
        ]
        
        for name, slug, featured in box_products:
            Product.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'category': paper_boxes,
                    'description': f'Professional {name.lower()} services',
                    'width_mm': 100,
                    'height_mm': 100,
                    'is_active': True,
                    'is_featured': featured,
                    'price_per_unit': 25.00
                }
            )
        
        # Create sample products for Marketing Materials
        marketing_products = [
            ('Brochures', 'brochures', True),
            ('Catalogue', 'catalogue', False),
            ('Poster', 'poster', False),
            ('Flyers', 'flyers', True),
        ]
        
        for name, slug, featured in marketing_products:
            Product.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'category': marketing,
                    'description': f'Professional {name.lower()} services',
                    'width_mm': 210,
                    'height_mm': 297,
                    'is_active': True,
                    'is_featured': featured,
                    'price_per_unit': 15.00
                }
            )
        
        # Create sample products for Stationery
        stationery_products = [
            ('Business Cards', 'business-cards', True),
            ('Letter Head', 'letter-head', True),
            ('Envelopes', 'envelopes', False),
            ('Bill Book', 'bill-book', True),
        ]
        
        for name, slug, featured in stationery_products:
            Product.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'category': stationery,
                    'description': f'Professional {name.lower()} services',
                    'width_mm': 85,
                    'height_mm': 55,
                    'is_active': True,
                    'is_featured': featured,
                    'price_per_unit': 10.00
                }
            )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample service categories and products')
        )