# apps/services/management/commands/seed_enhanced_products.py

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.services.models import ServiceCategory, Product, ProductPricing, ProductSpecification
from decimal import Decimal

class Command(BaseCommand):
    help = 'Seed enhanced products with comprehensive pricing similar to QinPrinting'

    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write(self.style.SUCCESS('Starting enhanced product seeding...'))
            
            # Create service categories
            self.create_categories()
            
            # Create flash cards product with detailed pricing
            self.create_flash_cards()
            
            # Create business cards product
            self.create_business_cards()
            
            # Create brochures product
            self.create_brochures()
            
            self.stdout.write(self.style.SUCCESS('Enhanced seeding completed successfully!'))

    def create_categories(self):
        """Create service categories"""
        categories_data = [
            {
                'name': 'Educational Materials',
                'description': 'Flash cards, study guides, and educational printing services',
                'icon': 'fas fa-graduation-cap',
                'order': 1
            },
            {
                'name': 'Business Stationery',
                'description': 'Business cards, letterheads, and corporate materials',
                'icon': 'fas fa-briefcase',
                'order': 2
            },
            {
                'name': 'Marketing Materials',
                'description': 'Brochures, flyers, and promotional printing',
                'icon': 'fas fa-bullhorn',
                'order': 3
            }
        ]
        
        for cat_data in categories_data:
            category, created = ServiceCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')

    def create_flash_cards(self):
        """Create flash cards with QinPrinting-style pricing"""
        category = ServiceCategory.objects.get(name='Educational Materials')
        
        # Create the flash cards product
        product, created = Product.objects.get_or_create(
            name='Custom Flash Cards',
            category=category,
            defaults={
                'slug': 'custom-flash-cards',
                'description': '''Take your flash card experience to the next level with our custom flash card printing. We use premium card stock and advanced offset printing at affordable prices, ensuring every card truly shines. Our professional cutting process creates smooth, flawless edges in every set. With a minimum order quantity of just 200 sets, we easily accommodate short run and bulk flash card printing. Choose from single-sheet cardstock, mounted double-layer, or triple-layer options to achieve the perfect thickness and durability for your needs.''',
                'short_description': 'Professional custom flash card printing with premium materials and competitive pricing.',
                'width_mm': 89.0,
                'height_mm': 51.0,
                'bleed_mm': 3.0,
                'safe_zone_mm': 5.0,
                'dpi': 300,
                'has_design_tool': True,
                'allows_upload': True,
                'allows_custom_size': True,
                'base_price': Decimal('50.00'),
                'price_per_unit': Decimal('2.50'),
                'minimum_quantity': 200,
                'is_active': True,
                'is_featured': True
            }
        )
        
        if created:
            self.stdout.write(f'Created product: {product.name}')
            
            # Add specifications
            specs_data = [
                {'name': 'Material Options', 'value': '300gsm-400gsm Art Paper', 'order': 1, 'is_highlighted': True},
                {'name': 'Finish Options', 'value': 'Matte/Glossy Lamination', 'order': 2, 'is_highlighted': True},
                {'name': 'Standard Size', 'value': '89 x 51 mm (Credit Card Size)', 'order': 3},
                {'name': 'Custom Sizes', 'value': 'Available on Request', 'order': 4},
                {'name': 'Minimum Order', 'value': '200 Cards', 'order': 5},
                {'name': 'Turnaround', 'value': '5-7 Business Days', 'order': 6},
                {'name': 'Packaging', 'value': 'Custom Printed Box Available', 'order': 7}
            ]
            
            for spec_data in specs_data:
                ProductSpecification.objects.create(product=product, **spec_data)
            
            # Create comprehensive pricing similar to QinPrinting
            pricing_data = [
                # 300gsm Art Paper with Matte Lamination - Different quantities
                {'size': 'Standard (89x51mm)', 'paper_type': '300gsm Art Paper', 'finish': 'Matte Lamination', 'colors': '4+4', 'min_quantity': 200, 'price_per_unit': Decimal('6.07'), 'setup_cost': Decimal('200.00'), 'turnaround_days': 7},
                {'size': 'Standard (89x51mm)', 'paper_type': '300gsm Art Paper', 'finish': 'Matte Lamination', 'colors': '4+4', 'min_quantity': 500, 'price_per_unit': Decimal('3.26'), 'setup_cost': Decimal('200.00'), 'turnaround_days': 6},
                {'size': 'Standard (89x51mm)', 'paper_type': '300gsm Art Paper', 'finish': 'Matte Lamination', 'colors': '4+4', 'min_quantity': 1000, 'price_per_unit': Decimal('2.33'), 'setup_cost': Decimal('200.00'), 'turnaround_days': 5},
                {'size': 'Standard (89x51mm)', 'paper_type': '300gsm Art Paper', 'finish': 'Matte Lamination', 'colors': '4+4', 'min_quantity': 2000, 'price_per_unit': Decimal('1.90'), 'setup_cost': Decimal('200.00'), 'turnaround_days': 5},
                {'size': 'Standard (89x51mm)', 'paper_type': '300gsm Art Paper', 'finish': 'Matte Lamination', 'colors': '4+4', 'min_quantity': 5000, 'price_per_unit': Decimal('1.64'), 'setup_cost': Decimal('200.00'), 'turnaround_days': 5},
                
                # 350gsm Art Paper with Matte Lamination
                {'size': 'Standard (89x51mm)', 'paper_type': '350gsm Art Paper', 'finish': 'Matte Lamination', 'colors': '4+4', 'min_quantity': 200, 'price_per_unit': Decimal('5.96'), 'setup_cost': Decimal('250.00'), 'turnaround_days': 7},
                {'size': 'Standard (89x51mm)', 'paper_type': '350gsm Art Paper', 'finish': 'Matte Lamination', 'colors': '4+4', 'min_quantity': 500, 'price_per_unit': Decimal('2.93'), 'setup_cost': Decimal('250.00'), 'turnaround_days': 6},
                {'size': 'Standard (89x51mm)', 'paper_type': '350gsm Art Paper', 'finish': 'Matte Lamination', 'colors': '4+4', 'min_quantity': 1000, 'price_per_unit': Decimal('1.96'), 'setup_cost': Decimal('250.00'), 'turnaround_days': 5},
                {'size': 'Standard (89x51mm)', 'paper_type': '350gsm Art Paper', 'finish': 'Matte Lamination', 'colors': '4+4', 'min_quantity': 2000, 'price_per_unit': Decimal('1.45'), 'setup_cost': Decimal('250.00'), 'turnaround_days': 5},
                {'size': 'Standard (89x51mm)', 'paper_type': '350gsm Art Paper', 'finish': 'Matte Lamination', 'colors': '4+4', 'min_quantity': 5000, 'price_per_unit': Decimal('1.16'), 'setup_cost': Decimal('250.00'), 'turnaround_days': 5},
                
                # Glossy Lamination Options
                {'size': 'Standard (89x51mm)', 'paper_type': '300gsm Art Paper', 'finish': 'Glossy Lamination', 'colors': '4+4', 'min_quantity': 200, 'price_per_unit': Decimal('6.25'), 'setup_cost': Decimal('220.00'), 'turnaround_days': 7},
                {'size': 'Standard (89x51mm)', 'paper_type': '300gsm Art Paper', 'finish': 'Glossy Lamination', 'colors': '4+4', 'min_quantity': 500, 'price_per_unit': Decimal('3.45'), 'setup_cost': Decimal('220.00'), 'turnaround_days': 6},
                {'size': 'Standard (89x51mm)', 'paper_type': '300gsm Art Paper', 'finish': 'Glossy Lamination', 'colors': '4+4', 'min_quantity': 1000, 'price_per_unit': Decimal('2.58'), 'setup_cost': Decimal('220.00'), 'turnaround_days': 5},
                
                # Single side printing options
                {'size': 'Standard (89x51mm)', 'paper_type': '300gsm Art Paper', 'finish': 'Matte Lamination', 'colors': '4+0', 'min_quantity': 200, 'price_per_unit': Decimal('4.50'), 'setup_cost': Decimal('150.00'), 'turnaround_days': 6},
                {'size': 'Standard (89x51mm)', 'paper_type': '300gsm Art Paper', 'finish': 'Matte Lamination', 'colors': '4+0', 'min_quantity': 500, 'price_per_unit': Decimal('2.75'), 'setup_cost': Decimal('150.00'), 'turnaround_days': 5},
                {'size': 'Standard (89x51mm)', 'paper_type': '300gsm Art Paper', 'finish': 'Matte Lamination', 'colors': '4+0', 'min_quantity': 1000, 'price_per_unit': Decimal('1.95'), 'setup_cost': Decimal('150.00'), 'turnaround_days': 5},
                
                # Custom sizes
                {'size': 'A6 (105x148mm)', 'paper_type': '300gsm Art Paper', 'finish': 'Matte Lamination', 'colors': '4+4', 'min_quantity': 200, 'price_per_unit': Decimal('8.50'), 'setup_cost': Decimal('300.00'), 'turnaround_days': 8},
                {'size': 'A6 (105x148mm)', 'paper_type': '300gsm Art Paper', 'finish': 'Matte Lamination', 'colors': '4+4', 'min_quantity': 500, 'price_per_unit': Decimal('5.25'), 'setup_cost': Decimal('300.00'), 'turnaround_days': 7},
                {'size': 'A6 (105x148mm)', 'paper_type': '300gsm Art Paper', 'finish': 'Matte Lamination', 'colors': '4+4', 'min_quantity': 1000, 'price_per_unit': Decimal('3.75'), 'setup_cost': Decimal('300.00'), 'turnaround_days': 6},
            ]
            
            for pricing in pricing_data:
                ProductPricing.objects.create(product=product, **pricing, is_active=True)
            
            self.stdout.write(f'Created {len(pricing_data)} pricing tiers for Flash Cards')

    def create_business_cards(self):
        """Create business cards product"""
        category = ServiceCategory.objects.get(name='Business Stationery')
        
        product, created = Product.objects.get_or_create(
            name='Premium Business Cards',
            category=category,
            defaults={
                'slug': 'premium-business-cards',
                'description': '''Make a lasting impression with our premium business cards. Printed on high-quality card stock with professional finishes, our business cards help you stand out in networking situations. Choose from various paper weights, finishes, and special effects to create business cards that truly represent your brand.''',
                'short_description': 'Professional business cards with premium materials and finishes.',
                'width_mm': 89.0,
                'height_mm': 51.0,
                'bleed_mm': 3.0,
                'safe_zone_mm': 5.0,
                'dpi': 300,
                'has_design_tool': True,
                'allows_upload': True,
                'base_price': Decimal('25.00'),
                'price_per_unit': Decimal('1.50'),
                'minimum_quantity': 100,
                'is_active': True,
                'is_featured': True
            }
        )
        
        if created:
            self.stdout.write(f'Created product: {product.name}')
            
            # Add business card pricing
            pricing_data = [
                {'size': 'Standard (89x51mm)', 'paper_type': '350gsm Card Stock', 'finish': 'Matte Finish', 'colors': '4+4', 'min_quantity': 100, 'price_per_unit': Decimal('2.25'), 'setup_cost': Decimal('100.00'), 'turnaround_days': 3},
                {'size': 'Standard (89x51mm)', 'paper_type': '350gsm Card Stock', 'finish': 'Matte Finish', 'colors': '4+4', 'min_quantity': 250, 'price_per_unit': Decimal('1.80'), 'setup_cost': Decimal('100.00'), 'turnaround_days': 3},
                {'size': 'Standard (89x51mm)', 'paper_type': '350gsm Card Stock', 'finish': 'Matte Finish', 'colors': '4+4', 'min_quantity': 500, 'price_per_unit': Decimal('1.50'), 'setup_cost': Decimal('100.00'), 'turnaround_days': 2},
                {'size': 'Standard (89x51mm)', 'paper_type': '350gsm Card Stock', 'finish': 'Matte Finish', 'colors': '4+4', 'min_quantity': 1000, 'price_per_unit': Decimal('1.25'), 'setup_cost': Decimal('100.00'), 'turnaround_days': 2},
                
                {'size': 'Standard (89x51mm)', 'paper_type': '400gsm Premium Stock', 'finish': 'Glossy Finish', 'colors': '4+4', 'min_quantity': 100, 'price_per_unit': Decimal('2.75'), 'setup_cost': Decimal('120.00'), 'turnaround_days': 4},
                {'size': 'Standard (89x51mm)', 'paper_type': '400gsm Premium Stock', 'finish': 'Glossy Finish', 'colors': '4+4', 'min_quantity': 250, 'price_per_unit': Decimal('2.25'), 'setup_cost': Decimal('120.00'), 'turnaround_days': 4},
                {'size': 'Standard (89x51mm)', 'paper_type': '400gsm Premium Stock', 'finish': 'Glossy Finish', 'colors': '4+4', 'min_quantity': 500, 'price_per_unit': Decimal('1.95'), 'setup_cost': Decimal('120.00'), 'turnaround_days': 3},
                {'size': 'Standard (89x51mm)', 'paper_type': '400gsm Premium Stock', 'finish': 'Glossy Finish', 'colors': '4+4', 'min_quantity': 1000, 'price_per_unit': Decimal('1.65'), 'setup_cost': Decimal('120.00'), 'turnaround_days': 3},
            ]
            
            for pricing in pricing_data:
                ProductPricing.objects.create(product=product, **pricing, is_active=True)

    def create_brochures(self):
        """Create brochures product"""
        category = ServiceCategory.objects.get(name='Marketing Materials')
        
        product, created = Product.objects.get_or_create(
            name='Tri-fold Brochures',
            category=category,
            defaults={
                'slug': 'tri-fold-brochures',
                'description': '''Professional tri-fold brochures perfect for marketing campaigns, product showcases, and information distribution. Our high-quality printing ensures vibrant colors and crisp text that effectively communicate your message. Available in various paper weights and finishes to suit your brand requirements.''',
                'short_description': 'Professional tri-fold brochures for marketing and information distribution.',
                'width_mm': 210.0,
                'height_mm': 297.0,  # A4 size
                'bleed_mm': 3.0,
                'safe_zone_mm': 5.0,
                'dpi': 300,
                'has_design_tool': True,
                'allows_upload': True,
                'base_price': Decimal('30.00'),
                'price_per_unit': Decimal('3.50'),
                'minimum_quantity': 100,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(f'Created product: {product.name}')
            
            # Add brochure pricing
            pricing_data = [
                {'size': 'A4 Tri-fold', 'paper_type': '250gsm Art Paper', 'finish': 'Matte Finish', 'colors': '4+4', 'min_quantity': 100, 'price_per_unit': Decimal('4.50'), 'setup_cost': Decimal('150.00'), 'turnaround_days': 5},
                {'size': 'A4 Tri-fold', 'paper_type': '250gsm Art Paper', 'finish': 'Matte Finish', 'colors': '4+4', 'min_quantity': 250, 'price_per_unit': Decimal('3.75'), 'setup_cost': Decimal('150.00'), 'turnaround_days': 4},
                {'size': 'A4 Tri-fold', 'paper_type': '250gsm Art Paper', 'finish': 'Matte Finish', 'colors': '4+4', 'min_quantity': 500, 'price_per_unit': Decimal('3.25'), 'setup_cost': Decimal('150.00'), 'turnaround_days': 4},
                {'size': 'A4 Tri-fold', 'paper_type': '250gsm Art Paper', 'finish': 'Matte Finish', 'colors': '4+4', 'min_quantity': 1000, 'price_per_unit': Decimal('2.85'), 'setup_cost': Decimal('150.00'), 'turnaround_days': 3},
                
                {'size': 'A4 Tri-fold', 'paper_type': '300gsm Art Paper', 'finish': 'Glossy Finish', 'colors': '4+4', 'min_quantity': 100, 'price_per_unit': Decimal('5.25'), 'setup_cost': Decimal('175.00'), 'turnaround_days': 6},
                {'size': 'A4 Tri-fold', 'paper_type': '300gsm Art Paper', 'finish': 'Glossy Finish', 'colors': '4+4', 'min_quantity': 250, 'price_per_unit': Decimal('4.35'), 'setup_cost': Decimal('175.00'), 'turnaround_days': 5},
                {'size': 'A4 Tri-fold', 'paper_type': '300gsm Art Paper', 'finish': 'Glossy Finish', 'colors': '4+4', 'min_quantity': 500, 'price_per_unit': Decimal('3.85'), 'setup_cost': Decimal('175.00'), 'turnaround_days': 5},
                {'size': 'A4 Tri-fold', 'paper_type': '300gsm Art Paper', 'finish': 'Glossy Finish', 'colors': '4+4', 'min_quantity': 1000, 'price_per_unit': Decimal('3.45'), 'setup_cost': Decimal('175.00'), 'turnaround_days': 4},
            ]
            
            for pricing in pricing_data:
                ProductPricing.objects.create(product=product, **pricing, is_active=True)

        self.stdout.write(self.style.SUCCESS('All products created with comprehensive pricing!'))