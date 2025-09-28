from django.core.management.base import BaseCommand
from django.db import transaction
from apps.services.models import Product, ProductFormField
import json

class Command(BaseCommand):
    help = 'Add dynamic form fields to existing Product models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--product-name',
            type=str,
            help='Specify a specific product name to migrate (optional)'
        )

    def handle(self, *args, **options):
        product_name = options['product_name']

        if product_name:
            self.migrate_specific_product(product_name)
        else:
            self.migrate_all_products()

        self.stdout.write(
            self.style.SUCCESS('Successfully migrated existing products')
        )

    @transaction.atomic
    def migrate_all_products(self):
        """Migrate all existing products"""
        products = Product.objects.all()

        for product in products:
            self.add_fields_to_product(product)

    def migrate_specific_product(self, product_name):
        """Migrate a specific product by name"""
        try:
            product = Product.objects.get(name__icontains=product_name)
            self.add_fields_to_product(product)
            self.stdout.write(f"Migrated product: {product.name}")
        except Product.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Product with name containing "{product_name}" not found')
            )
        except Product.MultipleObjectsReturned:
            products = Product.objects.filter(name__icontains=product_name)
            self.stdout.write(f"Multiple products found with '{product_name}'. Please be more specific:")
            for p in products:
                self.stdout.write(f"  - {p.name}")

    def add_fields_to_product(self, product):
        """Add appropriate form fields to a product based on its category and name"""
        product_name = product.name.lower()
        category_name = product.category.name.lower()

        self.stdout.write(f"Processing: {product.name} (Category: {product.category.name})")

        # Clear existing fields for this product
        ProductFormField.objects.filter(product=product).delete()

        # Determine product type and add appropriate fields
        if any(keyword in product_name for keyword in ['book', 'annual', 'children', 'comic', 'coloring']) or 'book' in category_name:
            self.add_book_fields(product)
        elif any(keyword in product_name for keyword in ['card', 'business card']) or 'card' in category_name:
            self.add_business_card_fields(product)
        elif any(keyword in product_name for keyword in ['letter', 'letterhead', 'header']) or 'letter' in category_name:
            self.add_letterhead_fields(product)
        elif any(keyword in product_name for keyword in ['document', 'report', 'presentation']) or 'document' in category_name:
            self.add_document_fields(product)
        else:
            self.add_generic_fields(product)

        self.stdout.write(f"  ✓ Added fields to {product.name}")

    def create_field(self, product, field_name, field_label, field_type, options_data, **kwargs):
        """Create a product form field"""
        defaults = {
            'field_label': field_label,
            'field_type': field_type,
            'options': json.dumps(options_data) if options_data else '',
            'is_active': True,
            **kwargs
        }

        field, created = ProductFormField.objects.update_or_create(
            product=product,
            field_name=field_name,
            defaults=defaults
        )
        return field

    def add_book_fields(self, product):
        """Add book printing fields"""
        # Interior Color
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
            options_data=[
                {'value': 'bw_premium', 'label': 'Black & White Premium', 'price_modifier': 0},
                {'value': 'bw_standard', 'label': 'Black & White Standard', 'price_modifier': -20},
                {'value': 'color_premium', 'label': 'Color Premium', 'price_modifier': 150},
                {'value': 'color_standard', 'label': 'Color Standard', 'price_modifier': 100},
                {'value': 'combine_color', 'label': 'Combined Color', 'price_modifier': 75},
            ]
        )

        # Page Count
        self.create_field(
            product=product,
            field_name='page_count',
            field_label='Total Page Count',
            field_type='number',
            field_section='product_specs',
            order=2,
            section_order=1,
            help_text='Total number of pages in your book',
            min_value=4,
            max_value=1000,
            default_value='50',
            show_condition=json.dumps({'field': 'interior_color', 'value': 'combine_color', 'operator': 'not_equals'}),
            options_data=None
        )

        # Conditional page counts
        self.create_field(
            product=product,
            field_name='bw_page_count',
            field_label='Black & White Page Count',
            field_type='number',
            field_section='product_specs',
            order=3,
            section_order=1,
            help_text='Number of black and white pages',
            min_value=0,
            max_value=1000,
            default_value='0',
            show_condition=json.dumps({'field': 'interior_color', 'value': 'combine_color', 'operator': 'equals'}),
            options_data=None
        )

        self.create_field(
            product=product,
            field_name='color_page_count',
            field_label='Color Page Count',
            field_type='number',
            field_section='product_specs',
            order=4,
            section_order=1,
            help_text='Number of color pages',
            min_value=0,
            max_value=1000,
            default_value='0',
            show_condition=json.dumps({'field': 'interior_color', 'value': 'combine_color', 'operator': 'equals'}),
            options_data=None
        )

        # Book Size
        self.create_field(
            product=product,
            field_name='book_size',
            field_label='Book Size',
            field_type='select',
            field_section='product_specs',
            order=5,
            section_order=1,
            help_text='Select the size for your book',
            options_data=[
                {'value': 'a4', 'label': 'A4 (210 x 297 mm)', 'price_modifier': 0},
                {'value': 'letter', 'label': 'Letter (216 x 279 mm)', 'price_modifier': 5},
                {'value': 'executive', 'label': 'Executive (184 x 267 mm)', 'price_modifier': -10},
                {'value': 'a5', 'label': 'A5 (148 x 210 mm)', 'price_modifier': -25},
            ]
        )

        # Paper Type
        self.create_field(
            product=product,
            field_name='paper_type',
            field_label='Paper Type',
            field_type='select',
            field_section='product_specs',
            order=6,
            section_order=1,
            help_text='Select the paper quality',
            options_data=[
                {'value': '75gsm', 'label': '75 GSM', 'price_modifier': 0},
                {'value': '100gsm', 'label': '100 GSM', 'price_modifier': 25},
                {'value': '100gsm_art', 'label': '100 GSM Art Paper', 'price_modifier': 50},
                {'value': '120gsm_art', 'label': '120 GSM Art Paper', 'price_modifier': 75},
            ]
        )

        # Binding Type
        self.create_field(
            product=product,
            field_name='binding_type',
            field_label='Binding Type',
            field_type='select',
            field_section='finishing_options',
            order=1,
            section_order=2,
            help_text='Select the binding method',
            options_data=[
                {'value': 'saddle_stitch', 'label': 'Saddle Stitch', 'price_modifier': 0},
                {'value': 'spiral_binding', 'label': 'Spiral Binding', 'price_modifier': 30},
                {'value': 'paperback', 'label': 'Paperback (Perfect)', 'price_modifier': 50},
                {'value': 'hardcover', 'label': 'Hardcover', 'price_modifier': 150},
            ]
        )

        # Cover Finish
        self.create_field(
            product=product,
            field_name='cover_finish',
            field_label='Cover Finish',
            field_type='radio',
            field_section='finishing_options',
            order=2,
            section_order=2,
            help_text='Select the cover finish',
            options_data=[
                {'value': 'matte', 'label': 'Matte', 'price_modifier': 0},
                {'value': 'glossy', 'label': 'Glossy', 'price_modifier': 20},
            ]
        )

        # Copies
        self.create_field(
            product=product,
            field_name='copies',
            field_label='Number of Copies',
            field_type='number',
            field_section='quantity_pricing',
            order=1,
            section_order=3,
            help_text='Minimum 25 copies required',
            min_value=25,
            max_value=10000,
            default_value='25',
            options_data=None
        )

    def add_business_card_fields(self, product):
        """Add business card fields"""
        # Printing Side
        self.create_field(
            product=product,
            field_name='printing_side',
            field_label='Printing Side',
            field_type='radio',
            field_section='printing_options',
            order=1,
            section_order=1,
            help_text='Select printing sides',
            options_data=[
                {'value': 'front', 'label': 'Front Only', 'price_modifier': 0},
                {'value': 'back', 'label': 'Back Only', 'price_modifier': 0},
                {'value': 'both', 'label': 'Both Sides', 'price_modifier': 50},
            ]
        )

        # Lamination
        self.create_field(
            product=product,
            field_name='lamination',
            field_label='Lamination',
            field_type='radio',
            field_section='finishing_options',
            order=1,
            section_order=2,
            help_text='Select lamination finish',
            options_data=[
                {'value': 'none', 'label': 'No Lamination', 'price_modifier': 0},
                {'value': 'matte', 'label': 'Matte Lamination', 'price_modifier': 20},
                {'value': 'glossy', 'label': 'Glossy Lamination', 'price_modifier': 25},
            ]
        )

        # Quantity
        self.create_field(
            product=product,
            field_name='quantity',
            field_label='Quantity',
            field_type='select',
            field_section='quantity_pricing',
            order=1,
            section_order=3,
            help_text='Select quantity (includes tiered pricing)',
            options_data=[
                {'value': '100', 'label': '100 Cards - ₹340', 'price_modifier': 340},
                {'value': '200', 'label': '200 Cards - ₹666', 'price_modifier': 666},
                {'value': '500', 'label': '500 Cards - ₹1,564', 'price_modifier': 1564},
                {'value': '1000', 'label': '1000 Cards - ₹2,788', 'price_modifier': 2788},
            ]
        )

    def add_letterhead_fields(self, product):
        """Add letterhead fields"""
        # Paper Type
        self.create_field(
            product=product,
            field_name='paper_type',
            field_label='Paper Type',
            field_type='radio',
            field_section='product_specs',
            order=1,
            section_order=1,
            help_text='Select paper type for letterhead',
            options_data=[
                {'value': 'jk_excel_bond', 'label': 'JK Excel Bond Paper 100 GSM', 'price_modifier': 0},
                {'value': 'do_paper_100gsm', 'label': 'Do Paper 100 GSM', 'price_modifier': 20},
            ]
        )

        # Quantity
        self.create_field(
            product=product,
            field_name='quantity',
            field_label='Quantity',
            field_type='select',
            field_section='quantity_pricing',
            order=1,
            section_order=2,
            help_text='Select quantity (2 Business Days delivery)',
            options_data=[
                {'value': '200', 'label': '200 Letterheads - ₹840', 'price_modifier': 840},
                {'value': '400', 'label': '400 Letterheads - ₹1,596', 'price_modifier': 1596},
                {'value': '500', 'label': '500 Letterheads - ₹1,932', 'price_modifier': 1932},
                {'value': '1000', 'label': '1000 Letterheads - ₹3,360', 'price_modifier': 3360},
            ]
        )

    def add_document_fields(self, product):
        """Add document printing fields (similar to book but simpler)"""
        # Interior Color
        self.create_field(
            product=product,
            field_name='interior_color',
            field_label='Interior Color',
            field_type='radio',
            field_section='printing_options',
            order=1,
            section_order=1,
            help_text='Select the color option for your document',
            options_data=[
                {'value': 'bw', 'label': 'Black & White', 'price_modifier': 0},
                {'value': 'color', 'label': 'Color', 'price_modifier': 100},
            ]
        )

        # Document Size
        self.create_field(
            product=product,
            field_name='document_size',
            field_label='Document Size',
            field_type='select',
            field_section='product_specs',
            order=1,
            section_order=1,
            help_text='Select the document size',
            options_data=[
                {'value': 'a4', 'label': 'A4', 'price_modifier': 0},
                {'value': 'legal', 'label': 'Legal', 'price_modifier': 10},
                {'value': 'a3', 'label': 'A3', 'price_modifier': 25},
            ]
        )

        # Page Count
        self.create_field(
            product=product,
            field_name='page_count',
            field_label='Page Count',
            field_type='number',
            field_section='product_specs',
            order=2,
            section_order=1,
            help_text='Total number of pages',
            min_value=1,
            max_value=1000,
            default_value='10',
            options_data=None
        )

        # Copies
        self.create_field(
            product=product,
            field_name='copies',
            field_label='Number of Copies',
            field_type='number',
            field_section='quantity_pricing',
            order=1,
            section_order=3,
            help_text='Number of copies required',
            min_value=1,
            max_value=10000,
            default_value='25',
            options_data=None
        )

    def add_generic_fields(self, product):
        """Add generic fields for other products"""
        # Size
        self.create_field(
            product=product,
            field_name='size',
            field_label='Size',
            field_type='select',
            field_section='product_specs',
            order=1,
            section_order=1,
            help_text='Select the size',
            options_data=[
                {'value': 'a4', 'label': 'A4', 'price_modifier': 0},
                {'value': 'a5', 'label': 'A5', 'price_modifier': -15},
                {'value': 'a3', 'label': 'A3', 'price_modifier': 25},
                {'value': 'custom', 'label': 'Custom Size', 'price_modifier': 50},
            ]
        )

        # Color
        self.create_field(
            product=product,
            field_name='color_option',
            field_label='Color Options',
            field_type='radio',
            field_section='printing_options',
            order=1,
            section_order=2,
            help_text='Select printing color option',
            options_data=[
                {'value': 'bw', 'label': 'Black & White', 'price_modifier': 0},
                {'value': 'full_color', 'label': 'Full Color', 'price_modifier': 100},
            ]
        )

        # Quantity
        self.create_field(
            product=product,
            field_name='quantity',
            field_label='Quantity',
            field_type='number',
            field_section='quantity_pricing',
            order=1,
            section_order=3,
            help_text='Number of copies required',
            min_value=1,
            max_value=10000,
            default_value='100',
            options_data=None
        )