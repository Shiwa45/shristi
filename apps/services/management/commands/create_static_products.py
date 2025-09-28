# apps/services/management/commands/create_static_products.py

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.services.models import ServiceCategory, StaticProduct
from decimal import Decimal

class Command(BaseCommand):
    help = 'Create 28 static products across 5 categories with Creative Print Arts pricing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating static products...'))

        # Create categories first
        categories_data = [
            {
                'name': 'Book Printing',
                'description': 'Professional book printing services including children\'s books, novels, and educational materials.',
                'icon': 'fas fa-book',
                'order': 1
            },
            {
                'name': 'Paper Boxes',
                'description': 'Custom packaging solutions for medical, cosmetic, retail and industrial applications.',
                'icon': 'fas fa-box',
                'order': 2
            },
            {
                'name': 'Marketing Materials',
                'description': 'Professional marketing and promotional materials to boost your business.',
                'icon': 'fas fa-bullhorn',
                'order': 3
            },
            {
                'name': 'Stationery',
                'description': 'High-quality business stationery and office supplies.',
                'icon': 'fas fa-pen',
                'order': 4
            },
            {
                'name': 'Documents',
                'description': 'Professional document printing and binding services.',
                'icon': 'fas fa-file-alt',
                'order': 5
            }
        ]

        categories = {}
        for cat_data in categories_data:
            category, created = ServiceCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'slug': slugify(cat_data['name']),
                    'description': cat_data['description'],
                    'icon': cat_data['icon'],
                    'order': cat_data['order'],
                    'is_active': True,
                    'is_featured': True
                }
            )
            categories[cat_data['name']] = category
            if created:
                self.stdout.write(f'Created category: {category.name}')
            else:
                self.stdout.write(f'Category already exists: {category.name}')

        # Define products with pricing and options
        products_data = [
            # Book Printing (8 products)
            {
                'name': "Children's Books",
                'category': 'Book Printing',
                'description': 'Colorful and engaging children\'s books with high-quality printing and child-safe materials.',
                'short_description': 'Professional children\'s book printing with vibrant colors and safe materials.',
                'base_price': Decimal('12.50'),
                'price_unit': 'per book',
                'design_tool_enabled': False,
                'available_sizes': [
                    {'name': '8.5x8.5 inches (Square)', 'price_modifier': 0},
                    {'name': '8.5x11 inches (Portrait)', 'price_modifier': 50},
                    {'name': '11x8.5 inches (Landscape)', 'price_modifier': 75}
                ],
                'available_papers': [
                    {'name': '130 GSM Art Paper', 'price_modifier': 0},
                    {'name': '170 GSM Art Paper', 'price_modifier': 100},
                    {'name': '250 GSM Art Card', 'price_modifier': 200}
                ],
                'available_bindings': [
                    {'name': 'Saddle Stitch', 'price_modifier': 0},
                    {'name': 'Perfect Binding', 'price_modifier': 150},
                    {'name': 'Hard Cover', 'price_modifier': 500}
                ],
                'color_options': [
                    {'name': 'Full Color (4+4)', 'price_modifier': 0}
                ],
                'quantity_tiers': [
                    {'min_qty': 50, 'max_qty': 99, 'discount_percent': 0},
                    {'min_qty': 100, 'max_qty': 249, 'discount_percent': 8},
                    {'min_qty': 250, 'max_qty': 499, 'discount_percent': 15},
                    {'min_qty': 500, 'max_qty': 999, 'discount_percent': 22},
                    {'min_qty': 1000, 'max_qty': 2499, 'discount_percent': 30}
                ],
                'key_features': [
                    {'title': 'Child-Safe Materials', 'description': 'Non-toxic inks and papers safe for children'},
                    {'title': 'Vibrant Colors', 'description': 'High-quality offset printing for bright illustrations'},
                    {'title': 'Durable Binding', 'description': 'Strong binding that withstands repeated reading'}
                ],
                'specifications': {
                    'Minimum Pages': '8 pages',
                    'Maximum Pages': '48 pages',
                    'Print Type': 'Full Color Digital/Offset',
                    'Finishing Options': 'Matte/Gloss Lamination'
                }
            },
            {
                'name': 'Comic Books',
                'category': 'Book Printing',
                'description': 'Professional comic book printing with vibrant colors and quality paper perfect for graphic novels.',
                'short_description': 'High-quality comic book printing with vibrant colors and professional finish.',
                'base_price': Decimal('8.75'),
                'price_unit': 'per comic',
                'design_tool_enabled': False,
                'available_sizes': [
                    {'name': '6.625x10.25 inches (Standard)', 'price_modifier': 0},
                    {'name': '7x10 inches (Digest)', 'price_modifier': 25}
                ],
                'available_papers': [
                    {'name': '80 GSM Newsprint', 'price_modifier': 0},
                    {'name': '100 GSM Art Paper', 'price_modifier': 50},
                    {'name': '130 GSM Art Paper', 'price_modifier': 100}
                ],
                'available_bindings': [
                    {'name': 'Saddle Stitch', 'price_modifier': 0},
                    {'name': 'Perfect Binding', 'price_modifier': 100}
                ],
                'color_options': [
                    {'name': 'Full Color (4+4)', 'price_modifier': 0},
                    {'name': 'Black & White', 'price_modifier': -200}
                ],
                'quantity_tiers': [
                    {'min_qty': 100, 'max_qty': 249, 'discount_percent': 0},
                    {'min_qty': 250, 'max_qty': 499, 'discount_percent': 10},
                    {'min_qty': 500, 'max_qty': 999, 'discount_percent': 18},
                    {'min_qty': 1000, 'max_qty': 2499, 'discount_percent': 25}
                ],
                'key_features': [
                    {'title': 'Professional Quality', 'description': 'Sharp text and vibrant illustrations'},
                    {'title': 'Fast Turnaround', 'description': '5-7 business days standard delivery'},
                    {'title': 'Custom Covers', 'description': 'Glossy or matte cover options available'}
                ],
                'specifications': {
                    'Page Count': '24-32 pages typical',
                    'Cover': '250 GSM with lamination',
                    'Interior': '80-130 GSM options',
                    'Binding': 'Saddle stitch or perfect bound'
                }
            },
            {
                'name': 'Coffee Table Books',
                'category': 'Book Printing',
                'description': 'Luxury coffee table books with premium paper, superior binding, and exceptional print quality.',
                'short_description': 'Premium coffee table books with luxury materials and superior print quality.',
                'base_price': Decimal('45.00'),
                'price_unit': 'per book',
                'design_tool_enabled': False,
                'available_sizes': [
                    {'name': '10x10 inches (Square)', 'price_modifier': 0},
                    {'name': '11x8.5 inches (Landscape)', 'price_modifier': 100},
                    {'name': '12x9 inches (Large Landscape)', 'price_modifier': 200}
                ],
                'available_papers': [
                    {'name': '170 GSM Art Paper', 'price_modifier': 0},
                    {'name': '250 GSM Art Paper', 'price_modifier': 300},
                    {'name': '300 GSM Art Paper', 'price_modifier': 500}
                ],
                'available_bindings': [
                    {'name': 'Perfect Binding', 'price_modifier': 0},
                    {'name': 'Hard Cover', 'price_modifier': 800},
                    {'name': 'Case Bound with Dust Jacket', 'price_modifier': 1200}
                ],
                'color_options': [
                    {'name': 'Full Color (4+4)', 'price_modifier': 0}
                ],
                'quantity_tiers': [
                    {'min_qty': 25, 'max_qty': 49, 'discount_percent': 0},
                    {'min_qty': 50, 'max_qty': 99, 'discount_percent': 12},
                    {'min_qty': 100, 'max_qty': 249, 'discount_percent': 20},
                    {'min_qty': 250, 'max_qty': 499, 'discount_percent': 28}
                ],
                'key_features': [
                    {'title': 'Premium Materials', 'description': 'High-grade papers and binding materials'},
                    {'title': 'Superior Print Quality', 'description': 'Professional offset printing with color matching'},
                    {'title': 'Luxury Finish', 'description': 'Multiple finishing options including foil stamping'}
                ],
                'specifications': {
                    'Minimum Pages': '48 pages',
                    'Cover Options': 'Hard cover with dust jacket available',
                    'Print Quality': 'High-resolution offset printing',
                    'Finishing': 'Matte/Gloss lamination, UV coating'
                }
            },
            {
                'name': 'Coloring Books',
                'category': 'Book Printing',
                'description': 'Custom coloring books with thick paper perfect for crayons, markers, and colored pencils.',
                'short_description': 'Custom coloring books with thick, bleed-resistant paper for all coloring mediums.',
                'base_price': Decimal('6.25'),
                'price_unit': 'per book',
                'design_tool_enabled': False,
                'available_sizes': [
                    {'name': '8.5x11 inches (Letter)', 'price_modifier': 0},
                    {'name': '8.5x8.5 inches (Square)', 'price_modifier': -25}
                ],
                'available_papers': [
                    {'name': '120 GSM Offset Paper', 'price_modifier': 0},
                    {'name': '150 GSM Drawing Paper', 'price_modifier': 75}
                ],
                'available_bindings': [
                    {'name': 'Saddle Stitch', 'price_modifier': 0},
                    {'name': 'Perfect Binding', 'price_modifier': 100}
                ],
                'color_options': [
                    {'name': 'Black Line Art Only', 'price_modifier': 0}
                ],
                'quantity_tiers': [
                    {'min_qty': 50, 'max_qty': 99, 'discount_percent': 0},
                    {'min_qty': 100, 'max_qty': 249, 'discount_percent': 15},
                    {'min_qty': 250, 'max_qty': 499, 'discount_percent': 25},
                    {'min_qty': 500, 'max_qty': 999, 'discount_percent': 35}
                ],
                'key_features': [
                    {'title': 'Thick Paper', 'description': 'Prevents bleed-through from markers'},
                    {'title': 'Perforated Pages', 'description': 'Easy tear-out option available'},
                    {'title': 'Child-Safe Inks', 'description': 'Non-toxic printing materials'}
                ],
                'specifications': {
                    'Page Count': '24-48 pages',
                    'Paper Weight': '120-150 GSM',
                    'Print Type': 'Black line art',
                    'Special Features': 'Optional perforation'
                }
            },
            {
                'name': 'Art Books',
                'category': 'Book Printing',
                'description': 'High-end art books with museum-quality reproduction and premium binding options.',
                'short_description': 'Museum-quality art books with exceptional color reproduction and premium materials.',
                'base_price': Decimal('35.00'),
                'price_unit': 'per book',
                'design_tool_enabled': False,
                'available_sizes': [
                    {'name': '9x12 inches (Portrait)', 'price_modifier': 0},
                    {'name': '12x9 inches (Landscape)', 'price_modifier': 100},
                    {'name': '10x10 inches (Square)', 'price_modifier': 50}
                ],
                'available_papers': [
                    {'name': '170 GSM Art Paper', 'price_modifier': 0},
                    {'name': '250 GSM Art Paper', 'price_modifier': 200},
                    {'name': '300 GSM Fine Art Paper', 'price_modifier': 400}
                ],
                'available_bindings': [
                    {'name': 'Perfect Binding', 'price_modifier': 0},
                    {'name': 'Hard Cover', 'price_modifier': 600},
                    {'name': 'Smyth Sewn Hard Cover', 'price_modifier': 1000}
                ],
                'color_options': [
                    {'name': 'Full Color (4+4)', 'price_modifier': 0},
                    {'name': 'Full Color + 2 Spot Colors', 'price_modifier': 300}
                ],
                'quantity_tiers': [
                    {'min_qty': 25, 'max_qty': 49, 'discount_percent': 0},
                    {'min_qty': 50, 'max_qty': 99, 'discount_percent': 15},
                    {'min_qty': 100, 'max_qty': 249, 'discount_percent': 25},
                    {'min_qty': 250, 'max_qty': 499, 'discount_percent': 35}
                ],
                'key_features': [
                    {'title': 'Color Accuracy', 'description': 'Professional color matching and calibration'},
                    {'title': 'Premium Papers', 'description': 'Museum-quality fine art papers'},
                    {'title': 'Expert Binding', 'description': 'Hand-crafted binding options available'}
                ],
                'specifications': {
                    'Color Profile': 'Adobe RGB, sRGB compatible',
                    'Print Process': 'High-end offset with spot color options',
                    'Proofing': 'Color-accurate digital proofs included',
                    'Quality Control': 'Individual inspection of each book'
                }
            },
            {
                'name': 'Annual Reports',
                'category': 'Book Printing',
                'description': 'Professional annual reports with executive binding and premium presentation materials.',
                'short_description': 'Executive-quality annual reports with professional binding and premium materials.',
                'base_price': Decimal('25.00'),
                'price_unit': 'per report',
                'design_tool_enabled': False,
                'available_sizes': [
                    {'name': '8.5x11 inches (Letter)', 'price_modifier': 0},
                    {'name': '11x8.5 inches (Landscape)', 'price_modifier': 50}
                ],
                'available_papers': [
                    {'name': '100 GSM Text Paper', 'price_modifier': 0},
                    {'name': '130 GSM Art Paper', 'price_modifier': 100},
                    {'name': '170 GSM Art Paper', 'price_modifier': 200}
                ],
                'available_bindings': [
                    {'name': 'Perfect Binding', 'price_modifier': 0},
                    {'name': 'Coil Binding', 'price_modifier': 75},
                    {'name': 'Hard Cover', 'price_modifier': 400}
                ],
                'color_options': [
                    {'name': 'Full Color (4+4)', 'price_modifier': 0},
                    {'name': 'Black & White Text + Color Cover', 'price_modifier': -150}
                ],
                'quantity_tiers': [
                    {'min_qty': 25, 'max_qty': 49, 'discount_percent': 0},
                    {'min_qty': 50, 'max_qty': 99, 'discount_percent': 10},
                    {'min_qty': 100, 'max_qty': 249, 'discount_percent': 18},
                    {'min_qty': 250, 'max_qty': 499, 'discount_percent': 25}
                ],
                'key_features': [
                    {'title': 'Professional Presentation', 'description': 'Executive-quality materials and binding'},
                    {'title': 'Fast Turnaround', 'description': 'Rush options available for urgent deadlines'},
                    {'title': 'Multiple Formats', 'description': 'Various sizes and binding options'}
                ],
                'specifications': {
                    'Page Range': '24-200 pages',
                    'Cover Options': '250 GSM with lamination',
                    'Finishing': 'Gloss/Matte/Soft-touch lamination',
                    'Add-ons': 'Foil stamping, embossing available'
                }
            },
            {
                'name': 'Yearbooks',
                'category': 'Book Printing',
                'description': 'School and organization yearbooks with durable binding and photo-quality printing.',
                'short_description': 'High-quality yearbooks with durable binding and excellent photo reproduction.',
                'base_price': Decimal('28.50'),
                'price_unit': 'per yearbook',
                'design_tool_enabled': False,
                'available_sizes': [
                    {'name': '8.5x11 inches (Portrait)', 'price_modifier': 0},
                    {'name': '9x12 inches (Large Portrait)', 'price_modifier': 150}
                ],
                'available_papers': [
                    {'name': '100 GSM Text Paper', 'price_modifier': 0},
                    {'name': '130 GSM Art Paper', 'price_modifier': 150},
                    {'name': '170 GSM Photo Paper', 'price_modifier': 300}
                ],
                'available_bindings': [
                    {'name': 'Perfect Binding', 'price_modifier': 0},
                    {'name': 'Hard Cover', 'price_modifier': 500},
                    {'name': 'Smyth Sewn Hard Cover', 'price_modifier': 800}
                ],
                'color_options': [
                    {'name': 'Full Color (4+4)', 'price_modifier': 0}
                ],
                'quantity_tiers': [
                    {'min_qty': 25, 'max_qty': 49, 'discount_percent': 0},
                    {'min_qty': 50, 'max_qty': 99, 'discount_percent': 12},
                    {'min_qty': 100, 'max_qty': 199, 'discount_percent': 20},
                    {'min_qty': 200, 'max_qty': 499, 'discount_percent': 28}
                ],
                'key_features': [
                    {'title': 'Photo Quality', 'description': 'High-resolution printing perfect for photographs'},
                    {'title': 'Durable Construction', 'description': 'Built to last for years of handling'},
                    {'title': 'Custom Covers', 'description': 'Personalized covers with school/organization branding'}
                ],
                'specifications': {
                    'Typical Pages': '100-300 pages',
                    'Photo Resolution': '300 DPI minimum',
                    'Cover Finishing': 'Gloss lamination standard',
                    'Personalization': 'Individual names/photos available'
                }
            },
            {
                'name': 'On-Demand Books',
                'category': 'Book Printing',
                'description': 'Print-on-demand books perfect for self-publishing authors and small publishers.',
                'short_description': 'Professional print-on-demand books with fast turnaround and no minimum orders.',
                'base_price': Decimal('8.95'),
                'price_unit': 'per book',
                'design_tool_enabled': False,
                'available_sizes': [
                    {'name': '6x9 inches (Trade)', 'price_modifier': 0},
                    {'name': '5.5x8.5 inches (Digest)', 'price_modifier': -25},
                    {'name': '8.5x11 inches (Large)', 'price_modifier': 100}
                ],
                'available_papers': [
                    {'name': '60# White Paper', 'price_modifier': 0},
                    {'name': '70# Cream Paper', 'price_modifier': 25},
                    {'name': '80# White Paper', 'price_modifier': 50}
                ],
                'available_bindings': [
                    {'name': 'Perfect Binding', 'price_modifier': 0},
                    {'name': 'Hardcover', 'price_modifier': 400}
                ],
                'color_options': [
                    {'name': 'Black & White Interior', 'price_modifier': 0},
                    {'name': 'Color Cover Only', 'price_modifier': 150},
                    {'name': 'Full Color', 'price_modifier': 400}
                ],
                'quantity_tiers': [
                    {'min_qty': 1, 'max_qty': 24, 'discount_percent': 0},
                    {'min_qty': 25, 'max_qty': 49, 'discount_percent': 8},
                    {'min_qty': 50, 'max_qty': 99, 'discount_percent': 15},
                    {'min_qty': 100, 'max_qty': 249, 'discount_percent': 22}
                ],
                'key_features': [
                    {'title': 'No Minimum Order', 'description': 'Order as few as 1 copy'},
                    {'title': 'Fast Production', 'description': '2-3 business days turnaround'},
                    {'title': 'Professional Quality', 'description': 'Bookstore-quality printing and binding'}
                ],
                'specifications': {
                    'Page Count': '24-800 pages',
                    'File Format': 'PDF ready-to-print files',
                    'Turnaround': '2-3 business days',
                    'Shipping': 'Multiple shipping options available'
                }
            },

            # Paper Boxes (6 products)
            {
                'name': 'Medical Boxes',
                'category': 'Paper Boxes',
                'description': 'FDA-compliant medical packaging boxes with tamper-evident features and sterile materials.',
                'short_description': 'FDA-compliant medical packaging with tamper-evident features and sterile materials.',
                'base_price': Decimal('2.75'),
                'price_unit': 'per box',
                'design_tool_enabled': False,
                'available_sizes': [
                    {'name': '4x4x2 inches (Small)', 'price_modifier': 0},
                    {'name': '6x4x2 inches (Medium)', 'price_modifier': 50},
                    {'name': '8x6x3 inches (Large)', 'price_modifier': 100}
                ],
                'available_papers': [
                    {'name': '350 GSM SBS Board', 'price_modifier': 0},
                    {'name': '400 GSM SBS Board', 'price_modifier': 25},
                    {'name': '450 GSM Pharmaceutical Grade', 'price_modifier': 75}
                ],
                'available_finishes': [
                    {'name': 'Matte Varnish', 'price_modifier': 0},
                    {'name': 'Gloss Varnish', 'price_modifier': 25},
                    {'name': 'Anti-microbial Coating', 'price_modifier': 100}
                ],
                'color_options': [
                    {'name': 'Single Color', 'price_modifier': 0},
                    {'name': '2 Colors', 'price_modifier': 50},
                    {'name': 'Full Color (CMYK)', 'price_modifier': 150}
                ],
                'quantity_tiers': [
                    {'min_qty': 500, 'max_qty': 999, 'discount_percent': 0},
                    {'min_qty': 1000, 'max_qty': 2499, 'discount_percent': 12},
                    {'min_qty': 2500, 'max_qty': 4999, 'discount_percent': 20},
                    {'min_qty': 5000, 'max_qty': 9999, 'discount_percent': 28}
                ],
                'key_features': [
                    {'title': 'FDA Compliant', 'description': 'Meets FDA requirements for medical packaging'},
                    {'title': 'Tamper Evident', 'description': 'Security features to prevent tampering'},
                    {'title': 'Sterile Materials', 'description': 'Clean-room processed materials'}
                ],
                'specifications': {
                    'Material': 'Pharmaceutical grade paperboard',
                    'Compliance': 'FDA 21 CFR 176.170',
                    'Features': 'Tamper-evident sealing',
                    'Certifications': 'ISO 15378 certified facility'
                }
            },
            {
                'name': 'Cosmetic Boxes',
                'category': 'Paper Boxes',
                'description': 'Luxury cosmetic packaging with premium finishes and elegant design options.',
                'short_description': 'Premium cosmetic packaging with luxury finishes and elegant design.',
                'base_price': Decimal('3.25'),
                'price_unit': 'per box',
                'design_tool_enabled': True,
                'canvas_width': 800,
                'canvas_height': 600,
                'available_sizes': [
                    {'name': '3x3x3 inches (Compact)', 'price_modifier': 0},
                    {'name': '4x4x2 inches (Foundation)', 'price_modifier': 25},
                    {'name': '6x4x2 inches (Palette)', 'price_modifier': 75}
                ],
                'available_papers': [
                    {'name': '350 GSM Art Card', 'price_modifier': 0},
                    {'name': '400 GSM Art Card', 'price_modifier': 35},
                    {'name': '450 GSM Luxury Board', 'price_modifier': 85}
                ],
                'available_finishes': [
                    {'name': 'Matte Lamination', 'price_modifier': 50},
                    {'name': 'Gloss Lamination', 'price_modifier': 50},
                    {'name': 'Soft Touch Lamination', 'price_modifier': 125},
                    {'name': 'Foil Stamping', 'price_modifier': 200},
                    {'name': 'Embossing', 'price_modifier': 175}
                ],
                'color_options': [
                    {'name': 'Full Color (CMYK)', 'price_modifier': 0},
                    {'name': 'CMYK + 1 Spot Color', 'price_modifier': 75},
                    {'name': 'CMYK + Metallic', 'price_modifier': 125}
                ],
                'quantity_tiers': [
                    {'min_qty': 250, 'max_qty': 499, 'discount_percent': 0},
                    {'min_qty': 500, 'max_qty': 999, 'discount_percent': 15},
                    {'min_qty': 1000, 'max_qty': 2499, 'discount_percent': 25},
                    {'min_qty': 2500, 'max_qty': 4999, 'discount_percent': 35}
                ],
                'key_features': [
                    {'title': 'Luxury Finishes', 'description': 'Premium lamination and foil options'},
                    {'title': 'Custom Shapes', 'description': 'Die-cut windows and unique shapes available'},
                    {'title': 'Brand Enhancement', 'description': 'Professional design that enhances brand value'}
                ],
                'specifications': {
                    'Structure': 'Reverse tuck end, auto-lock bottom',
                    'Window Options': 'Clear PVC or PET windows',
                    'Inserts': 'Custom foam or cardboard inserts',
                    'Minimum Order': '250 pieces'
                }
            },
            {
                'name': 'Retail Boxes',
                'category': 'Paper Boxes',
                'description': 'Versatile retail packaging boxes perfect for e-commerce and in-store display.',
                'short_description': 'Versatile retail packaging for e-commerce and in-store display.',
                'base_price': Decimal('1.85'),
                'price_unit': 'per box',
                'design_tool_enabled': True,
                'canvas_width': 900,
                'canvas_height': 700,
                'available_sizes': [
                    {'name': '6x6x4 inches (Small)', 'price_modifier': 0},
                    {'name': '8x6x4 inches (Medium)', 'price_modifier': 35},
                    {'name': '10x8x4 inches (Large)', 'price_modifier': 75},
                    {'name': '12x9x6 inches (Extra Large)', 'price_modifier': 125}
                ],
                'available_papers': [
                    {'name': '300 GSM Kraft Board', 'price_modifier': -25},
                    {'name': '350 GSM SBS Board', 'price_modifier': 0},
                    {'name': '400 GSM SBS Board', 'price_modifier': 50}
                ],
                'available_finishes': [
                    {'name': 'Natural (No Coating)', 'price_modifier': 0},
                    {'name': 'Matte Varnish', 'price_modifier': 25},
                    {'name': 'Gloss Varnish', 'price_modifier': 25},
                    {'name': 'Matte Lamination', 'price_modifier': 75}
                ],
                'color_options': [
                    {'name': 'Single Color', 'price_modifier': 0},
                    {'name': '2 Colors', 'price_modifier': 40},
                    {'name': 'Full Color (CMYK)', 'price_modifier': 100}
                ],
                'quantity_tiers': [
                    {'min_qty': 500, 'max_qty': 999, 'discount_percent': 0},
                    {'min_qty': 1000, 'max_qty': 2499, 'discount_percent': 18},
                    {'min_qty': 2500, 'max_qty': 4999, 'discount_percent': 28},
                    {'min_qty': 5000, 'max_qty': 9999, 'discount_percent': 38}
                ],
                'key_features': [
                    {'title': 'E-commerce Ready', 'description': 'Designed for shipping and unboxing experience'},
                    {'title': 'Shelf Appeal', 'description': 'Attractive design for retail display'},
                    {'title': 'Cost Effective', 'description': 'Economical solution for high-volume needs'}
                ],
                'specifications': {
                    'Construction': 'Crash-lock bottom, tuck-top',
                    'Shipping': 'Flat-packed for efficient storage',
                    'Customization': 'Full-color printing available',
                    'Eco-Friendly': 'Recyclable materials'
                }
            },
            {
                'name': 'Folding Carton',
                'category': 'Paper Boxes',
                'description': 'Professional folding cartons for food, pharmaceutical, and consumer goods packaging.',
                'short_description': 'Professional folding cartons for food, pharmaceutical, and consumer goods.',
                'base_price': Decimal('1.45'),
                'price_unit': 'per carton',
                'design_tool_enabled': False,
                'available_sizes': [
                    {'name': '4x3x1 inches (Small)', 'price_modifier': 0},
                    {'name': '6x4x2 inches (Medium)', 'price_modifier': 25},
                    {'name': '8x6x3 inches (Large)', 'price_modifier': 65}
                ],
                'available_papers': [
                    {'name': '300 GSM SBS Board', 'price_modifier': 0},
                    {'name': '350 GSM SBS Board', 'price_modifier': 20},
                    {'name': '400 GSM Food Grade Board', 'price_modifier': 50}
                ],
                'available_finishes': [
                    {'name': 'Aqueous Coating', 'price_modifier': 15},
                    {'name': 'UV Coating', 'price_modifier': 35},
                    {'name': 'Food-Safe Coating', 'price_modifier': 50}
                ],
                'color_options': [
                    {'name': 'Single Color', 'price_modifier': 0},
                    {'name': '2 Colors', 'price_modifier': 25},
                    {'name': 'Full Color (CMYK)', 'price_modifier': 75}
                ],
                'quantity_tiers': [
                    {'min_qty': 1000, 'max_qty': 2499, 'discount_percent': 0},
                    {'min_qty': 2500, 'max_qty': 4999, 'discount_percent': 15},
                    {'min_qty': 5000, 'max_qty': 9999, 'discount_percent': 25},
                    {'min_qty': 10000, 'max_qty': 24999, 'discount_percent': 35}
                ],
                'key_features': [
                    {'title': 'Food Safe', 'description': 'FDA-approved materials for food contact'},
                    {'title': 'Efficient Assembly', 'description': 'Pre-glued for easy setup'},
                    {'title': 'High-Speed Production', 'description': 'Designed for automated packaging lines'}
                ],
                'specifications': {
                    'Material Compliance': 'FDA, USDA approved',
                    'Assembly': 'Straight-line or crash-lock bottom',
                    'Printing': 'Flexographic or lithographic',
                    'Testing': 'Drop test and compression certified'
                }
            },
            {
                'name': 'Corrugated Boxes',
                'category': 'Paper Boxes',
                'description': 'Heavy-duty corrugated shipping boxes with superior protection and durability.',
                'short_description': 'Heavy-duty corrugated shipping boxes with superior protection.',
                'base_price': Decimal('2.25'),
                'price_unit': 'per box',
                'design_tool_enabled': False,
                'available_sizes': [
                    {'name': '12x9x6 inches (Medium)', 'price_modifier': 0},
                    {'name': '16x12x8 inches (Large)', 'price_modifier': 75},
                    {'name': '20x16x12 inches (Extra Large)', 'price_modifier': 150}
                ],
                'available_papers': [
                    {'name': '32 ECT Single Wall', 'price_modifier': 0},
                    {'name': '44 ECT Single Wall', 'price_modifier': 35},
                    {'name': '48 ECT Double Wall', 'price_modifier': 85}
                ],
                'color_options': [
                    {'name': 'Natural Brown', 'price_modifier': 0},
                    {'name': 'Single Color Print', 'price_modifier': 50},
                    {'name': 'Full Color Print', 'price_modifier': 150}
                ],
                'quantity_tiers': [
                    {'min_qty': 100, 'max_qty': 249, 'discount_percent': 0},
                    {'min_qty': 250, 'max_qty': 499, 'discount_percent': 12},
                    {'min_qty': 500, 'max_qty': 999, 'discount_percent': 22},
                    {'min_qty': 1000, 'max_qty': 2499, 'discount_percent': 32}
                ],
                'key_features': [
                    {'title': 'Superior Protection', 'description': 'High-strength corrugated material'},
                    {'title': 'Shipping Optimized', 'description': 'Designed for efficient shipping and storage'},
                    {'title': 'Eco-Friendly', 'description': '100% recyclable materials'}
                ],
                'specifications': {
                    'Edge Crush Test': '32-48 ECT options',
                    'Construction': 'RSC (Regular Slotted Container)',
                    'Printing': 'Flexographic printing available',
                    'Environmental': '100% recyclable'
                }
            },
            {
                'name': 'Kraft Boxes',
                'category': 'Paper Boxes',
                'description': 'Eco-friendly kraft boxes perfect for natural and organic product packaging.',
                'short_description': 'Eco-friendly kraft boxes perfect for natural and organic products.',
                'base_price': Decimal('1.65'),
                'price_unit': 'per box',
                'design_tool_enabled': True,
                'canvas_width': 750,
                'canvas_height': 600,
                'available_sizes': [
                    {'name': '4x4x2 inches (Small)', 'price_modifier': 0},
                    {'name': '6x6x3 inches (Medium)', 'price_modifier': 35},
                    {'name': '8x8x4 inches (Large)', 'price_modifier': 75}
                ],
                'available_papers': [
                    {'name': '300 GSM Natural Kraft', 'price_modifier': 0},
                    {'name': '350 GSM Natural Kraft', 'price_modifier': 25},
                    {'name': '400 GSM Recycled Kraft', 'price_modifier': 45}
                ],
                'available_finishes': [
                    {'name': 'Natural (Uncoated)', 'price_modifier': 0},
                    {'name': 'Matte Varnish', 'price_modifier': 25}
                ],
                'color_options': [
                    {'name': 'Natural Kraft Color', 'price_modifier': 0},
                    {'name': 'Single Color Print', 'price_modifier': 35},
                    {'name': '2 Color Print', 'price_modifier': 65}
                ],
                'quantity_tiers': [
                    {'min_qty': 250, 'max_qty': 499, 'discount_percent': 0},
                    {'min_qty': 500, 'max_qty': 999, 'discount_percent': 15},
                    {'min_qty': 1000, 'max_qty': 2499, 'discount_percent': 25},
                    {'min_qty': 2500, 'max_qty': 4999, 'discount_percent': 35}
                ],
                'key_features': [
                    {'title': '100% Recyclable', 'description': 'Environmentally friendly packaging'},
                    {'title': 'Natural Appeal', 'description': 'Perfect for organic and artisanal products'},
                    {'title': 'Cost Effective', 'description': 'Economical packaging solution'}
                ],
                'specifications': {
                    'Material': '100% recycled kraft paperboard',
                    'Certification': 'FSC certified',
                    'Printing': 'Water-based inks',
                    'End of Life': 'Fully recyclable and biodegradable'
                }
            },

            # Marketing Materials (7 products)
            {
                'name': 'Brochures',
                'category': 'Marketing Materials',
                'description': 'Professional brochures with premium paper and finishing options for effective marketing.',
                'short_description': 'Professional tri-fold and bi-fold brochures with premium finishes.',
                'base_price': Decimal('0.85'),
                'price_unit': 'per brochure',
                'design_tool_enabled': True,
                'canvas_width': 2550,
                'canvas_height': 3300,  # 8.5x11 tri-fold at 300 DPI
                'available_sizes': [
                    {'name': '8.5x11 inches (Tri-fold)', 'price_modifier': 0},
                    {'name': '8.5x14 inches (Legal Tri-fold)', 'price_modifier': 25},
                    {'name': '11x17 inches (Bi-fold)', 'price_modifier': 50}
                ],
                'available_papers': [
                    {'name': '100 GSM Text Paper', 'price_modifier': 0},
                    {'name': '130 GSM Art Paper', 'price_modifier': 15},
                    {'name': '170 GSM Art Paper', 'price_modifier': 35}
                ],
                'available_finishes': [
                    {'name': 'No Coating', 'price_modifier': 0},
                    {'name': 'Matte Lamination', 'price_modifier': 25},
                    {'name': 'Gloss Lamination', 'price_modifier': 25},
                    {'name': 'Spot UV', 'price_modifier': 65}
                ],
                'color_options': [
                    {'name': 'Full Color (4+4)', 'price_modifier': 0},
                    {'name': 'Full Color + Spot UV', 'price_modifier': 45}
                ],
                'quantity_tiers': [
                    {'min_qty': 250, 'max_qty': 499, 'discount_percent': 0},
                    {'min_qty': 500, 'max_qty': 999, 'discount_percent': 12},
                    {'min_qty': 1000, 'max_qty': 2499, 'discount_percent': 22},
                    {'min_qty': 2500, 'max_qty': 4999, 'discount_percent': 32},
                    {'min_qty': 5000, 'max_qty': 9999, 'discount_percent': 42}
                ],
                'key_features': [
                    {'title': 'Professional Design', 'description': 'High-impact marketing materials'},
                    {'title': 'Premium Finishes', 'description': 'Lamination and UV coating options'},
                    {'title': 'Fast Turnaround', 'description': '3-5 business days standard'}
                ],
                'specifications': {
                    'Fold Types': 'Tri-fold, Z-fold, Gate-fold, Bi-fold',
                    'Print Quality': '300 DPI offset printing',
                    'File Requirements': 'PDF with 0.125" bleed',
                    'Turnaround': '3-5 business days'
                }
            },
            {
                'name': 'Catalogues',
                'category': 'Marketing Materials',
                'description': 'Professional product catalogues with perfect binding and high-quality photo reproduction.',
                'short_description': 'Professional product catalogues with perfect binding and photo-quality printing.',
                'base_price': Decimal('12.50'),
                'price_unit': 'per catalogue',
                'design_tool_enabled': False,
                'available_sizes': [
                    {'name': '8.5x11 inches (Letter)', 'price_modifier': 0},
                    {'name': '8.5x8.5 inches (Square)', 'price_modifier': -25},
                    {'name': '9x12 inches (Large)', 'price_modifier': 75}
                ],
                'available_papers': [
                    {'name': '100 GSM Text Paper', 'price_modifier': 0},
                    {'name': '130 GSM Art Paper', 'price_modifier': 100},
                    {'name': '170 GSM Art Paper', 'price_modifier': 200}
                ],
                'available_bindings': [
                    {'name': 'Saddle Stitch (up to 48 pages)', 'price_modifier': 0},
                    {'name': 'Perfect Binding', 'price_modifier': 150},
                    {'name': 'Coil Binding', 'price_modifier': 125}
                ],
                'color_options': [
                    {'name': 'Full Color (4+4)', 'price_modifier': 0}
                ],
                'quantity_tiers': [
                    {'min_qty': 50, 'max_qty': 99, 'discount_percent': 0},
                    {'min_qty': 100, 'max_qty': 249, 'discount_percent': 15},
                    {'min_qty': 250, 'max_qty': 499, 'discount_percent': 25},
                    {'min_qty': 500, 'max_qty': 999, 'discount_percent': 35}
                ],
                'key_features': [
                    {'title': 'Photo Quality', 'description': 'High-resolution printing perfect for product images'},
                    {'title': 'Professional Binding', 'description': 'Durable binding options for frequent use'},
                    {'title': 'Custom Covers', 'description': 'Heavy cover stock with lamination options'}
                ],
                'specifications': {
                    'Page Count': '16-200 pages',
                    'Cover Stock': '250 GSM with lamination',
                    'Image Quality': '300 DPI, color-corrected',
                    'Binding Options': 'Saddle stitch, perfect bound, coil'
                }
            },
            {
                'name': 'Posters',
                'category': 'Marketing Materials',
                'description': 'High-impact posters for advertising, events, and promotional campaigns.',
                'short_description': 'High-impact advertising and promotional posters in various sizes.',
                'base_price': Decimal('8.95'),
                'price_unit': 'per poster',
                'design_tool_enabled': False,
                'available_sizes': [
                    {'name': '18x24 inches (Medium)', 'price_modifier': 0},
                    {'name': '24x36 inches (Large)', 'price_modifier': 85},
                    {'name': '27x40 inches (Movie Poster)', 'price_modifier': 150},
                    {'name': '36x48 inches (Extra Large)', 'price_modifier': 225}
                ],
                'available_papers': [
                    {'name': '170 GSM Poster Paper', 'price_modifier': 0},
                    {'name': '200 GSM Photo Paper', 'price_modifier': 45},
                    {'name': '250 GSM Heavy Poster', 'price_modifier': 85}
                ],
                'available_finishes': [
                    {'name': 'Matte Finish', 'price_modifier': 0},
                    {'name': 'Gloss Finish', 'price_modifier': 25},
                    {'name': 'Satin Finish', 'price_modifier': 35}
                ],
                'color_options': [
                    {'name': 'Full Color (4+0)', 'price_modifier': 0}
                ],
                'quantity_tiers': [
                    {'min_qty': 25, 'max_qty': 49, 'discount_percent': 0},
                    {'min_qty': 50, 'max_qty': 99, 'discount_percent': 15},
                    {'min_qty': 100, 'max_qty': 249, 'discount_percent': 25},
                    {'min_qty': 250, 'max_qty': 499, 'discount_percent': 35}
                ],
                'key_features': [
                    {'title': 'High Resolution', 'description': 'Sharp, vibrant colors for maximum impact'},
                    {'title': 'Durable Materials', 'description': 'Tear-resistant papers for long-lasting display'},
                    {'title': 'Weather Resistant', 'description': 'UV-resistant inks for outdoor use'}
                ],
                'specifications': {
                    'Resolution': '150-300 DPI recommended',
                    'Color Profile': 'CMYK, Pantone matching available',
                    'Mounting': 'Foam core mounting available',
                    'Lamination': 'Optional for outdoor use'
                }
            },
            {
                'name': 'Flyers',
                'category': 'Marketing Materials',
                'description': 'Eye-catching flyers perfect for promotions, events, and direct mail campaigns.',
                'short_description': 'Eye-catching promotional flyers for events and direct mail campaigns.',
                'base_price': Decimal('0.35'),
                'price_unit': 'per flyer',
                'design_tool_enabled': True,
                'canvas_width': 2550,
                'canvas_height': 3300,  # 8.5x11 at 300 DPI
                'available_sizes': [
                    {'name': '8.5x11 inches (Letter)', 'price_modifier': 0},
                    {'name': '5.5x8.5 inches (Half Sheet)', 'price_modifier': -15},
                    {'name': '4x6 inches (Postcard)', 'price_modifier': -25},
                    {'name': '11x17 inches (Tabloid)', 'price_modifier': 50}
                ],
                'available_papers': [
                    {'name': '80 GSM Text Paper', 'price_modifier': 0},
                    {'name': '100 GSM Text Paper', 'price_modifier': 10},
                    {'name': '130 GSM Art Paper', 'price_modifier': 25},
                    {'name': '170 GSM Card Stock', 'price_modifier': 45}
                ],
                'available_finishes': [
                    {'name': 'No Coating', 'price_modifier': 0},
                    {'name': 'Aqueous Coating', 'price_modifier': 15},
                    {'name': 'UV Coating', 'price_modifier': 25}
                ],
                'color_options': [
                    {'name': 'Full Color (4+4)', 'price_modifier': 0},
                    {'name': 'Full Color (4+0)', 'price_modifier': -15},
                    {'name': 'Black & White', 'price_modifier': -25}
                ],
                'quantity_tiers': [
                    {'min_qty': 500, 'max_qty': 999, 'discount_percent': 0},
                    {'min_qty': 1000, 'max_qty': 2499, 'discount_percent': 20},
                    {'min_qty': 2500, 'max_qty': 4999, 'discount_percent': 35},
                    {'min_qty': 5000, 'max_qty': 9999, 'discount_percent': 45},
                    {'min_qty': 10000, 'max_qty': 24999, 'discount_percent': 55}
                ],
                'key_features': [
                    {'title': 'High Volume Pricing', 'description': 'Excellent rates for large quantities'},
                    {'title': 'Fast Production', 'description': '24-48 hour rush options available'},
                    {'title': 'Distribution Ready', 'description': 'Perfect for direct mail and hand distribution'}
                ],
                'specifications': {
                    'Typical Uses': 'Events, sales, grand openings, direct mail',
                    'Mailing': 'USDA compliant for direct mail',
                    'Rush Options': '24-48 hours available',
                    'File Format': 'PDF with bleed preferred'
                }
            },
            {
                'name': 'Danglers',
                'category': 'Marketing Materials',
                'description': 'Hanging promotional danglers and shelf talkers for point-of-sale advertising.',
                'short_description': 'Hanging promotional danglers and shelf talkers for point-of-sale advertising.',
                'base_price': Decimal('1.25'),
                'price_unit': 'per dangler',
                'design_tool_enabled': False,
                'available_sizes': [
                    {'name': '4x6 inches (Small)', 'price_modifier': 0},
                    {'name': '6x8 inches (Medium)', 'price_modifier': 35},
                    {'name': '8x10 inches (Large)', 'price_modifier': 75}
                ],
                'available_papers': [
                    {'name': '250 GSM Art Card', 'price_modifier': 0},
                    {'name': '300 GSM Art Card', 'price_modifier': 25},
                    {'name': '350 GSM Card Stock', 'price_modifier': 50}
                ],
                'available_finishes': [
                    {'name': 'Matte Lamination', 'price_modifier': 35},
                    {'name': 'Gloss Lamination', 'price_modifier': 35},
                    {'name': 'Spot UV', 'price_modifier': 65}
                ],
                'color_options': [
                    {'name': 'Full Color (4+4)', 'price_modifier': 0},
                    {'name': 'Full Color + Spot UV', 'price_modifier': 45}
                ],
                'quantity_tiers': [
                    {'min_qty': 100, 'max_qty': 249, 'discount_percent': 0},
                    {'min_qty': 250, 'max_qty': 499, 'discount_percent': 18},
                    {'min_qty': 500, 'max_qty': 999, 'discount_percent': 28},
                    {'min_qty': 1000, 'max_qty': 2499, 'discount_percent': 38}
                ],
                'key_features': [
                    {'title': 'Die-Cut Shapes', 'description': 'Custom shapes and perforations available'},
                    {'title': 'Hanging Hardware', 'description': 'Pre-punched holes for easy hanging'},
                    {'title': 'Eye-Catching', 'description': 'Designed to grab customer attention'}
                ],
                'specifications': {
                    'Material': 'Heavy card stock for durability',
                    'Finishing': 'Lamination for protection',
                    'Hardware': 'Grommets or punch holes included',
                    'Custom Shapes': 'Die-cutting available'
                }
            },
            {
                'name': 'Standees',
                'category': 'Marketing Materials',
                'description': 'Life-size cardboard standees and display stands for promotional events and retail.',
                'short_description': 'Life-size cardboard standees and display stands for promotional events.',
                'base_price': Decimal('125.00'),
                'price_unit': 'per standee',
                'design_tool_enabled': False,
                'available_sizes': [
                    {'name': '24x36 inches (Small)', 'price_modifier': 0},
                    {'name': '36x72 inches (Life-size)', 'price_modifier': 200},
                    {'name': '48x96 inches (Extra Large)', 'price_modifier': 400}
                ],
                'available_papers': [
                    {'name': '5mm Corrugated Board', 'price_modifier': 0},
                    {'name': '10mm Foam Board', 'price_modifier': 150},
                    {'name': '15mm Foam Board', 'price_modifier': 250}
                ],
                'available_finishes': [
                    {'name': 'Matte Finish', 'price_modifier': 0},
                    {'name': 'Gloss Finish', 'price_modifier': 50}
                ],
                'color_options': [
                    {'name': 'Full Color (4+0)', 'price_modifier': 0}
                ],
                'quantity_tiers': [
                    {'min_qty': 1, 'max_qty': 4, 'discount_percent': 0},
                    {'min_qty': 5, 'max_qty': 9, 'discount_percent': 15},
                    {'min_qty': 10, 'max_qty': 24, 'discount_percent': 25},
                    {'min_qty': 25, 'max_qty': 49, 'discount_percent': 35}
                ],
                'key_features': [
                    {'title': 'Free-Standing', 'description': 'Includes easel back for stable display'},
                    {'title': 'High Resolution', 'description': 'Photo-quality printing for realistic appearance'},
                    {'title': 'Lightweight', 'description': 'Easy to transport and set up'}
                ],
                'specifications': {
                    'Material': 'Corrugated cardboard or foam board',
                    'Support': 'Easel back or H-frame stand',
                    'Resolution': '150 DPI for large format',
                    'Shipping': 'Flat-packed for easy transport'
                }
            },
            {
                'name': 'Pen Drives',
                'category': 'Marketing Materials',
                'description': 'Custom branded USB pen drives with logo printing and data loading services.',
                'short_description': 'Custom branded USB pen drives with logo printing and preloaded content.',
                'base_price': Decimal('8.50'),
                'price_unit': 'per pen drive',
                'design_tool_enabled': False,
                'available_sizes': [
                    {'name': '4 GB Capacity', 'price_modifier': 0},
                    {'name': '8 GB Capacity', 'price_modifier': 50},
                    {'name': '16 GB Capacity', 'price_modifier': 125},
                    {'name': '32 GB Capacity', 'price_modifier': 250}
                ],
                'available_papers': [
                    {'name': 'Plastic Body', 'price_modifier': 0},
                    {'name': 'Metal Body', 'price_modifier': 150},
                    {'name': 'Wooden Body', 'price_modifier': 125}
                ],
                'color_options': [
                    {'name': 'Full Color Logo Print', 'price_modifier': 0},
                    {'name': 'Laser Engraving', 'price_modifier': 75},
                    {'name': 'Embossed Logo', 'price_modifier': 100}
                ],
                'quantity_tiers': [
                    {'min_qty': 50, 'max_qty': 99, 'discount_percent': 0},
                    {'min_qty': 100, 'max_qty': 249, 'discount_percent': 20},
                    {'min_qty': 250, 'max_qty': 499, 'discount_percent': 30},
                    {'min_qty': 500, 'max_qty': 999, 'discount_percent': 40}
                ],
                'key_features': [
                    {'title': 'Data Preloading', 'description': 'Your content loaded before shipping'},
                    {'title': 'Custom Packaging', 'description': 'Branded boxes and pouches available'},
                    {'title': 'Quality Guarantee', 'description': '2-year warranty on all drives'}
                ],
                'specifications': {
                    'Interface': 'USB 2.0/3.0 options',
                    'Compatibility': 'Windows, Mac, Linux compatible',
                    'Warranty': '2 years manufacturer warranty',
                    'Data Services': 'Content loading and autorun setup'
                }
            },

            # Stationery (6 products)
            {
                'name': 'Business Cards',
                'category': 'Stationery',
                'description': 'Professional business cards with premium finishes and high-quality printing.',
                'short_description': 'Professional business cards with premium materials and finishes.',
                'base_price': Decimal('5.99'),
                'price_unit': 'per 100 cards',
                'design_tool_enabled': True,
                'canvas_width': 1050,
                'canvas_height': 600,  # 3.5x2 inches at 300 DPI
                'available_sizes': [
                    {'name': '3.5x2 inches (Standard)', 'price_modifier': 0},
                    {'name': '3.5x2.5 inches (European)', 'price_modifier': 50}
                ],
                'available_papers': [
                    {'name': '300 GSM Art Card', 'price_modifier': 0},
                    {'name': '350 GSM Art Card', 'price_modifier': 100},
                    {'name': '400 GSM Premium Card', 'price_modifier': 200},
                    {'name': 'Premium Plastic (PVC)', 'price_modifier': 500}
                ],
                'available_finishes': [
                    {'name': 'Matte Lamination', 'price_modifier': 150},
                    {'name': 'Gloss Lamination', 'price_modifier': 150},
                    {'name': 'Soft Touch Lamination', 'price_modifier': 250},
                    {'name': 'Spot UV', 'price_modifier': 300},
                    {'name': 'Foil Stamping', 'price_modifier': 400}
                ],
                'color_options': [
                    {'name': 'Full Color (4+4)', 'price_modifier': 0},
                    {'name': 'Full Color + Spot UV', 'price_modifier': 200},
                    {'name': 'Full Color + Foil', 'price_modifier': 300}
                ],
                'quantity_tiers': [
                    {'min_qty': 100, 'max_qty': 249, 'discount_percent': 0},
                    {'min_qty': 250, 'max_qty': 499, 'discount_percent': 8},
                    {'min_qty': 500, 'max_qty': 999, 'discount_percent': 17},
                    {'min_qty': 1000, 'max_qty': 2499, 'discount_percent': 25},
                    {'min_qty': 2500, 'max_qty': 4999, 'discount_percent': 33}
                ],
                'key_features': [
                    {'title': 'Premium Materials', 'description': 'High-quality card stocks and finishes'},
                    {'title': 'Design Tools', 'description': 'Online design tool with templates'},
                    {'title': 'Fast Turnaround', 'description': '2-3 business days standard delivery'}
                ],
                'specifications': {
                    'Standard Size': '3.5x2 inches (89x51mm)',
                    'Material Options': '300-400 GSM card stock, PVC plastic',
                    'Print Process': 'Digital or offset printing',
                    'Special Features': 'Rounded corners, die-cutting available'
                }
            },
            {
                'name': 'Letterheads',
                'category': 'Stationery',
                'description': 'Professional letterheads with company branding for business correspondence.',
                'short_description': 'Professional branded letterheads for business correspondence.',
                'base_price': Decimal('1.85'),
                'price_unit': 'per 100 sheets',
                'design_tool_enabled': True,
                'canvas_width': 2550,
                'canvas_height': 3300,  # 8.5x11 at 300 DPI
                'available_sizes': [
                    {'name': '8.5x11 inches (Letter)', 'price_modifier': 0},
                    {'name': 'A4 (210x297mm)', 'price_modifier': 25}
                ],
                'available_papers': [
                    {'name': '80 GSM Bond Paper', 'price_modifier': 0},
                    {'name': '100 GSM Text Paper', 'price_modifier': 50},
                    {'name': '120 GSM Premium Paper', 'price_modifier': 100},
                    {'name': '24lb Linen Paper', 'price_modifier': 150}
                ],
                'color_options': [
                    {'name': 'Single Color', 'price_modifier': 0},
                    {'name': '2 Colors', 'price_modifier': 75},
                    {'name': 'Full Color (4+0)', 'price_modifier': 150}
                ],
                'quantity_tiers': [
                    {'min_qty': 100, 'max_qty': 249, 'discount_percent': 0},
                    {'min_qty': 250, 'max_qty': 499, 'discount_percent': 15},
                    {'min_qty': 500, 'max_qty': 999, 'discount_percent': 25},
                    {'min_qty': 1000, 'max_qty': 2499, 'discount_percent': 35},
                    {'min_qty': 2500, 'max_qty': 4999, 'discount_percent': 45}
                ],
                'key_features': [
                    {'title': 'Professional Branding', 'description': 'Consistent company image across correspondence'},
                    {'title': 'High-Quality Papers', 'description': 'Premium paper options for professional feel'},
                    {'title': 'Matching Stationery', 'description': 'Coordinate with business cards and envelopes'}
                ],
                'specifications': {
                    'Paper Weight': '80-120 GSM options',
                    'Print Area': 'Full page with margins',
                    'File Format': 'PDF with proper margins',
                    'Uses': 'Business letters, invoices, formal correspondence'
                }
            },
            {
                'name': 'Envelopes',
                'category': 'Stationery',
                'description': 'Custom printed envelopes in various sizes with professional branding options.',
                'short_description': 'Custom printed business envelopes with professional branding.',
                'base_price': Decimal('1.25'),
                'price_unit': 'per 100 envelopes',
                'design_tool_enabled': False,
                'available_sizes': [
                    {'name': '#10 (4.125x9.5 inches)', 'price_modifier': 0},
                    {'name': '6x9 inches (Booklet)', 'price_modifier': 25},
                    {'name': '9x12 inches (Catalog)', 'price_modifier': 75},
                    {'name': 'A4 (C4) European', 'price_modifier': 50}
                ],
                'available_papers': [
                    {'name': '80 GSM Envelope Paper', 'price_modifier': 0},
                    {'name': '100 GSM Premium Paper', 'price_modifier': 35},
                    {'name': '120 GSM Heavy Paper', 'price_modifier': 75}
                ],
                'color_options': [
                    {'name': 'Single Color', 'price_modifier': 0},
                    {'name': '2 Colors', 'price_modifier': 50},
                    {'name': 'Full Color (4+0)', 'price_modifier': 125}
                ],
                'quantity_tiers': [
                    {'min_qty': 100, 'max_qty': 249, 'discount_percent': 0},
                    {'min_qty': 250, 'max_qty': 499, 'discount_percent': 18},
                    {'min_qty': 500, 'max_qty': 999, 'discount_percent': 28},
                    {'min_qty': 1000, 'max_qty': 2499, 'discount_percent': 38},
                    {'min_qty': 2500, 'max_qty': 4999, 'discount_percent': 48}
                ],
                'key_features': [
                    {'title': 'Professional Appearance', 'description': 'Custom branding for business mail'},
                    {'title': 'Multiple Sizes', 'description': 'Standard business and large catalog sizes'},
                    {'title': 'Window Options', 'description': 'Clear windows for address visibility'}
                ],
                'specifications': {
                    'Closure': 'Gummed flap standard',
                    'Window Options': 'Left or right window placement',
                    'Security': 'Security tint available',
                    'USPS Compliance': 'All sizes meet postal requirements'
                }
            },
            {
                'name': 'Bill Books',
                'category': 'Stationery',
                'description': 'Professional invoice books and receipt books with carbon copies and numbering.',
                'short_description': 'Professional invoice and receipt books with carbon copies.',
                'base_price': Decimal('12.50'),
                'price_unit': 'per book',
                'design_tool_enabled': True,
                'canvas_width': 1240,
                'canvas_height': 1754,  # A5 at 300 DPI
                'available_sizes': [
                    {'name': 'A5 (5.8x8.3 inches)', 'price_modifier': 0},
                    {'name': 'A4 (8.3x11.7 inches)', 'price_modifier': 75},
                    {'name': '4x6 inches (Small)', 'price_modifier': -25}
                ],
                'available_papers': [
                    {'name': '80 GSM NCR Paper (2-part)', 'price_modifier': 0},
                    {'name': '80 GSM NCR Paper (3-part)', 'price_modifier': 125},
                    {'name': '100 GSM NCR Paper (2-part)', 'price_modifier': 75}
                ],
                'color_options': [
                    {'name': 'Single Color', 'price_modifier': 0},
                    {'name': '2 Colors', 'price_modifier': 100},
                    {'name': 'Full Color (First Sheet Only)', 'price_modifier': 200}
                ],
                'quantity_tiers': [
                    {'min_qty': 25, 'max_qty': 49, 'discount_percent': 0},
                    {'min_qty': 50, 'max_qty': 99, 'discount_percent': 12},
                    {'min_qty': 100, 'max_qty': 249, 'discount_percent': 22},
                    {'min_qty': 250, 'max_qty': 499, 'discount_percent': 32}
                ],
                'key_features': [
                    {'title': 'Sequential Numbering', 'description': 'Pre-numbered for record keeping'},
                    {'title': 'Carbon Copies', 'description': '2 or 3-part NCR paper options'},
                    {'title': 'Professional Layout', 'description': 'Custom design with your business details'}
                ],
                'specifications': {
                    'Sheets per Book': '50 or 100 sets',
                    'Paper Type': 'NCR (No Carbon Required)',
                    'Binding': 'Pad glued at top',
                    'Numbering': 'Sequential numbering included'
                }
            },
            {
                'name': 'ID Cards',
                'category': 'Stationery',
                'description': 'Professional employee ID cards with security features and durable materials.',
                'short_description': 'Professional employee ID cards with security features.',
                'base_price': Decimal('2.50'),
                'price_unit': 'per card',
                'design_tool_enabled': False,
                'available_sizes': [
                    {'name': '3.375x2.125 inches (CR80)', 'price_modifier': 0},
                    {'name': '3.5x2.5 inches (Custom)', 'price_modifier': 25}
                ],
                'available_papers': [
                    {'name': 'PVC Plastic (30 mil)', 'price_modifier': 0},
                    {'name': 'Teslin Synthetic (10 mil)', 'price_modifier': -50},
                    {'name': 'Premium PVC (40 mil)', 'price_modifier': 75}
                ],
                'available_finishes': [
                    {'name': 'Standard Print', 'price_modifier': 0},
                    {'name': 'Magnetic Stripe', 'price_modifier': 150},
                    {'name': 'Barcode/QR Code', 'price_modifier': 100},
                    {'name': 'RFID Chip', 'price_modifier': 500}
                ],
                'color_options': [
                    {'name': 'Full Color (4+4)', 'price_modifier': 0}
                ],
                'quantity_tiers': [
                    {'min_qty': 50, 'max_qty': 99, 'discount_percent': 0},
                    {'min_qty': 100, 'max_qty': 249, 'discount_percent': 15},
                    {'min_qty': 250, 'max_qty': 499, 'discount_percent': 25},
                    {'min_qty': 500, 'max_qty': 999, 'discount_percent': 35}
                ],
                'key_features': [
                    {'title': 'Photo Quality', 'description': 'High-resolution photo printing'},
                    {'title': 'Security Features', 'description': 'Holographic overlays and RFID options'},
                    {'title': 'Durable Materials', 'description': 'Water and tear resistant PVC'}
                ],
                'specifications': {
                    'Standard Size': 'CR80 (credit card size)',
                    'Thickness': '30 mil (0.76mm) standard',
                    'Features': 'Photo, text, barcodes, magnetic stripe',
                    'Durability': '3-5 year outdoor rated'
                }
            },
            {
                'name': 'Stickers',
                'category': 'Stationery',
                'description': 'Custom printed stickers and labels in various shapes and materials.',
                'short_description': 'Custom printed stickers and labels in various shapes and materials.',
                'base_price': Decimal('0.45'),
                'price_unit': 'per sticker',
                'design_tool_enabled': True,
                'canvas_width': 600,
                'canvas_height': 600,  # 2x2 inches at 300 DPI
                'available_sizes': [
                    {'name': '2x2 inches (Square)', 'price_modifier': 0},
                    {'name': '3x3 inches (Square)', 'price_modifier': 25},
                    {'name': '4x4 inches (Square)', 'price_modifier': 50},
                    {'name': '2x4 inches (Rectangle)', 'price_modifier': 35},
                    {'name': 'Circle (2 inches diameter)', 'price_modifier': 15}
                ],
                'available_papers': [
                    {'name': 'White Vinyl', 'price_modifier': 0},
                    {'name': 'Clear Vinyl', 'price_modifier': 50},
                    {'name': 'Waterproof Vinyl', 'price_modifier': 75},
                    {'name': 'Removable Adhesive', 'price_modifier': 35}
                ],
                'available_finishes': [
                    {'name': 'Matte Finish', 'price_modifier': 0},
                    {'name': 'Gloss Finish', 'price_modifier': 25},
                    {'name': 'UV Resistant', 'price_modifier': 50}
                ],
                'color_options': [
                    {'name': 'Full Color (4+0)', 'price_modifier': 0},
                    {'name': 'White Ink (for clear vinyl)', 'price_modifier': 100}
                ],
                'quantity_tiers': [
                    {'min_qty': 100, 'max_qty': 249, 'discount_percent': 0},
                    {'min_qty': 250, 'max_qty': 499, 'discount_percent': 20},
                    {'min_qty': 500, 'max_qty': 999, 'discount_percent': 35},
                    {'min_qty': 1000, 'max_qty': 2499, 'discount_percent': 45},
                    {'min_qty': 2500, 'max_qty': 4999, 'discount_percent': 55}
                ],
                'key_features': [
                    {'title': 'Weather Resistant', 'description': 'Outdoor-rated vinyl materials'},
                    {'title': 'Custom Shapes', 'description': 'Die-cutting for unique shapes'},
                    {'title': 'Strong Adhesive', 'description': 'Permanent or removable options'}
                ],
                'specifications': {
                    'Material': 'Premium vinyl with UV protection',
                    'Adhesive': 'Permanent or removable options',
                    'Outdoor Life': '3-5 years',
                    'Applications': 'Indoor/outdoor use, promotional, branding'
                }
            },

            # Documents (1 product)
            {
                'name': 'Document Printing',
                'category': 'Documents',
                'description': 'Professional document printing services including reports, manuals, and presentations.',
                'short_description': 'Professional document printing for reports, manuals, and presentations.',
                'base_price': Decimal('0.25'),
                'price_unit': 'per page',
                'design_tool_enabled': False,
                'available_sizes': [
                    {'name': '8.5x11 inches (Letter)', 'price_modifier': 0},
                    {'name': '8.5x14 inches (Legal)', 'price_modifier': 15},
                    {'name': '11x17 inches (Tabloid)', 'price_modifier': 50},
                    {'name': 'A4 (210x297mm)', 'price_modifier': 10}
                ],
                'available_papers': [
                    {'name': '20lb White Bond', 'price_modifier': 0},
                    {'name': '24lb White Bond', 'price_modifier': 15},
                    {'name': '28lb Premium Paper', 'price_modifier': 35},
                    {'name': '32lb Heavy Paper', 'price_modifier': 50}
                ],
                'available_bindings': [
                    {'name': 'No Binding (Loose)', 'price_modifier': 0},
                    {'name': 'Staple (Corner)', 'price_modifier': 5},
                    {'name': 'Staple (Side)', 'price_modifier': 10},
                    {'name': 'Coil Binding', 'price_modifier': 150},
                    {'name': 'Comb Binding', 'price_modifier': 125},
                    {'name': '3-Hole Punch', 'price_modifier': 25}
                ],
                'color_options': [
                    {'name': 'Black & White', 'price_modifier': 0},
                    {'name': 'Color Pages', 'price_modifier': 200}
                ],
                'quantity_tiers': [
                    {'min_qty': 1, 'max_qty': 99, 'discount_percent': 0},
                    {'min_qty': 100, 'max_qty': 499, 'discount_percent': 15},
                    {'min_qty': 500, 'max_qty': 999, 'discount_percent': 25},
                    {'min_qty': 1000, 'max_qty': 4999, 'discount_percent': 35},
                    {'min_qty': 5000, 'max_qty': 9999, 'discount_percent': 45}
                ],
                'key_features': [
                    {'title': 'Same Day Service', 'description': 'Rush printing available for urgent documents'},
                    {'title': 'Professional Binding', 'description': 'Multiple binding options for presentations'},
                    {'title': 'High Volume Pricing', 'description': 'Excellent rates for large document sets'}
                ],
                'specifications': {
                    'Print Quality': '600x600 DPI laser printing',
                    'Page Limits': 'Up to 500 pages per document',
                    'File Formats': 'PDF, Word, PowerPoint accepted',
                    'Same Day': 'Orders by 2 PM for same-day pickup'
                }
            }
        ]

        # Create products
        created_count = 0
        for product_data in products_data:
            category = categories[product_data['category']]

            # Check if product already exists
            existing_product = StaticProduct.objects.filter(
                name=product_data['name'],
                category=category
            ).first()

            if existing_product:
                self.stdout.write(f'Product already exists: {product_data["name"]}')
                continue

            # Create new product
            product = StaticProduct.objects.create(
                name=product_data['name'],
                slug=slugify(product_data['name']),
                category=category,
                description=product_data['description'],
                short_description=product_data['short_description'],
                base_price=product_data['base_price'],
                price_unit=product_data['price_unit'],
                design_tool_enabled=product_data['design_tool_enabled'],
                canvas_width=product_data.get('canvas_width'),
                canvas_height=product_data.get('canvas_height'),
                available_sizes=product_data.get('available_sizes', []),
                available_papers=product_data.get('available_papers', []),
                available_finishes=product_data.get('available_finishes', []),
                available_bindings=product_data.get('available_bindings', []),
                color_options=product_data.get('color_options', []),
                quantity_tiers=product_data.get('quantity_tiers', []),
                key_features=product_data.get('key_features', []),
                specifications=product_data.get('specifications', {}),
                is_active=True,
                is_featured=product_data['design_tool_enabled'],  # Featured if has design tool
                order=created_count
            )

            created_count += 1
            self.stdout.write(self.style.SUCCESS(f'Created product: {product.name}'))

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} static products!')
        )

        # Summary statistics
        total_products = StaticProduct.objects.count()
        design_tool_products = StaticProduct.objects.filter(design_tool_enabled=True).count()

        self.stdout.write(f'\nSummary:')
        self.stdout.write(f'Total products in database: {total_products}')
        self.stdout.write(f'Products with design tool: {design_tool_products}')
        self.stdout.write(f'Categories: {ServiceCategory.objects.count()}')