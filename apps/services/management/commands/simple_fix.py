# Create: apps/services/management/commands/simple_fix.py

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.services.models import StaticProduct, ProductFormField
import json

class Command(BaseCommand):
    help = 'Simple fix for Children\'s Books fields - no complex parameters'

    def handle(self, *args, **options):
        self.stdout.write('Creating simple fields for Children\'s Books...')
        
        try:
            # Find the Children's Books product
            product = StaticProduct.objects.filter(name__icontains="children").first()
            if not product:
                # Try to find any book-related product
                product = StaticProduct.objects.filter(name__icontains="book").first()
            
            if not product:
                self.stdout.write(self.style.ERROR('No book product found'))
                return
                
            self.stdout.write(f'Found product: {product.name}')
            
            # Clear existing fields
            ProductFormField.objects.filter(static_product=product).delete()
            self.stdout.write('Cleared existing fields')
            
            # Create simple fields
            with transaction.atomic():
                self.create_simple_fields(product)
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created fields for {product.name}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )

    def create_simple_fields(self, product):
        """Create simple form fields"""
        
        # 1. Interior Color
        ProductFormField.objects.create(
            static_product=product,
            field_name='interior_color',
            field_label='Interior Color',
            field_type='radio',
            field_section='printing_options',
            order=1,
            section_order=1,
            help_text='Select the color option for your book interior',
            triggers_fields=json.dumps(['bw_page_count', 'color_page_count']),
            is_price_affecting=True,
            options=json.dumps([
                {'value': 'bw_premium', 'label': 'Black & White Premium', 'price_modifier': 0},
                {'value': 'bw_standard', 'label': 'Black & White Standard', 'price_modifier': -20},
                {'value': 'color_premium', 'label': 'Color Premium', 'price_modifier': 150},
                {'value': 'color_standard', 'label': 'Color Standard', 'price_modifier': 100},
                {'value': 'combine_color', 'label': 'Combine Color', 'price_modifier': 75},
            ])
        )
        self.stdout.write('  ✓ Interior Color')

        # 2. Page Count (when NOT combine color)
        ProductFormField.objects.create(
            static_product=product,
            field_name='page_count',
            field_label='Page Count',
            field_type='number',
            field_section='product_specs',
            order=1,
            section_order=2,
            help_text='Total number of pages in your book',
            min_value=4,
            max_value=1000,
            default_value='50',
            is_price_affecting=True,
            show_condition=json.dumps({'field': 'interior_color', 'value': 'combine_color', 'operator': 'not_equals'})
        )
        self.stdout.write('  ✓ Page Count')

        # 3. Black & White Page Count (when combine color)
        ProductFormField.objects.create(
            static_product=product,
            field_name='bw_page_count',
            field_label='Black and White Page Count',
            field_type='number',
            field_section='product_specs',
            order=2,
            section_order=2,
            help_text='Number of black and white pages',
            min_value=0,
            max_value=1000,
            default_value='0',
            is_price_affecting=True,
            show_condition=json.dumps({'field': 'interior_color', 'value': 'combine_color', 'operator': 'equals'})
        )
        self.stdout.write('  ✓ Black & White Page Count')

        # 4. Color Page Count (when combine color)
        ProductFormField.objects.create(
            static_product=product,
            field_name='color_page_count',
            field_label='Color Page Count',
            field_type='number',
            field_section='product_specs',
            order=3,
            section_order=2,
            help_text='Number of color pages',
            min_value=0,
            max_value=1000,
            default_value='0',
            is_price_affecting=True,
            show_condition=json.dumps({'field': 'interior_color', 'value': 'combine_color', 'operator': 'equals'})
        )
        self.stdout.write('  ✓ Color Page Count')

        # 5. Book Size
        ProductFormField.objects.create(
            static_product=product,
            field_name='book_size',
            field_label='Book Size And Page Count',
            field_type='select',
            field_section='product_specs',
            order=4,
            section_order=2,
            help_text='Select the size for your book',
            is_price_affecting=True,
            options=json.dumps([
                {'value': 'a4', 'label': 'A4', 'price_modifier': 0},
                {'value': 'letter', 'label': 'Letter', 'price_modifier': 5},
                {'value': 'executive', 'label': 'Executive', 'price_modifier': -10},
                {'value': 'a5', 'label': 'A5', 'price_modifier': -25},
            ])
        )
        self.stdout.write('  ✓ Book Size')

        # 6. Paper Type
        ProductFormField.objects.create(
            static_product=product,
            field_name='paper_type',
            field_label='Paper Type',
            field_type='select',
            field_section='product_specs',
            order=5,
            section_order=2,
            help_text='Select the paper quality',
            is_price_affecting=True,
            options=json.dumps([
                {'value': '75gsm', 'label': '75 GSM', 'price_modifier': 0},
                {'value': '100gsm', 'label': '100 GSM', 'price_modifier': 25},
                {'value': '100gsm_art', 'label': '100 GSM Art Paper', 'price_modifier': 50},
                {'value': '120gsm_art', 'label': '120 GSM Art Paper', 'price_modifier': 75},
            ])
        )
        self.stdout.write('  ✓ Paper Type')

        # 7. Binding Type
        ProductFormField.objects.create(
            static_product=product,
            field_name='binding_type',
            field_label='Binding Type',
            field_type='select',
            field_section='finishing_options',
            order=1,
            section_order=3,
            help_text='Select the binding method',
            is_price_affecting=True,
            options=json.dumps([
                {'value': 'saddle_stitch', 'label': 'Saddle Stitch', 'price_modifier': 0},
                {'value': 'spiral_binding', 'label': 'Spiral Binding', 'price_modifier': 30},
                {'value': 'paperback', 'label': 'Paperback (Perfect)', 'price_modifier': 50},
                {'value': 'hardcover', 'label': 'Hardcover', 'price_modifier': 200},
            ])
        )
        self.stdout.write('  ✓ Binding Type')

        # 8. Cover Finish
        ProductFormField.objects.create(
            static_product=product,
            field_name='cover_finish',
            field_label='Cover Finish',
            field_type='radio',
            field_section='finishing_options',
            order=2,
            section_order=3,
            help_text='Select the cover finishing',
            is_price_affecting=True,
            options=json.dumps([
                {'value': 'glossy', 'label': 'Glossy', 'price_modifier': 25},
                {'value': 'matte', 'label': 'Matte', 'price_modifier': 20},
            ])
        )
        self.stdout.write('  ✓ Cover Finish')

        # 9. Designing And Formatting
        ProductFormField.objects.create(
            static_product=product,
            field_name='design_service',
            field_label='Designing And Formatting',
            field_type='radio',
            field_section='additional_services',
            order=1,
            section_order=4,
            help_text='Rs.1500/- Extra Per Cover Page And Rs. 50 Extra Per Inner Page',
            is_price_affecting=True,
            options=json.dumps([
                {'value': 'not_required', 'label': 'Not Required', 'price_modifier': 0},
                {'value': 'yes_you_can', 'label': 'Yes You Can', 'price_modifier': 1500, 'description': 'Rs.1500/- Extra Per Cover Page And Rs. 50 Extra Per Inner Page'},
            ])
        )
        self.stdout.write('  ✓ Designing And Formatting')

        # 10. ISBN Allocation
        ProductFormField.objects.create(
            static_product=product,
            field_name='isbn_allocation',
            field_label='ISBN Allocation',
            field_type='radio',
            field_section='additional_services',
            order=2,
            section_order=4,
            help_text='ISBN allocation service',
            is_price_affecting=True,
            options=json.dumps([
                {'value': 'not_apply', 'label': 'Not Apply', 'price_modifier': 0},
                {'value': 'yes_assign', 'label': 'Yes Assign a Unique ISBN Number', 'price_modifier': 500},
            ])
        )
        self.stdout.write('  ✓ ISBN Allocation')

        # 11. Number of Copies
        ProductFormField.objects.create(
            static_product=product,
            field_name='copies',
            field_label='Number of Copies',
            field_type='number',
            field_section='quantity_pricing',
            order=1,
            section_order=5,
            help_text='Min. 25',
            min_value=25,
            max_value=10000,
            default_value='25',
            is_price_affecting=True
        )
        self.stdout.write('  ✓ Number of Copies')