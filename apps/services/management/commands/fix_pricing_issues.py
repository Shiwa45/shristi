# apps/services/management/commands/fix_pricing_issues.py
from django.core.management.base import BaseCommand
from apps.services.models import Product, ProductFormField
import json


class Command(BaseCommand):
    help = 'Fix pricing issues and ensure correct base prices'

    def handle(self, *args, **options):
        # Correct base prices for all products
        price_corrections = {
            'Business Cards': 8,
            'Letter Head': 5,
            'Brochures': 12,
            'Flyers': 12,
            'Catalogue': 12,
            'Sticker': 3,
            'Envelopes': 4,
            'Document Printing': 2,
            'Bill Book': 150,
            'Paper Boxes': 25,
            'Corrugated Boxes': 25,
            'Folding Carton Boxes': 25,
            'Kraft Boxes': 25,
            'Cosmetic Paper Boxes': 25,
            'Medical Paper Boxes': 25,
            'Retail Paper Boxes': 25,
            'Annual Reports': 150,
            'Art Book Printing': 150,
            'Children\'s Book Printing': 150,
            'Coffee Table Books': 150,
            'Coloring Book Printing': 150,
            'Comic Book Printing': 150,
            'On Demand Books': 150,
            'Year Book Printing': 150,
            'Banners & Flex Printing': 50,
            'Wedding Cards': 25,
            'Roll-Up Standees': 1500,
            'Invoice Books': 150,
        }
        
        updated_count = 0
        for product_name, correct_price in price_corrections.items():
            try:
                product = Product.objects.get(name=product_name)
                if product.base_price != correct_price:
                    product.base_price = correct_price
                    product.price_per_unit = correct_price
                    product.save()
                    updated_count += 1
                    self.stdout.write(f'✓ Updated {product_name}: ₹{correct_price}')
                else:
                    self.stdout.write(f'- {product_name}: ₹{correct_price} (already correct)')
            except Product.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'⚠ Product not found: {product_name}'))
        
        # Fix card size field for business cards (change -25 to -0.25 for percentage)
        try:
            business_cards = Product.objects.get(name='Business Cards')
            card_size_field = ProductFormField.objects.get(
                product=business_cards, 
                field_name='card_size'
            )
            
            # Update the options to use percentage for mini cards
            options = card_size_field.get_options()
            for option in options:
                if option['value'] == 'mini':
                    option['price_modifier'] = -0.25  # 25% discount
            
            card_size_field.options = json.dumps(options)
            card_size_field.save()
            self.stdout.write('✓ Fixed card size pricing for Business Cards')
            
        except (Product.DoesNotExist, ProductFormField.DoesNotExist):
            self.stdout.write(self.style.WARNING('⚠ Could not fix card size field'))
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 Fixed pricing for {updated_count} products')
        )