# apps/services/management/commands/analyze_and_create_pricing.py
from django.core.management.base import BaseCommand
from apps.services.models import Product, ProductFormField, ProductPricing
import json


class Command(BaseCommand):
    help = 'Analyze and create comprehensive pricing system based on Indian market research'

    def handle(self, *args, **options):
        # Clear existing form fields and pricing
        self.stdout.write(self.style.WARNING('Clearing existing form fields and pricing...'))
        ProductFormField.objects.all().delete()
        ProductPricing.objects.all().delete()
        
        # Comprehensive product analysis based on Indian printing market
        product_configs = {
            # BOOK PRINTING PRODUCTS
            'book_printing': {
                'products': ['Annual Reports', 'Art Book Printing', 'Children\'s Book Printing', 
                           'Coffee Table Books', 'Coloring Book Printing', 'Comic Book Printing', 
                           'On Demand Books', 'Year Book Printing'],
                'form_fields': [
                    {
                        'field_name': 'quantity',
                        'field_label': 'Quantity',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': '25', 'label': '25 Books', 'price_modifier': 0},
                            {'value': '50', 'label': '50 Books', 'price_modifier': 0},
                            {'value': '100', 'label': '100 Books', 'price_modifier': -0.05},
                            {'value': '250', 'label': '250 Books', 'price_modifier': -0.10},
                            {'value': '500', 'label': '500 Books', 'price_modifier': -0.15},
                            {'value': '1000', 'label': '1000 Books', 'price_modifier': -0.20},
                            {'value': '2500', 'label': '2500 Books', 'price_modifier': -0.25},
                            {'value': '5000', 'label': '5000 Books', 'price_modifier': -0.30},
                        ]),
                        'default_value': '100',
                        'order': 1,
                        'is_required': True,
                    },
                    {
                        'field_name': 'book_size',
                        'field_label': 'Book Size',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': 'A5', 'label': 'A5 (148 x 210 mm)', 'price_modifier': 0},
                            {'value': 'A4', 'label': 'A4 (210 x 297 mm)', 'price_modifier': 50},
                            {'value': '6x9', 'label': '6" x 9" (152 x 229 mm)', 'price_modifier': 25},
                            {'value': '8.5x11', 'label': '8.5" x 11" (216 x 279 mm)', 'price_modifier': 75},
                            {'value': 'custom', 'label': 'Custom Size', 'price_modifier': 100},
                        ]),
                        'default_value': 'A5',
                        'order': 2,
                        'is_required': True,
                    },
                    {
                        'field_name': 'page_count',
                        'field_label': 'Number of Pages',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': '24', 'label': '24 Pages', 'price_modifier': 0},
                            {'value': '32', 'label': '32 Pages', 'price_modifier': 50},
                            {'value': '48', 'label': '48 Pages', 'price_modifier': 100},
                            {'value': '64', 'label': '64 Pages', 'price_modifier': 150},
                            {'value': '80', 'label': '80 Pages', 'price_modifier': 200},
                            {'value': '100', 'label': '100 Pages', 'price_modifier': 250},
                            {'value': '128', 'label': '128 Pages', 'price_modifier': 300},
                            {'value': '150', 'label': '150 Pages', 'price_modifier': 375},
                            {'value': '200', 'label': '200 Pages', 'price_modifier': 500},
                            {'value': '250', 'label': '250 Pages', 'price_modifier': 625},
                            {'value': '300', 'label': '300 Pages', 'price_modifier': 750},
                        ]),
                        'default_value': '100',
                        'order': 3,
                        'is_required': True,
                    },
                    {
                        'field_name': 'paper_type_inner',
                        'field_label': 'Inner Pages Paper',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': '70gsm_offset', 'label': '70 GSM Offset Paper', 'price_modifier': 0},
                            {'value': '80gsm_offset', 'label': '80 GSM Offset Paper', 'price_modifier': 25},
                            {'value': '90gsm_offset', 'label': '90 GSM Offset Paper', 'price_modifier': 50},
                            {'value': '100gsm_art', 'label': '100 GSM Art Paper', 'price_modifier': 100},
                            {'value': '130gsm_art', 'label': '130 GSM Art Paper', 'price_modifier': 150},
                        ]),
                        'default_value': '70gsm_offset',
                        'order': 4,
                        'is_required': True,
                    },
                    {
                        'field_name': 'inner_printing',
                        'field_label': 'Inner Pages Printing',
                        'field_type': 'radio',
                        'options': json.dumps([
                            {'value': 'bw', 'label': 'Black & White', 'price_modifier': 0},
                            {'value': 'color', 'label': 'Full Color (4+4)', 'price_modifier': 200},
                            {'value': 'mixed', 'label': 'Mixed (Some B&W, Some Color)', 'price_modifier': 100},
                        ]),
                        'default_value': 'bw',
                        'order': 5,
                        'is_required': True,
                    },
                    {
                        'field_name': 'cover_paper',
                        'field_label': 'Cover Paper',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': '250gsm_art', 'label': '250 GSM Art Card', 'price_modifier': 0},
                            {'value': '300gsm_art', 'label': '300 GSM Art Card', 'price_modifier': 50},
                            {'value': '350gsm_art', 'label': '350 GSM Art Card', 'price_modifier': 100},
                            {'value': '250gsm_duplex', 'label': '250 GSM Duplex Board', 'price_modifier': 25},
                            {'value': '300gsm_duplex', 'label': '300 GSM Duplex Board', 'price_modifier': 75},
                        ]),
                        'default_value': '250gsm_art',
                        'order': 6,
                        'is_required': True,
                    },
                    {
                        'field_name': 'cover_printing',
                        'field_label': 'Cover Printing',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': 'color_4_0', 'label': 'Full Color Front Only (4+0)', 'price_modifier': 0},
                            {'value': 'color_4_4', 'label': 'Full Color Both Sides (4+4)', 'price_modifier': 100},
                            {'value': 'color_4_1', 'label': 'Color Front + Black Back (4+1)', 'price_modifier': 50},
                        ]),
                        'default_value': 'color_4_0',
                        'order': 7,
                        'is_required': True,
                    },
                    {
                        'field_name': 'binding_type',
                        'field_label': 'Binding Type',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': 'saddle_stitch', 'label': 'Saddle Stitching', 'price_modifier': 0},
                            {'value': 'perfect_binding', 'label': 'Perfect Binding', 'price_modifier': 150},
                            {'value': 'spiral_binding', 'label': 'Spiral Binding', 'price_modifier': 100},
                            {'value': 'case_binding', 'label': 'Case Binding (Hardcover)', 'price_modifier': 500},
                            {'value': 'thread_sewing', 'label': 'Thread Sewing + Perfect Binding', 'price_modifier': 250},
                        ]),
                        'default_value': 'perfect_binding',
                        'order': 8,
                        'is_required': True,
                    },
                    {
                        'field_name': 'cover_finish',
                        'field_label': 'Cover Finishing',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': 'matte', 'label': 'Matte Finish', 'price_modifier': 0},
                            {'value': 'gloss', 'label': 'Gloss Lamination', 'price_modifier': 75},
                            {'value': 'matte_lam', 'label': 'Matte Lamination', 'price_modifier': 75},
                            {'value': 'spot_uv', 'label': 'Spot UV', 'price_modifier': 200},
                            {'value': 'foiling', 'label': 'Gold/Silver Foiling', 'price_modifier': 300},
                            {'value': 'embossing', 'label': 'Embossing', 'price_modifier': 250},
                        ]),
                        'default_value': 'matte_lam',
                        'order': 9,
                        'is_required': True,
                    },
                    {
                        'field_name': 'design_service',
                        'field_label': 'Design & Formatting Service',
                        'field_type': 'checkbox',
                        'options': json.dumps([
                            {'value': 'basic', 'label': 'Basic Design Service (+₹2,500)', 'price_modifier': 2500},
                            {'value': 'premium', 'label': 'Premium Design Service (+₹5,000)', 'price_modifier': 5000},
                            {'value': 'formatting', 'label': 'Text Formatting Only (+₹1,500)', 'price_modifier': 1500},
                        ]),
                        'order': 10,
                        'is_required': False,
                    },
                    {
                        'field_name': 'isbn_service',
                        'field_label': 'ISBN & Legal Services',
                        'field_type': 'checkbox',
                        'options': json.dumps([
                            {'value': 'isbn', 'label': 'ISBN Allocation (+₹500)', 'price_modifier': 500},
                            {'value': 'barcode', 'label': 'Barcode Generation (+₹200)', 'price_modifier': 200},
                            {'value': 'copyright', 'label': 'Copyright Registration (+₹2,000)', 'price_modifier': 2000},
                        ]),
                        'order': 11,
                        'is_required': False,
                    },
                ],
                'base_price': 150,  # Base price per book
            },
            
            # DOCUMENT PRINTING
            'document_printing': {
                'products': ['Document Printing', 'Bill Book'],
                'form_fields': [
                    {
                        'field_name': 'quantity',
                        'field_label': 'Quantity',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': '100', 'label': '100 Copies', 'price_modifier': 0},
                            {'value': '250', 'label': '250 Copies', 'price_modifier': -0.05},
                            {'value': '500', 'label': '500 Copies', 'price_modifier': -0.10},
                            {'value': '1000', 'label': '1000 Copies', 'price_modifier': -0.15},
                            {'value': '2500', 'label': '2500 Copies', 'price_modifier': -0.20},
                            {'value': '5000', 'label': '5000 Copies', 'price_modifier': -0.25},
                        ]),
                        'default_value': '500',
                        'order': 1,
                        'is_required': True,
                    },
                    {
                        'field_name': 'paper_size',
                        'field_label': 'Paper Size',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': 'A4', 'label': 'A4 (210 x 297 mm)', 'price_modifier': 0},
                            {'value': 'A3', 'label': 'A3 (297 x 420 mm)', 'price_modifier': 100},
                            {'value': 'A5', 'label': 'A5 (148 x 210 mm)', 'price_modifier': -25},
                            {'value': 'legal', 'label': 'Legal Size (216 x 356 mm)', 'price_modifier': 50},
                            {'value': 'letter', 'label': 'Letter Size (216 x 279 mm)', 'price_modifier': 25},
                        ]),
                        'default_value': 'A4',
                        'order': 2,
                        'is_required': True,
                    },
                    {
                        'field_name': 'paper_type',
                        'field_label': 'Paper Type',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': '70gsm', 'label': '70 GSM Copier Paper', 'price_modifier': 0},
                            {'value': '80gsm', 'label': '80 GSM Bond Paper', 'price_modifier': 25},
                            {'value': '90gsm', 'label': '90 GSM Premium Paper', 'price_modifier': 50},
                            {'value': '100gsm', 'label': '100 GSM Art Paper', 'price_modifier': 100},
                        ]),
                        'default_value': '70gsm',
                        'order': 3,
                        'is_required': True,
                    },
                    {
                        'field_name': 'printing_type',
                        'field_label': 'Printing Type',
                        'field_type': 'radio',
                        'options': json.dumps([
                            {'value': 'bw_single', 'label': 'Black & White Single Side', 'price_modifier': 0},
                            {'value': 'bw_double', 'label': 'Black & White Double Side', 'price_modifier': 50},
                            {'value': 'color_single', 'label': 'Full Color Single Side', 'price_modifier': 200},
                            {'value': 'color_double', 'label': 'Full Color Double Side', 'price_modifier': 350},
                        ]),
                        'default_value': 'bw_single',
                        'order': 4,
                        'is_required': True,
                    },
                    {
                        'field_name': 'binding_option',
                        'field_label': 'Binding/Finishing',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': 'loose', 'label': 'Loose Sheets', 'price_modifier': 0},
                            {'value': 'staple', 'label': 'Staple Binding', 'price_modifier': 25},
                            {'value': 'spiral', 'label': 'Spiral Binding', 'price_modifier': 100},
                            {'value': 'folder', 'label': 'File Folder', 'price_modifier': 150},
                        ]),
                        'default_value': 'loose',
                        'order': 5,
                        'is_required': True,
                    },
                ],
                'base_price': 2,  # Base price per page
            },
            
            # BUSINESS CARDS
            'business_cards': {
                'products': ['Business Cards'],
                'form_fields': [
                    {
                        'field_name': 'quantity',
                        'field_label': 'Quantity',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': '100', 'label': '100 Cards', 'price_modifier': 0},
                            {'value': '250', 'label': '250 Cards', 'price_modifier': -0.10},
                            {'value': '500', 'label': '500 Cards', 'price_modifier': -0.20},
                            {'value': '1000', 'label': '1000 Cards', 'price_modifier': -0.30},
                            {'value': '2500', 'label': '2500 Cards', 'price_modifier': -0.35},
                            {'value': '5000', 'label': '5000 Cards', 'price_modifier': -0.40},
                        ]),
                        'default_value': '500',
                        'order': 1,
                        'is_required': True,
                    },
                    {
                        'field_name': 'card_size',
                        'field_label': 'Card Size',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': 'standard', 'label': 'Standard (90 x 54 mm)', 'price_modifier': 0},
                            {'value': 'mini', 'label': 'Mini (85 x 50 mm)', 'price_modifier': -25},
                            {'value': 'square', 'label': 'Square (70 x 70 mm)', 'price_modifier': 50},
                            {'value': 'folded', 'label': 'Folded (180 x 54 mm)', 'price_modifier': 100},
                        ]),
                        'default_value': 'standard',
                        'order': 2,
                        'is_required': True,
                    },
                    {
                        'field_name': 'paper_type',
                        'field_label': 'Paper Type',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': '300gsm_art', 'label': '300 GSM Art Card', 'price_modifier': 0},
                            {'value': '350gsm_art', 'label': '350 GSM Art Card', 'price_modifier': 50},
                            {'value': '400gsm_art', 'label': '400 GSM Art Card', 'price_modifier': 100},
                            {'value': '300gsm_duplex', 'label': '300 GSM Duplex Board', 'price_modifier': 25},
                            {'value': 'textured', 'label': 'Textured Paper', 'price_modifier': 150},
                            {'value': 'linen', 'label': 'Linen Finish', 'price_modifier': 200},
                        ]),
                        'default_value': '300gsm_art',
                        'order': 3,
                        'is_required': True,
                    },
                    {
                        'field_name': 'printing_sides',
                        'field_label': 'Printing Sides',
                        'field_type': 'radio',
                        'options': json.dumps([
                            {'value': 'single', 'label': 'Single Side (4+0)', 'price_modifier': 0},
                            {'value': 'double', 'label': 'Double Side (4+4)', 'price_modifier': 100},
                        ]),
                        'default_value': 'double',
                        'order': 4,
                        'is_required': True,
                    },
                    {
                        'field_name': 'finishing',
                        'field_label': 'Finishing Options',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': 'matte', 'label': 'Matte Finish', 'price_modifier': 0},
                            {'value': 'gloss_lam', 'label': 'Gloss Lamination', 'price_modifier': 150},
                            {'value': 'matte_lam', 'label': 'Matte Lamination', 'price_modifier': 150},
                            {'value': 'spot_uv', 'label': 'Spot UV', 'price_modifier': 300},
                            {'value': 'foiling', 'label': 'Gold/Silver Foiling', 'price_modifier': 500},
                            {'value': 'embossing', 'label': 'Embossing', 'price_modifier': 400},
                        ]),
                        'default_value': 'matte_lam',
                        'order': 5,
                        'is_required': True,
                    },
                    {
                        'field_name': 'design_service',
                        'field_label': 'Design Service',
                        'field_type': 'checkbox',
                        'options': json.dumps([
                            {'value': 'basic', 'label': 'Basic Design (+₹500)', 'price_modifier': 500},
                            {'value': 'premium', 'label': 'Premium Design (+₹1,500)', 'price_modifier': 1500},
                        ]),
                        'order': 6,
                        'is_required': False,
                    },
                ],
                'base_price': 8,  # Base price per card
            },
            
            # LETTERHEADS
            'letterheads': {
                'products': ['Letter Head'],
                'form_fields': [
                    {
                        'field_name': 'quantity',
                        'field_label': 'Quantity',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': '100', 'label': '100 Letterheads', 'price_modifier': 0},
                            {'value': '250', 'label': '250 Letterheads', 'price_modifier': -0.10},
                            {'value': '500', 'label': '500 Letterheads', 'price_modifier': -0.15},
                            {'value': '1000', 'label': '1000 Letterheads', 'price_modifier': -0.20},
                            {'value': '2500', 'label': '2500 Letterheads', 'price_modifier': -0.25},
                        ]),
                        'default_value': '500',
                        'order': 1,
                        'is_required': True,
                    },
                    {
                        'field_name': 'paper_size',
                        'field_label': 'Paper Size',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': 'A4', 'label': 'A4 (210 x 297 mm)', 'price_modifier': 0},
                            {'value': 'A5', 'label': 'A5 (148 x 210 mm)', 'price_modifier': -25},
                            {'value': 'letter', 'label': 'Letter Size (216 x 279 mm)', 'price_modifier': 25},
                        ]),
                        'default_value': 'A4',
                        'order': 2,
                        'is_required': True,
                    },
                    {
                        'field_name': 'paper_type',
                        'field_label': 'Paper Quality',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': '80gsm_bond', 'label': '80 GSM Bond Paper', 'price_modifier': 0},
                            {'value': '90gsm_bond', 'label': '90 GSM Bond Paper', 'price_modifier': 50},
                            {'value': '100gsm_bond', 'label': '100 GSM Bond Paper', 'price_modifier': 100},
                            {'value': '120gsm_bond', 'label': '120 GSM Bond Paper', 'price_modifier': 150},
                            {'value': 'linen', 'label': 'Linen Finish Paper', 'price_modifier': 200},
                        ]),
                        'default_value': '80gsm_bond',
                        'order': 3,
                        'is_required': True,
                    },
                    {
                        'field_name': 'printing_type',
                        'field_label': 'Printing Type',
                        'field_type': 'radio',
                        'options': json.dumps([
                            {'value': 'single_color', 'label': 'Single Color', 'price_modifier': 0},
                            {'value': 'two_color', 'label': 'Two Color', 'price_modifier': 100},
                            {'value': 'full_color', 'label': 'Full Color (CMYK)', 'price_modifier': 200},
                        ]),
                        'default_value': 'full_color',
                        'order': 4,
                        'is_required': True,
                    },
                    {
                        'field_name': 'design_service',
                        'field_label': 'Design Service',
                        'field_type': 'checkbox',
                        'options': json.dumps([
                            {'value': 'design', 'label': 'Professional Design (+₹1,000)', 'price_modifier': 1000},
                        ]),
                        'order': 5,
                        'is_required': False,
                    },
                ],
                'base_price': 5,  # Base price per letterhead
            },
            
            # BROCHURES & FLYERS
            'brochures_flyers': {
                'products': ['Brochures', 'Flyers', 'Catalogue'],
                'form_fields': [
                    {
                        'field_name': 'quantity',
                        'field_label': 'Quantity',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': '100', 'label': '100 Pieces', 'price_modifier': 0},
                            {'value': '250', 'label': '250 Pieces', 'price_modifier': -0.10},
                            {'value': '500', 'label': '500 Pieces', 'price_modifier': -0.15},
                            {'value': '1000', 'label': '1000 Pieces', 'price_modifier': -0.20},
                            {'value': '2500', 'label': '2500 Pieces', 'price_modifier': -0.25},
                            {'value': '5000', 'label': '5000 Pieces', 'price_modifier': -0.30},
                        ]),
                        'default_value': '500',
                        'order': 1,
                        'is_required': True,
                    },
                    {
                        'field_name': 'size',
                        'field_label': 'Size',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': 'A4', 'label': 'A4 (210 x 297 mm)', 'price_modifier': 0},
                            {'value': 'A5', 'label': 'A5 (148 x 210 mm)', 'price_modifier': -25},
                            {'value': 'A3', 'label': 'A3 (297 x 420 mm)', 'price_modifier': 100},
                            {'value': 'dl', 'label': 'DL (99 x 210 mm)', 'price_modifier': -50},
                            {'value': 'custom', 'label': 'Custom Size', 'price_modifier': 75},
                        ]),
                        'default_value': 'A4',
                        'order': 2,
                        'is_required': True,
                    },
                    {
                        'field_name': 'paper_type',
                        'field_label': 'Paper Type',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': '130gsm_art', 'label': '130 GSM Art Paper', 'price_modifier': 0},
                            {'value': '170gsm_art', 'label': '170 GSM Art Paper', 'price_modifier': 50},
                            {'value': '200gsm_art', 'label': '200 GSM Art Paper', 'price_modifier': 100},
                            {'value': '250gsm_art', 'label': '250 GSM Art Card', 'price_modifier': 150},
                            {'value': '300gsm_art', 'label': '300 GSM Art Card', 'price_modifier': 200},
                        ]),
                        'default_value': '170gsm_art',
                        'order': 3,
                        'is_required': True,
                    },
                    {
                        'field_name': 'folding',
                        'field_label': 'Folding Type',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': 'no_fold', 'label': 'No Folding (Flat)', 'price_modifier': 0},
                            {'value': 'half_fold', 'label': 'Half Fold', 'price_modifier': 50},
                            {'value': 'tri_fold', 'label': 'Tri-Fold', 'price_modifier': 100},
                            {'value': 'z_fold', 'label': 'Z-Fold', 'price_modifier': 100},
                            {'value': 'gate_fold', 'label': 'Gate Fold', 'price_modifier': 150},
                        ]),
                        'default_value': 'tri_fold',
                        'order': 4,
                        'is_required': True,
                    },
                    {
                        'field_name': 'printing_sides',
                        'field_label': 'Printing Sides',
                        'field_type': 'radio',
                        'options': json.dumps([
                            {'value': 'single', 'label': 'Single Side (4+0)', 'price_modifier': 0},
                            {'value': 'double', 'label': 'Double Side (4+4)', 'price_modifier': 150},
                        ]),
                        'default_value': 'double',
                        'order': 5,
                        'is_required': True,
                    },
                    {
                        'field_name': 'finishing',
                        'field_label': 'Finishing',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': 'matte', 'label': 'Matte Finish', 'price_modifier': 0},
                            {'value': 'gloss_lam', 'label': 'Gloss Lamination', 'price_modifier': 100},
                            {'value': 'matte_lam', 'label': 'Matte Lamination', 'price_modifier': 100},
                            {'value': 'spot_uv', 'label': 'Spot UV', 'price_modifier': 200},
                        ]),
                        'default_value': 'matte_lam',
                        'order': 6,
                        'is_required': True,
                    },
                ],
                'base_price': 12,  # Base price per piece
            },
            
            # STICKERS & LABELS
            'stickers': {
                'products': ['Sticker'],
                'form_fields': [
                    {
                        'field_name': 'quantity',
                        'field_label': 'Quantity',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': '100', 'label': '100 Stickers', 'price_modifier': 0},
                            {'value': '250', 'label': '250 Stickers', 'price_modifier': -0.15},
                            {'value': '500', 'label': '500 Stickers', 'price_modifier': -0.25},
                            {'value': '1000', 'label': '1000 Stickers', 'price_modifier': -0.35},
                            {'value': '2500', 'label': '2500 Stickers', 'price_modifier': -0.40},
                            {'value': '5000', 'label': '5000 Stickers', 'price_modifier': -0.45},
                        ]),
                        'default_value': '500',
                        'order': 1,
                        'is_required': True,
                    },
                    {
                        'field_name': 'size',
                        'field_label': 'Sticker Size',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': '25mm', 'label': '25mm Circle', 'price_modifier': 0},
                            {'value': '38mm', 'label': '38mm Circle', 'price_modifier': 25},
                            {'value': '50mm', 'label': '50mm Circle', 'price_modifier': 50},
                            {'value': '75mm', 'label': '75mm Circle', 'price_modifier': 100},
                            {'value': '50x25', 'label': '50x25mm Rectangle', 'price_modifier': 50},
                            {'value': '75x50', 'label': '75x50mm Rectangle', 'price_modifier': 100},
                            {'value': 'custom', 'label': 'Custom Size', 'price_modifier': 150},
                        ]),
                        'default_value': '50mm',
                        'order': 2,
                        'is_required': True,
                    },
                    {
                        'field_name': 'material',
                        'field_label': 'Material',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': 'vinyl', 'label': 'Vinyl Sticker', 'price_modifier': 0},
                            {'value': 'paper', 'label': 'Paper Sticker', 'price_modifier': -25},
                            {'value': 'transparent', 'label': 'Transparent Vinyl', 'price_modifier': 50},
                            {'value': 'holographic', 'label': 'Holographic', 'price_modifier': 100},
                            {'value': 'waterproof', 'label': 'Waterproof Vinyl', 'price_modifier': 75},
                        ]),
                        'default_value': 'vinyl',
                        'order': 3,
                        'is_required': True,
                    },
                    {
                        'field_name': 'cutting',
                        'field_label': 'Cutting Type',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': 'kiss_cut', 'label': 'Kiss Cut (Easy Peel)', 'price_modifier': 0},
                            {'value': 'die_cut', 'label': 'Die Cut (Custom Shape)', 'price_modifier': 100},
                        ]),
                        'default_value': 'kiss_cut',
                        'order': 4,
                        'is_required': True,
                    },
                ],
                'base_price': 3,  # Base price per sticker
            },
            
            # PACKAGING BOXES
            'packaging_boxes': {
                'products': ['Paper Boxes', 'Corrugated Boxes', 'Folding Carton Boxes', 
                           'Kraft Boxes', 'Cosmetic Paper Boxes', 'Medical Paper Boxes', 'Retail Paper Boxes'],
                'form_fields': [
                    {
                        'field_name': 'quantity',
                        'field_label': 'Quantity',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': '50', 'label': '50 Boxes', 'price_modifier': 0},
                            {'value': '100', 'label': '100 Boxes', 'price_modifier': -0.10},
                            {'value': '250', 'label': '250 Boxes', 'price_modifier': -0.20},
                            {'value': '500', 'label': '500 Boxes', 'price_modifier': -0.30},
                            {'value': '1000', 'label': '1000 Boxes', 'price_modifier': -0.35},
                            {'value': '2500', 'label': '2500 Boxes', 'price_modifier': -0.40},
                        ]),
                        'default_value': '250',
                        'order': 1,
                        'is_required': True,
                    },
                    {
                        'field_name': 'box_size',
                        'field_label': 'Box Size (L x W x H)',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': '10x10x5', 'label': '10 x 10 x 5 cm', 'price_modifier': 0},
                            {'value': '15x15x8', 'label': '15 x 15 x 8 cm', 'price_modifier': 50},
                            {'value': '20x20x10', 'label': '20 x 20 x 10 cm', 'price_modifier': 100},
                            {'value': '25x25x12', 'label': '25 x 25 x 12 cm', 'price_modifier': 150},
                            {'value': '30x30x15', 'label': '30 x 30 x 15 cm', 'price_modifier': 200},
                            {'value': 'custom', 'label': 'Custom Size', 'price_modifier': 250},
                        ]),
                        'default_value': '15x15x8',
                        'order': 2,
                        'is_required': True,
                    },
                    {
                        'field_name': 'material',
                        'field_label': 'Material',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': '300gsm_duplex', 'label': '300 GSM Duplex Board', 'price_modifier': 0},
                            {'value': '350gsm_duplex', 'label': '350 GSM Duplex Board', 'price_modifier': 50},
                            {'value': '400gsm_duplex', 'label': '400 GSM Duplex Board', 'price_modifier': 100},
                            {'value': 'corrugated_3ply', 'label': '3-Ply Corrugated', 'price_modifier': 75},
                            {'value': 'corrugated_5ply', 'label': '5-Ply Corrugated', 'price_modifier': 150},
                            {'value': 'kraft', 'label': 'Kraft Paper', 'price_modifier': 25},
                        ]),
                        'default_value': '300gsm_duplex',
                        'order': 3,
                        'is_required': True,
                    },
                    {
                        'field_name': 'printing',
                        'field_label': 'Printing',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': 'no_print', 'label': 'No Printing', 'price_modifier': 0},
                            {'value': 'single_color', 'label': 'Single Color', 'price_modifier': 100},
                            {'value': 'two_color', 'label': 'Two Color', 'price_modifier': 200},
                            {'value': 'full_color', 'label': 'Full Color (CMYK)', 'price_modifier': 300},
                        ]),
                        'default_value': 'full_color',
                        'order': 4,
                        'is_required': True,
                    },
                    {
                        'field_name': 'finishing',
                        'field_label': 'Finishing Options',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': 'matte', 'label': 'Matte Finish', 'price_modifier': 0},
                            {'value': 'gloss_lam', 'label': 'Gloss Lamination', 'price_modifier': 150},
                            {'value': 'matte_lam', 'label': 'Matte Lamination', 'price_modifier': 150},
                            {'value': 'spot_uv', 'label': 'Spot UV', 'price_modifier': 300},
                            {'value': 'foiling', 'label': 'Gold/Silver Foiling', 'price_modifier': 500},
                        ]),
                        'default_value': 'matte_lam',
                        'order': 5,
                        'is_required': True,
                    },
                    {
                        'field_name': 'window',
                        'field_label': 'Window Option',
                        'field_type': 'checkbox',
                        'options': json.dumps([
                            {'value': 'window', 'label': 'Add Window (+₹200)', 'price_modifier': 200},
                        ]),
                        'order': 6,
                        'is_required': False,
                    },
                ],
                'base_price': 25,  # Base price per box
            },
            
            # ENVELOPES
            'envelopes': {
                'products': ['Envelopes'],
                'form_fields': [
                    {
                        'field_name': 'quantity',
                        'field_label': 'Quantity',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': '100', 'label': '100 Envelopes', 'price_modifier': 0},
                            {'value': '250', 'label': '250 Envelopes', 'price_modifier': -0.10},
                            {'value': '500', 'label': '500 Envelopes', 'price_modifier': -0.15},
                            {'value': '1000', 'label': '1000 Envelopes', 'price_modifier': -0.20},
                            {'value': '2500', 'label': '2500 Envelopes', 'price_modifier': -0.25},
                        ]),
                        'default_value': '500',
                        'order': 1,
                        'is_required': True,
                    },
                    {
                        'field_name': 'size',
                        'field_label': 'Envelope Size',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': 'dl', 'label': 'DL (110 x 220 mm)', 'price_modifier': 0},
                            {'value': 'c5', 'label': 'C5 (162 x 229 mm)', 'price_modifier': 25},
                            {'value': 'c4', 'label': 'C4 (229 x 324 mm)', 'price_modifier': 50},
                            {'value': 'a4', 'label': 'A4 (229 x 324 mm)', 'price_modifier': 50},
                            {'value': 'custom', 'label': 'Custom Size', 'price_modifier': 100},
                        ]),
                        'default_value': 'dl',
                        'order': 2,
                        'is_required': True,
                    },
                    {
                        'field_name': 'paper_type',
                        'field_label': 'Paper Quality',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': '80gsm', 'label': '80 GSM White Paper', 'price_modifier': 0},
                            {'value': '90gsm', 'label': '90 GSM Premium Paper', 'price_modifier': 25},
                            {'value': '100gsm', 'label': '100 GSM Art Paper', 'price_modifier': 50},
                            {'value': 'kraft', 'label': 'Kraft Paper', 'price_modifier': 25},
                        ]),
                        'default_value': '80gsm',
                        'order': 3,
                        'is_required': True,
                    },
                    {
                        'field_name': 'printing',
                        'field_label': 'Printing',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': 'no_print', 'label': 'No Printing', 'price_modifier': 0},
                            {'value': 'single_color', 'label': 'Single Color', 'price_modifier': 50},
                            {'value': 'full_color', 'label': 'Full Color', 'price_modifier': 150},
                        ]),
                        'default_value': 'full_color',
                        'order': 4,
                        'is_required': True,
                    },
                ],
                'base_price': 4,  # Base price per envelope
            },
        }
        
        # Apply configurations to products
        created_fields = 0
        created_pricing = 0
        
        for config_name, config in product_configs.items():
            self.stdout.write(f'\nProcessing {config_name}...')
            
            for product_name in config['products']:
                try:
                    product = Product.objects.get(name=product_name, is_active=True)
                    
                    # Clear existing fields for this product
                    ProductFormField.objects.filter(product=product).delete()
                    
                    # Create form fields
                    for field_data in config['form_fields']:
                        field_data_copy = field_data.copy()
                        field_data_copy['product'] = product
                        ProductFormField.objects.create(**field_data_copy)
                        created_fields += 1
                    
                    # Update base price
                    product.base_price = config['base_price']
                    product.price_per_unit = config['base_price']
                    product.save()
                    
                    # Create basic pricing tiers
                    ProductPricing.objects.filter(product=product).delete()
                    
                    # Create pricing based on quantity tiers
                    quantity_field = next((f for f in config['form_fields'] if f['field_name'] == 'quantity'), None)
                    if quantity_field:
                        options = json.loads(quantity_field['options'])
                        for option in options:
                            qty = int(option['value'])
                            base_price = config['base_price']
                            
                            # Apply quantity discount
                            if option['price_modifier'] < 0:
                                unit_price = base_price * (1 + option['price_modifier'])
                            else:
                                unit_price = base_price
                            
                            ProductPricing.objects.create(
                                product=product,
                                size='Standard',
                                min_quantity=qty,
                                max_quantity=qty * 2 - 1 if qty < 5000 else None,
                                price_per_unit=round(unit_price, 2),
                                setup_cost=500 if qty < 500 else 0,
                                turnaround_days=7 if qty < 1000 else 10,
                                is_active=True
                            )
                            created_pricing += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Updated {product.name}')
                    )
                    
                except Product.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠ Product not found: {product_name}')
                    )
                    continue
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 Successfully created:')
        )
        self.stdout.write(f'   • {created_fields} form fields')
        self.stdout.write(f'   • {created_pricing} pricing tiers')
        self.stdout.write(f'   • Updated {len([p for config in product_configs.values() for p in config["products"]])} products')