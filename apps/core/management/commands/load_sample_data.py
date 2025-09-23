from django.core.management.base import BaseCommand
from apps.services.models import ServiceCategory, Product

class Command(BaseCommand):
    help = 'Load sample data for development'

    def handle(self, *args, **options):
        category, _ = ServiceCategory.objects.get_or_create(
            slug='business-cards',
            defaults={'name': 'Business Cards', 'icon': 'fas fa-id-card'}
        )
        Product.objects.get_or_create(
            slug='standard-business-card',
            defaults={
                'name': 'Standard Business Card',
                'category': category,
                'description': 'Professional business cards with custom design options',
                'base_price': 29.99,
                'has_design_tool': True,
                'is_featured': True,
            }
        )
        self.stdout.write(self.style.SUCCESS('Sample data loaded successfully'))
