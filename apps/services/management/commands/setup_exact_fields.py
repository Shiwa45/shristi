# Create: apps/services/management/commands/setup_exact_fields.py

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.services.models import StaticProduct, ProductFormField, ServiceCategory
import json

class Command(BaseCommand):
    help = 'Setup EXACT fields as specified by the user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--product',
            type=str,
            choices=['book_printing', 'document_printing', 'business_cards', 'letter_head', 'all'],
            default='all',
            help='Which product to setup'
        )

    def handle(self, *args, **options):
        product_type = options['product']
        
        with transaction.atomic():
            if product_type == 'all':
                self.setup_book_printing()
                self.setup_document_printing()
                self.setup_business_cards()
                self.setup_letter_head()
            elif product_type == 'book_printing':
                self.setup_book_printing()
            elif product_type == 'document_printing':
                self.setup_document_printing()
            elif product_type == 'business_cards':
                self.setup_business_cards()
            elif product_type == 'letter_head':
                self.setup_letter_head()

        self.stdout.write(
            self.style.SUCCESS(f'Successfully setup exact fields for {product_type}')
        )

    def get_or_create_product(self, name, category_name):
        """Get or create product"""
        category, _ = ServiceCategory.objects.get_or_create(
            name=category_name,
            defaults={'description': f'{category_name} services', 'is_active': True}
        )
        
        # Try to find existing product by name (case insensitive)
        try:
            product = StaticProduct.objects.get(name__icontains=name.split()[0])
            self.stdout.write(f'Found existing product: {product.name}')
        except StaticProduct.DoesNotExist:
            product = StaticProduct.objects.create(
                name=name,
                category=category,
                description=f'Professional {name.lower()} services',
                short_description=f'High-quality {name.lower()}',
                base_price=100.00,
                price_unit='per piece',
                is_active=True
            )
            self.stdout.write(f'Created new product: {product.name}')
        
        return product

    def create_field(self, product, field_name, field_label, field_type, options_data, **kwargs):
        """Create or update field"""
        # Remove price_modifier from kwargs since it doesn't exist as a field
        kwargs.pop('price_modifier', None)
        
        defaults = {
            'field_label': field_label,
            'field_type': field_type,
            'options': json.dumps(options_data) if options_data else '',
            'is_active': True,
            **kwargs
        }

        field, created = ProductFormField.objects.update_or_create(
            static_product=product,
            field_name=field_name,
            defaults=defaults
        )

        action = "✓" if created else "↻"
        self.stdout.write(f"  {action} {field_label}")
        return field

    def setup_book_printing(self):
        """Book Printing - EXACTLY as specified"""
        self.stdout.write(self.style.WARNING("Setting up Book Printing..."))
        
        # Find Children's Books or create Book Printing
        try:
            product = StaticProduct.objects.get(name__icontains="children")
        except StaticProduct.DoesNotExist:
            product = self.get_or_create_product("Book Printing", "Book Printing")
        
        # Clear existing fields
        ProductFormField.objects.filter(static_product=product).delete()

        # 1. Interior Color
        self.create_field(
            product=product,
            field_name='interior_color',
            field_label='Interior Color',
            field_type='radio',
            field_section='printing_options',
            order=1,
            section_order=1,
            help_text='Select the color option for your book interior',
            triggers_fields=json.dumps(['bw_page_count', 'color_page_count']),
            is_price_affecting=True,
            options_data=[
                {'value': 'bw_premium', 'label': 'Black & White Premium', 'price_modifier': 0},
                {'value': 'bw_standard', 'label': 'Black & White Standard', 'price_modifier': -20},
                {'value': 'color_premium', 'label': 'Color Premium', 'price_modifier': 150},
                {'value': 'color_standard', 'label': 'Color Standard', 'price_modifier': 100},
                {'value': 'combine_color', 'label': 'Combine Color', 'price_modifier': 75},
            ]
        )

        # 2. Page Count (shows when NOT combine color)
        self.create_field(
            product=product,
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

        # 3. Black & White Page Count (shows when combine color)
        self.create_field(
            product=product,
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

        # 4. Color Page Count (shows when combine color)
        self.create_field(
            product=product,
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

        # 5. Book Size
        self.create_field(
            product=product,
            field_name='book_size',
            field_label='Book Size And Page Count',
            field_type='select',
            field_section='product_specs',
            order=4,
            section_order=2,
            help_text='Select the size for your book',
            is_price_affecting=True,
            options_data=[
                {'value': 'a4', 'label': 'A4', 'price_modifier': 0},
                {'value': 'letter', 'label': 'Letter', 'price_modifier': 5},
                {'value': 'executive', 'label': 'Executive', 'price_modifier': -10},
                {'value': 'a5', 'label': 'A5', 'price_modifier': -25},
            ]
        )

        # 6. Paper Type
        self.create_field(
            product=product,
            field_name='paper_type',
            field_label='Paper Type',
            field_type='select',
            field_section='product_specs',
            order=5,
            section_order=2,
            help_text='Select the paper quality',
            is_price_affecting=True,
            options_data=[
                {'value': '75gsm', 'label': '75 GSM', 'price_modifier': 0},
                {'value': '100gsm', 'label': '100 GSM', 'price_modifier': 25},
                {'value': '100gsm_art', 'label': '100 GSM Art Paper', 'price_modifier': 50},
                {'value': '120gsm_art', 'label': '120 GSM Art Paper', 'price_modifier': 75},
            ]
        )

        # 7. Binding Type
        self.create_field(
            product=product,
            field_name='binding_type',
            field_label='Binding Type',
            field_type='select',
            field_section='finishing_options',
            order=1,
            section_order=3,
            help_text='Select the binding method',
            is_price_affecting=True,
            options_data=[
                {'value': 'saddle_stitch', 'label': 'Saddle Stitch', 'price_modifier': 0},
                {'value': 'spiral_binding', 'label': 'Spiral Binding', 'price_modifier': 30},
                {'value': 'paperback', 'label': 'Paperback (Perfect)', 'price_modifier': 50},
                {'value': 'hardcover', 'label': 'Hardcover', 'price_modifier': 200},
            ]
        )

        # 8. Cover Finish
        self.create_field(
            product=product,
            field_name='cover_finish',
            field_label='Cover Finish',
            field_type='radio',
            field_section='finishing_options',
            order=2,
            section_order=3,
            help_text='Select the cover finishing',
            is_price_affecting=True,
            options_data=[
                {'value': 'glossy', 'label': 'Glossy', 'price_modifier': 25},
                {'value': 'matte', 'label': 'Matte', 'price_modifier': 20},
            ]
        )

        # 9. Designing And Formatting
        self.create_field(
            product=product,
            field_name='design_service',
            field_label='Designing And Formatting',
            field_type='radio',
            field_section='additional_services',
            order=1,
            section_order=4,
            help_text='Rs.1500/- Extra Per Cover Page And Rs. 50 Extra Per Inner Page',
            is_price_affecting=True,
            options_data=[
                {'value': 'not_required', 'label': 'Not Required', 'price_modifier': 0},
                {'value': 'yes_you_can', 'label': 'Yes You Can', 'price_modifier': 1500, 'description': 'Rs.1500/- Extra Per Cover Page And Rs. 50 Extra Per Inner Page'},
            ]
        )

        # 10. ISBN Allocation
        self.create_field(
            product=product,
            field_name='isbn_allocation',
            field_label='ISBN Allocation',
            field_type='radio',
            field_section='additional_services',
            order=2,
            section_order=4,
            help_text='ISBN allocation service',
            is_price_affecting=True,
            options_data=[
                {'value': 'not_apply', 'label': 'Not Apply', 'price_modifier': 0},
                {'value': 'yes_assign', 'label': 'Yes Assign a Unique ISBN Number', 'price_modifier': 500},
            ]
        )

        # 11. Number of Copies
        self.create_field(
            product=product,
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

    def setup_document_printing(self):
        """Document Printing - EXACTLY as specified"""
        self.stdout.write(self.style.WARNING("Setting up Document Printing..."))
        
        product = self.get_or_create_product("Document Printing", "Documents")
        
        # Clear existing fields
        ProductFormField.objects.filter(static_product=product).delete()

        # 1. Interior Color
        self.create_field(
            product=product,
            field_name='interior_color',
            field_label='Interior Color',
            field_type='radio',
            field_section='printing_options',
            order=1,
            section_order=1,
            help_text='Select color option',
            triggers_fields=json.dumps(['bw_page_count', 'color_page_count']),
            is_price_affecting=True,
            options_data=[
                {'value': 'bw', 'label': 'Black & White', 'price_modifier': 0},
                {'value': 'color', 'label': 'Color', 'price_modifier': 100},
                {'value': 'combine_color', 'label': 'Combine Color', 'price_modifier': 50},
            ]
        )

        # 2. Document Size
        self.create_field(
            product=product,
            field_name='document_size',
            field_label='Document Size And Page Count',
            field_type='select',
            field_section='product_specs',
            order=1,
            section_order=2,
            help_text='Select document size',
            is_price_affecting=True,
            options_data=[
                {'value': 'a4', 'label': 'A4', 'price_modifier': 0},
                {'value': 'legal', 'label': 'Legal', 'price_modifier': 15},
                {'value': 'a3', 'label': 'A3', 'price_modifier': 30},
            ]
        )

        # 3. Page Count (when NOT combine color)
        self.create_field(
            product=product,
            field_name='page_count',
            field_label='Page Count',
            field_type='number',
            field_section='product_specs',
            order=2,
            section_order=2,
            help_text='Total number of pages',
            min_value=1,
            max_value=1000,
            default_value='10',
            is_price_affecting=True,
            show_condition=json.dumps({'field': 'interior_color', 'value': 'combine_color', 'operator': 'not_equals'})
        )

        # 4. Black & White Page Count (when combine color)
        self.create_field(
            product=product,
            field_name='bw_page_count',
            field_label='Black and White Page Count',
            field_type='number',
            field_section='product_specs',
            order=3,
            section_order=2,
            help_text='Number of black and white pages',
            min_value=0,
            max_value=1000,
            default_value='0',
            is_price_affecting=True,
            show_condition=json.dumps({'field': 'interior_color', 'value': 'combine_color', 'operator': 'equals'})
        )

        # 5. Color Page Count (when combine color)
        self.create_field(
            product=product,
            field_name='color_page_count',
            field_label='Color Page Count',
            field_type='number',
            field_section='product_specs',
            order=4,
            section_order=2,
            help_text='Number of color pages',
            min_value=0,
            max_value=1000,
            default_value='0',
            is_price_affecting=True,
            show_condition=json.dumps({'field': 'interior_color', 'value': 'combine_color', 'operator': 'equals'})
        )

        # 6. Paper Type
        self.create_field(
            product=product,
            field_name='paper_type',
            field_label='Paper Type',
            field_type='select',
            field_section='product_specs',
            order=5,
            section_order=2,
            help_text='Select paper quality',
            is_price_affecting=True,
            options_data=[
                {'value': '75gsm', 'label': '75 GSM', 'price_modifier': 0},
                {'value': '100gsm', 'label': '100 GSM', 'price_modifier': 20},
            ]
        )

        # 7. Binding Type
        self.create_field(
            product=product,
            field_name='binding_type',
            field_label='Binding Type',
            field_type='select',
            field_section='finishing_options',
            order=1,
            section_order=3,
            help_text='Select binding method',
            is_price_affecting=True,
            options_data=[
                {'value': 'spiral_binding', 'label': 'Spiral Binding', 'price_modifier': 30},
                {'value': 'paperback', 'label': 'Paperback (Perfect)', 'price_modifier': 50},
                {'value': 'hardcover', 'label': 'Hardcover', 'price_modifier': 150},
            ]
        )

        # 8. Cover Finish
        self.create_field(
            product=product,
            field_name='cover_finish',
            field_label='Cover Finish',
            field_type='radio',
            field_section='finishing_options',
            order=2,
            section_order=3,
            help_text='Select cover finish',
            is_price_affecting=True,
            options_data=[
                {'value': 'glossy', 'label': 'Glossy', 'price_modifier': 20},
                {'value': 'matte', 'label': 'Matte', 'price_modifier': 15},
            ]
        )

        # 9. Upload Your Files - Cover Page
        self.create_field(
            product=product,
            field_name='cover_file',
            field_label='Upload Your Files - Cover Page',
            field_type='file',
            field_section='file_uploads',
            order=1,
            section_order=4,
            help_text='PDF, Word File & Excel',
            is_price_affecting=False
        )

        # 10. Upload Your Files - Inner Page
        self.create_field(
            product=product,
            field_name='inner_file',
            field_label='Upload Your Files - Inner Page',
            field_type='file',
            field_section='file_uploads',
            order=2,
            section_order=4,
            help_text='PDF, Word File & Excel',
            is_price_affecting=False
        )

        # 11. Number of Copies
        self.create_field(
            product=product,
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

    def setup_business_cards(self):
        """Business Cards - EXACTLY as specified"""
        self.stdout.write(self.style.WARNING("Setting up Business Cards..."))
        
        product = self.get_or_create_product("Business Cards", "Marketing Materials")
        
        # Clear existing fields
        ProductFormField.objects.filter(static_product=product).delete()

        # 1. Printing Side
        self.create_field(
            product=product,
            field_name='printing_side',
            field_label='Printing Side',
            field_type='radio',
            field_section='printing_options',
            order=1,
            section_order=1,
            help_text='Front or Back',
            is_price_affecting=True,
            options_data=[
                {'value': 'front', 'label': 'Front', 'price_modifier': 0},
                {'value': 'back', 'label': 'Back', 'price_modifier': 0},
                {'value': 'both', 'label': 'Both Sides', 'price_modifier': 50},
            ]
        )

        # 2. Lamination
        self.create_field(
            product=product,
            field_name='lamination',
            field_label='Lamination',
            field_type='radio',
            field_section='finishing_options',
            order=1,
            section_order=2,
            help_text='Select lamination type',
            is_price_affecting=True,
            options_data=[
                {'value': 'matte', 'label': 'Matte', 'price_modifier': 20},
                {'value': 'glossy', 'label': 'Glossy', 'price_modifier': 25},
            ]
        )

        # Note: Business card quantities and pricing will be handled separately
        # as they have complex pricing tiers

    def setup_letter_head(self):
        """Letter Head - EXACTLY as specified"""
        self.stdout.write(self.style.WARNING("Setting up Letter Head..."))
        
        product = self.get_or_create_product("Letter Head", "Stationery")
        
        # Clear existing fields
        ProductFormField.objects.filter(static_product=product).delete()

        # 1. Paper Type
        self.create_field(
            product=product,
            field_name='paper_type',
            field_label='Paper Type',
            field_type='select',
            field_section='product_specs',
            order=1,
            section_order=1,
            help_text='JK Excel Bond Paper Do Paper 100 GSM',
            is_price_affecting=False,
            options_data=[
                {'value': 'jk_excel_bond', 'label': 'JK Excel Bond Paper Do Paper 100 GSM', 'price_modifier': 0},
            ]
        )

        # Note: Letter head quantities and pricing will be handled separately