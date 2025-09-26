# apps/services/management/commands/create_product_form_fields.py
from django.core.management.base import BaseCommand
from apps.services.models import Product, ProductFormField
import json


class Command(BaseCommand):
    help = 'Create dynamic form fields for products'

    def handle(self, *args, **options):
        # Common form fields for all products
        common_fields = [
            {
                'field_name': 'quantity',
                'field_label': 'Quantity',
                'field_type': 'select',
                'options': json.dumps([
                    {'value': '25', 'label': '25', 'price_modifier': 0},
                    {'value': '50', 'label': '50', 'price_modifier': 0},
                    {'value': '100', 'label': '100', 'price_modifier': 0},
                    {'value': '250', 'label': '250', 'price_modifier': -0.1},
                    {'value': '500', 'label': '500', 'price_modifier': -0.15},
                    {'value': '1000', 'label': '1000', 'price_modifier': -0.2},
                ]),
                'default_value': '50',
                'order': 1,
                'is_required': True,
            },
            {
                'field_name': 'color',
                'field_label': 'Color',
                'field_type': 'radio',
                'options': json.dumps([
                    {'value': 'bw', 'label': 'Black & White', 'price_modifier': 0},
                    {'value': 'color', 'label': 'Full Color', 'price_modifier': 50},
                ]),
                'default_value': 'bw',
                'order': 2,
                'is_required': True,
            },
            {
                'field_name': 'paper_type',
                'field_label': 'Paper Type',
                'field_type': 'select',
                'options': json.dumps([
                    {'value': '70gsm', 'label': '70gsm Standard', 'price_modifier': 0},
                    {'value': '80gsm', 'label': '80gsm Premium', 'price_modifier': 25},
                    {'value': '100gsm', 'label': '100gsm Art Paper', 'price_modifier': 50},
                    {'value': '130gsm', 'label': '130gsm Glossy', 'price_modifier': 75},
                ]),
                'default_value': '70gsm',
                'order': 4,
                'is_required': True,
            },
        ]
        
        # Book-specific fields
        book_fields = [
            {
                'field_name': 'page_count',
                'field_label': 'Book Size And Page Count',
                'field_type': 'select',
                'options': json.dumps([
                    {'value': '50', 'label': '50 Pages', 'price_modifier': 0},
                    {'value': '100', 'label': '100 Pages', 'price_modifier': 100},
                    {'value': '150', 'label': '150 Pages', 'price_modifier': 200},
                    {'value': '200', 'label': '200 Pages', 'price_modifier': 300},
                    {'value': '300', 'label': '300 Pages', 'price_modifier': 500},
                ]),
                'default_value': '100',
                'order': 3,
                'is_required': True,
            },
            {
                'field_name': 'binding_type',
                'field_label': 'Binding Type',
                'field_type': 'select',
                'options': json.dumps([
                    {'value': 'spiral', 'label': 'Spiral Binding', 'price_modifier': 0},
                    {'value': 'perfect', 'label': 'Perfect Binding', 'price_modifier': 50},
                    {'value': 'saddle', 'label': 'Saddle Stitching', 'price_modifier': 25},
                    {'value': 'hardcover', 'label': 'Hardcover Binding', 'price_modifier': 200},
                ]),
                'default_value': 'spiral',
                'order': 5,
                'is_required': True,
            },
            {
                'field_name': 'cover_finish',
                'field_label': 'Cover Finish',
                'field_type': 'select',
                'options': json.dumps([
                    {'value': 'matte', 'label': 'Matte Finish', 'price_modifier': 0},
                    {'value': 'glossy', 'label': 'Glossy Finish', 'price_modifier': 30},
                    {'value': 'velvet', 'label': 'Velvet Finish', 'price_modifier': 50},
                    {'value': 'spot_uv', 'label': 'Spot UV', 'price_modifier': 100},
                ]),
                'default_value': 'matte',
                'order': 6,
                'is_required': True,
            },
            {
                'field_name': 'design_formatting',
                'field_label': 'Designing And Formatting',
                'field_type': 'checkbox',
                'options': json.dumps([
                    {'value': 'yes', 'label': 'Include Design & Formatting Service (+Rs.1500)', 'price_modifier': 1500},
                ]),
                'order': 7,
                'is_required': False,
            },
            {
                'field_name': 'isbn_allocation',
                'field_label': 'ISBN Allocation',
                'field_type': 'checkbox',
                'options': json.dumps([
                    {'value': 'yes', 'label': 'Include ISBN Allocation (+Rs.500)', 'price_modifier': 500},
                ]),
                'order': 8,
                'is_required': False,
            },
        ]
        
        # Stationery-specific fields
        stationery_fields = [
            {
                'field_name': 'finish_type',
                'field_label': 'Finish Type',
                'field_type': 'select',
                'options': json.dumps([
                    {'value': 'standard', 'label': 'Standard Finish', 'price_modifier': 0},
                    {'value': 'lamination', 'label': 'Lamination', 'price_modifier': 25},
                    {'value': 'spot_uv', 'label': 'Spot UV', 'price_modifier': 75},
                    {'value': 'embossing', 'label': 'Embossing', 'price_modifier': 100},
                ]),
                'default_value': 'standard',
                'order': 5,
                'is_required': True,
            },
        ]
        
        # Box-specific fields
        box_fields = [
            {
                'field_name': 'box_type',
                'field_label': 'Box Type',
                'field_type': 'select',
                'options': json.dumps([
                    {'value': 'standard', 'label': 'Standard Box', 'price_modifier': 0},
                    {'value': 'window', 'label': 'Window Box', 'price_modifier': 50},
                    {'value': 'magnetic', 'label': 'Magnetic Closure', 'price_modifier': 100},
                    {'value': 'custom', 'label': 'Custom Shape', 'price_modifier': 200},
                ]),
                'default_value': 'standard',
                'order': 3,
                'is_required': True,
            },
            {
                'field_name': 'material_type',
                'field_label': 'Material Type',
                'field_type': 'select',
                'options': json.dumps([
                    {'value': 'cardboard', 'label': 'Cardboard', 'price_modifier': 0},
                    {'value': 'corrugated', 'label': 'Corrugated', 'price_modifier': 30},
                    {'value': 'kraft', 'label': 'Kraft Paper', 'price_modifier': 20},
                    {'value': 'rigid', 'label': 'Rigid Box', 'price_modifier': 150},
                ]),
                'default_value': 'cardboard',
                'order': 4,
                'is_required': True,
            },
        ]
        
        created_count = 0
        
        # Create fields for all products
        for product in Product.objects.filter(is_active=True):
            # Clear existing fields
            ProductFormField.objects.filter(product=product).delete()
            
            # Add common fields
            for field_data in common_fields:
                field_data['product'] = product
                ProductFormField.objects.create(**field_data)
                created_count += 1
            
            # Add product-specific fields based on product name/category
            product_name_lower = product.name.lower()
            
            if 'book' in product_name_lower:
                for field_data in book_fields:
                    field_data['product'] = product
                    ProductFormField.objects.create(**field_data)
                    created_count += 1
            elif 'stationery' in product_name_lower or 'card' in product_name_lower:
                for field_data in stationery_fields:
                    field_data['product'] = product
                    ProductFormField.objects.create(**field_data)
                    created_count += 1
            elif 'box' in product_name_lower or 'packaging' in product_name_lower:
                for field_data in box_fields:
                    field_data['product'] = product
                    ProductFormField.objects.create(**field_data)
                    created_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'Created form fields for: {product.name}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} form fields')
        )