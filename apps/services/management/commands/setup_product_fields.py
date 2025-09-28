from django.core.management.base import BaseCommand
from django.db import transaction
from apps.services.models import StaticProduct, ProductFormField, ServiceCategory
import json

class Command(BaseCommand):
    help = 'Setup product-specific form fields based on requirements'

    def add_arguments(self, parser):
        parser.add_argument(
            '--product-type',
            type=str,
            choices=['book_printing', 'document_printing', 'business_cards', 'letter_head', 'all'],
            default='all',
            help='Specify which product type to setup'
        )

    def handle(self, *args, **options):
        product_type = options['product_type']

        if product_type == 'all':
            self.setup_all_products()
        else:
            self.setup_specific_product(product_type)

        self.stdout.write(
            self.style.SUCCESS(f'Successfully setup fields for {product_type}')
        )

    @transaction.atomic
    def setup_all_products(self):
        """Setup fields for all product types"""
        self.setup_book_printing()
        self.setup_document_printing()
        self.setup_business_cards()
        self.setup_letter_head()

    def setup_specific_product(self, product_type):
        """Setup fields for a specific product type"""
        setup_methods = {
            'book_printing': self.setup_book_printing,
            'document_printing': self.setup_document_printing,
            'business_cards': self.setup_business_cards,
            'letter_head': self.setup_letter_head,
        }

        method = setup_methods.get(product_type)
        if method:
            method()

    def get_or_create_product(self, name, category_name, description, short_description):
        """Get or create a static product"""
        category, _ = ServiceCategory.objects.get_or_create(
            name=category_name,
            defaults={'description': f'{category_name} services'}
        )

        product, created = StaticProduct.objects.get_or_create(
            name=name,
            defaults={
                'category': category,
                'description': description,
                'short_description': short_description,
                'base_price': 100.00,
                'price_unit': 'per piece'
            }
        )
        return product

    def create_field(self, product, field_name, field_label, field_type, options_data, **kwargs):
        """Create or update a product form field"""
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

        action = "Created" if created else "Updated"
        self.stdout.write(f"  {action} field: {field_label}")
        return field

    def setup_book_printing(self):
        """Setup Book Printing product fields"""
        self.stdout.write("Setting up Book Printing fields...")

        product = self.get_or_create_product(
            name="Book Printing",
            category_name="Printing Services",
            description="Professional book printing services with various binding and finishing options",
            short_description="High-quality book printing with custom specifications"
        )

        # 1. Interior Color (Radio buttons)
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
                {'value': 'bw_premium', 'label': 'Black & White Premium', 'price_modifier': 0, 'description': 'High-quality black and white printing'},
                {'value': 'bw_standard', 'label': 'Black & White Standard', 'price_modifier': -20, 'description': 'Standard black and white printing'},
                {'value': 'color_premium', 'label': 'Color Premium', 'price_modifier': 150, 'description': 'Premium full-color printing'},
                {'value': 'color_standard', 'label': 'Color Standard', 'price_modifier': 100, 'description': 'Standard full-color printing'},
                {'value': 'combine_color', 'label': 'Combined Color', 'price_modifier': 75, 'description': 'Mix of black & white and color pages'},
            ]
        )

        # 2. Page Count (conditional on interior color)
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

        # 3. Black & White Page Count (conditional)
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

        # 4. Color Page Count (conditional)
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

        # 5. Book Size
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

        # 6. Paper Type
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

        # 7. Binding Type
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

        # 8. Cover Finish
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
                {'value': 'glossy', 'label': 'Glossy', 'price_modifier': 20},
                {'value': 'matte', 'label': 'Matte', 'price_modifier': 0},
            ]
        )

        # 9. Design and Formatting
        self.create_field(
            product=product,
            field_name='design_service',
            field_label='Design and Formatting',
            field_type='radio',
            field_section='additional_services',
            order=1,
            section_order=3,
            help_text='Do you need design and formatting services?',
            options_data=[
                {'value': 'not_required', 'label': 'Not Required', 'price_modifier': 0},
                {'value': 'yes_required', 'label': 'Yes, Please Design (₹1500 per cover + ₹50 per inner page)', 'price_modifier': 1500},
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
            section_order=3,
            help_text='Do you need ISBN allocation?',
            options_data=[
                {'value': 'not_apply', 'label': 'Not Required', 'price_modifier': 0},
                {'value': 'yes_assign', 'label': 'Yes, assign a unique ISBN number', 'price_modifier': 500},
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
            section_order=4,
            help_text='Minimum 25 copies required',
            min_value=25,
            max_value=10000,
            default_value='25',
            options_data=None
        )

    def setup_document_printing(self):
        """Setup Document Printing product fields"""
        self.stdout.write("Setting up Document Printing fields...")

        product = self.get_or_create_product(
            name="Document Printing",
            category_name="Printing Services",
            description="Professional document printing services for reports, presentations, and business documents",
            short_description="High-quality document printing with various binding options"
        )

        # 1. Interior Color
        self.create_field(
            product=product,
            field_name='interior_color',
            field_label='Interior Color',
            field_type='radio',
            field_section='printing_options',
            order=1,
            section_order=1,
            help_text='Select the color option for your document',
            triggers_fields=json.dumps(['bw_page_count', 'color_page_count']),
            options_data=[
                {'value': 'bw', 'label': 'Black & White', 'price_modifier': 0},
                {'value': 'color', 'label': 'Color', 'price_modifier': 100},
                {'value': 'combine_color', 'label': 'Combined Color', 'price_modifier': 50},
            ]
        )

        # 2. Document Size
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

        # 3. Page Count fields (similar to book printing)
        self.create_field(
            product=product,
            field_name='page_count',
            field_label='Total Page Count',
            field_type='number',
            field_section='product_specs',
            order=2,
            section_order=1,
            help_text='Total number of pages in your document',
            min_value=1,
            max_value=1000,
            default_value='10',
            show_condition=json.dumps({'field': 'interior_color', 'value': 'combine_color', 'operator': 'not_equals'}),
            options_data=None
        )

        # Conditional page counts for combined color
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

        # 4. Paper Type
        self.create_field(
            product=product,
            field_name='paper_type',
            field_label='Paper Type',
            field_type='select',
            field_section='product_specs',
            order=5,
            section_order=1,
            help_text='Select the paper quality',
            options_data=[
                {'value': '75gsm', 'label': '75 GSM', 'price_modifier': 0},
                {'value': '100gsm', 'label': '100 GSM', 'price_modifier': 15},
            ]
        )

        # 5. Binding Type
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
                {'value': 'spiral_binding', 'label': 'Spiral Binding', 'price_modifier': 20},
                {'value': 'paperback', 'label': 'Paperback (Perfect)', 'price_modifier': 35},
                {'value': 'hardcover', 'label': 'Hardcover', 'price_modifier': 100},
            ]
        )

        # 6. Cover Finish
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
                {'value': 'glossy', 'label': 'Glossy', 'price_modifier': 15},
                {'value': 'matte', 'label': 'Matte', 'price_modifier': 0},
            ]
        )

        # 7. File Upload Section
        self.create_field(
            product=product,
            field_name='cover_file',
            field_label='Upload Cover Page',
            field_type='file',
            field_section='file_uploads',
            order=1,
            section_order=3,
            help_text='Upload your cover page (PDF, Word, or Excel file)',
            is_required=False,
            options_data=None
        )

        self.create_field(
            product=product,
            field_name='inner_file',
            field_label='Upload Inner Pages',
            field_type='file',
            field_section='file_uploads',
            order=2,
            section_order=3,
            help_text='Upload your inner pages (PDF, Word, or Excel file)',
            options_data=None
        )

        # 8. Number of Copies
        self.create_field(
            product=product,
            field_name='copies',
            field_label='Number of Copies',
            field_type='number',
            field_section='quantity_pricing',
            order=1,
            section_order=4,
            help_text='Minimum 25 copies required',
            min_value=25,
            max_value=10000,
            default_value='25',
            options_data=None
        )

    def setup_business_cards(self):
        """Setup Business Cards product fields"""
        self.stdout.write("Setting up Business Cards fields...")

        product = self.get_or_create_product(
            name="Business Cards",
            category_name="Marketing Materials",
            description="Professional business card printing with premium finishes and quick turnaround",
            short_description="High-quality business cards with various finish options"
        )

        # 1. Printing Side
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

        # 2. Lamination
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
                {'value': 'matte', 'label': 'Matte Lamination', 'price_modifier': 20},
                {'value': 'glossy', 'label': 'Glossy Lamination', 'price_modifier': 25},
                {'value': 'none', 'label': 'No Lamination', 'price_modifier': 0},
            ]
        )

        # 3. Quantity with tiered pricing
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
                {'value': '100', 'label': '100 Cards - ₹340 (Standard) / ₹290 (Express)', 'price_modifier': 340, 'rush_modifier': 290},
                {'value': '200', 'label': '200 Cards - ₹666 (Standard) / ₹568 (Express)', 'price_modifier': 666, 'rush_modifier': 568},
                {'value': '300', 'label': '300 Cards - ₹979 (Standard) / ₹835 (Express)', 'price_modifier': 979, 'rush_modifier': 835},
                {'value': '400', 'label': '400 Cards - ₹1,278 (Standard) / ₹1,090 (Express)', 'price_modifier': 1278, 'rush_modifier': 1090},
                {'value': '500', 'label': '500 Cards - ₹1,564 (Standard) / ₹1,334 (Express)', 'price_modifier': 1564, 'rush_modifier': 1334},
                {'value': '600', 'label': '600 Cards - ₹1,836 (Standard) / ₹1,566 (Express)', 'price_modifier': 1836, 'rush_modifier': 1566},
                {'value': '700', 'label': '700 Cards - ₹2,094 (Standard) / ₹1,786 (Express)', 'price_modifier': 2094, 'rush_modifier': 1786},
                {'value': '800', 'label': '800 Cards - ₹2,339 (Standard) / ₹1,995 (Express)', 'price_modifier': 2339, 'rush_modifier': 1995},
                {'value': '900', 'label': '900 Cards - ₹2,570 (Standard) / ₹2,192 (Express)', 'price_modifier': 2570, 'rush_modifier': 2192},
                {'value': '1000', 'label': '1000 Cards - ₹2,788 (Standard) / ₹2,378 (Express)', 'price_modifier': 2788, 'rush_modifier': 2378},
                {'value': '1500', 'label': '1500 Cards - ₹3,672 (Standard) / ₹3,132 (Express)', 'price_modifier': 3672, 'rush_modifier': 3132},
                {'value': '2000', 'label': '2000 Cards - ₹4,216 (Standard) / ₹3,596 (Express)', 'price_modifier': 4216, 'rush_modifier': 3596},
            ]
        )

        # 4. Delivery Time
        self.create_field(
            product=product,
            field_name='delivery_time',
            field_label='Delivery Time',
            field_type='radio',
            field_section='additional_services',
            order=1,
            section_order=4,
            help_text='Select delivery timeframe',
            options_data=[
                {'value': 'standard', 'label': '4 Business Days (Standard Pricing)', 'price_modifier': 0},
                {'value': 'express', 'label': '2 Business Days (Express Pricing)', 'price_modifier': 0, 'use_rush_pricing': True},
            ]
        )

    def setup_letter_head(self):
        """Setup Letter Head product fields"""
        self.stdout.write("Setting up Letter Head fields...")

        product = self.get_or_create_product(
            name="Letter Head",
            category_name="Business Stationery",
            description="Professional letterhead printing on premium paper with custom designs",
            short_description="High-quality letterhead printing for professional correspondence"
        )

        # 1. Paper Type
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

        # 2. Quantity with tiered pricing
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
                {'value': '200', 'label': '200 Letterheads - ₹840 (₹4.20 per item)', 'price_modifier': 840},
                {'value': '400', 'label': '400 Letterheads - ₹1,596 (₹3.99 per item)', 'price_modifier': 1596},
                {'value': '500', 'label': '500 Letterheads - ₹1,932 (₹3.86 per item)', 'price_modifier': 1932},
                {'value': '800', 'label': '800 Letterheads - ₹2,856 (₹3.57 per item)', 'price_modifier': 2856},
                {'value': '1000', 'label': '1000 Letterheads - ₹3,360 (₹3.36 per item)', 'price_modifier': 3360},
                {'value': '1500', 'label': '1500 Letterheads - ₹4,725 (₹3.15 per item)', 'price_modifier': 4725},
            ]
        )

        # 3. Custom Quantity Option
        self.create_field(
            product=product,
            field_name='custom_quantity',
            field_label='Custom Quantity',
            field_type='number',
            field_section='quantity_pricing',
            order=2,
            section_order=2,
            help_text='Enter custom quantity if not listed above (leave blank if using preset quantities)',
            min_value=100,
            max_value=10000,
            is_required=False,
            options_data=None
        )