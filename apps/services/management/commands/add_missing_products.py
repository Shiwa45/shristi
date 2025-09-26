# apps/services/management/commands/add_missing_products.py
from django.core.management.base import BaseCommand
from apps.services.models import Product, ServiceCategory, ProductFormField
import json


class Command(BaseCommand):
    help = 'Add missing products commonly found in Indian printing market'

    def handle(self, *args, **options):
        # Get or create categories
        categories = {}
        category_names = [
            'Books & Publications',
            'Business Stationery', 
            'Marketing Materials',
            'Packaging & Boxes',
            'Large Format Printing',
            'Specialty Items'
        ]
        
        for cat_name in category_names:
            category, created = ServiceCategory.objects.get_or_create(
                name=cat_name,
                defaults={
                    'description': f'Professional {cat_name.lower()} printing services',
                    'is_active': True,
                    'order': len(categories) + 1
                }
            )
            categories[cat_name] = category
            if created:
                self.stdout.write(f'Created category: {cat_name}')
        
        # Additional products to add
        additional_products = [
            # Large Format Printing
            {
                'name': 'Banners & Flex Printing',
                'category': 'Large Format Printing',
                'description': 'High-quality vinyl banners and flex printing for outdoor advertising',
                'base_price': 50,
                'width_mm': 1000,
                'height_mm': 2000,
                'form_fields': [
                    {
                        'field_name': 'size',
                        'field_label': 'Banner Size',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': '3x2', 'label': '3 x 2 feet', 'price_modifier': 0},
                            {'value': '4x3', 'label': '4 x 3 feet', 'price_modifier': 50},
                            {'value': '6x4', 'label': '6 x 4 feet', 'price_modifier': 150},
                            {'value': '8x6', 'label': '8 x 6 feet', 'price_modifier': 300},
                            {'value': '10x8', 'label': '10 x 8 feet', 'price_modifier': 500},
                            {'value': 'custom', 'label': 'Custom Size', 'price_modifier': 200},
                        ]),
                        'default_value': '4x3',
                        'order': 1,
                        'is_required': True,
                    },
                    {
                        'field_name': 'material',
                        'field_label': 'Material',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': 'vinyl', 'label': 'Vinyl Banner', 'price_modifier': 0},
                            {'value': 'flex', 'label': 'Flex Banner', 'price_modifier': -25},
                            {'value': 'mesh', 'label': 'Mesh Banner', 'price_modifier': 50},
                            {'value': 'fabric', 'label': 'Fabric Banner', 'price_modifier': 100},
                        ]),
                        'default_value': 'vinyl',
                        'order': 2,
                        'is_required': True,
                    },
                    {
                        'field_name': 'finishing',
                        'field_label': 'Finishing Options',
                        'field_type': 'checkbox',
                        'options': json.dumps([
                            {'value': 'eyelets', 'label': 'Eyelets for Hanging (+₹100)', 'price_modifier': 100},
                            {'value': 'hemming', 'label': 'Hemming (+₹150)', 'price_modifier': 150},
                            {'value': 'pole_pocket', 'label': 'Pole Pocket (+₹200)', 'price_modifier': 200},
                        ]),
                        'order': 3,
                        'is_required': False,
                    },
                ]
            },
            
            # Specialty Items
            {
                'name': 'Wedding Cards',
                'category': 'Specialty Items',
                'description': 'Elegant wedding invitation cards with premium finishing options',
                'base_price': 25,
                'width_mm': 150,
                'height_mm': 200,
                'form_fields': [
                    {
                        'field_name': 'quantity',
                        'field_label': 'Quantity',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': '50', 'label': '50 Cards', 'price_modifier': 0},
                            {'value': '100', 'label': '100 Cards', 'price_modifier': -0.10},
                            {'value': '200', 'label': '200 Cards', 'price_modifier': -0.20},
                            {'value': '300', 'label': '300 Cards', 'price_modifier': -0.25},
                            {'value': '500', 'label': '500 Cards', 'price_modifier': -0.30},
                        ]),
                        'default_value': '100',
                        'order': 1,
                        'is_required': True,
                    },
                    {
                        'field_name': 'card_type',
                        'field_label': 'Card Type',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': 'single', 'label': 'Single Card', 'price_modifier': 0},
                            {'value': 'folded', 'label': 'Folded Card', 'price_modifier': 100},
                            {'value': 'multi_fold', 'label': 'Multi-Fold Card', 'price_modifier': 200},
                            {'value': 'booklet', 'label': 'Wedding Booklet', 'price_modifier': 300},
                        ]),
                        'default_value': 'folded',
                        'order': 2,
                        'is_required': True,
                    },
                    {
                        'field_name': 'paper_type',
                        'field_label': 'Paper Quality',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': '250gsm_art', 'label': '250 GSM Art Card', 'price_modifier': 0},
                            {'value': '300gsm_art', 'label': '300 GSM Art Card', 'price_modifier': 100},
                            {'value': '350gsm_art', 'label': '350 GSM Art Card', 'price_modifier': 200},
                            {'value': 'handmade', 'label': 'Handmade Paper', 'price_modifier': 500},
                            {'value': 'textured', 'label': 'Textured Paper', 'price_modifier': 300},
                        ]),
                        'default_value': '300gsm_art',
                        'order': 3,
                        'is_required': True,
                    },
                    {
                        'field_name': 'finishing',
                        'field_label': 'Premium Finishing',
                        'field_type': 'checkbox',
                        'options': json.dumps([
                            {'value': 'foiling', 'label': 'Gold/Silver Foiling (+₹500)', 'price_modifier': 500},
                            {'value': 'embossing', 'label': 'Embossing (+₹400)', 'price_modifier': 400},
                            {'value': 'laser_cut', 'label': 'Laser Cutting (+₹800)', 'price_modifier': 800},
                            {'value': 'ribbon', 'label': 'Ribbon Attachment (+₹200)', 'price_modifier': 200},
                        ]),
                        'order': 4,
                        'is_required': False,
                    },
                ]
            },
            
            # Marketing Materials
            {
                'name': 'Roll-Up Standees',
                'category': 'Marketing Materials',
                'description': 'Portable roll-up banner stands for exhibitions and events',
                'base_price': 1500,
                'width_mm': 850,
                'height_mm': 2000,
                'form_fields': [
                    {
                        'field_name': 'size',
                        'field_label': 'Standee Size',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': '80x200', 'label': '80 x 200 cm', 'price_modifier': 0},
                            {'value': '85x200', 'label': '85 x 200 cm', 'price_modifier': 200},
                            {'value': '100x200', 'label': '100 x 200 cm', 'price_modifier': 500},
                            {'value': '120x200', 'label': '120 x 200 cm', 'price_modifier': 800},
                        ]),
                        'default_value': '85x200',
                        'order': 1,
                        'is_required': True,
                    },
                    {
                        'field_name': 'stand_quality',
                        'field_label': 'Stand Quality',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': 'economy', 'label': 'Economy Stand', 'price_modifier': 0},
                            {'value': 'premium', 'label': 'Premium Stand', 'price_modifier': 500},
                            {'value': 'deluxe', 'label': 'Deluxe Stand', 'price_modifier': 1000},
                        ]),
                        'default_value': 'premium',
                        'order': 2,
                        'is_required': True,
                    },
                    {
                        'field_name': 'printing',
                        'field_label': 'Print Quality',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': 'standard', 'label': 'Standard Print', 'price_modifier': 0},
                            {'value': 'hd', 'label': 'HD Print', 'price_modifier': 300},
                            {'value': 'premium', 'label': 'Premium Print', 'price_modifier': 500},
                        ]),
                        'default_value': 'hd',
                        'order': 3,
                        'is_required': True,
                    },
                ]
            },
            
            # Business Stationery
            {
                'name': 'Invoice Books',
                'category': 'Business Stationery',
                'description': 'Professional invoice books with carbon copies',
                'base_price': 150,
                'width_mm': 210,
                'height_mm': 297,
                'form_fields': [
                    {
                        'field_name': 'quantity',
                        'field_label': 'Number of Books',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': '5', 'label': '5 Books', 'price_modifier': 0},
                            {'value': '10', 'label': '10 Books', 'price_modifier': -0.10},
                            {'value': '25', 'label': '25 Books', 'price_modifier': -0.20},
                            {'value': '50', 'label': '50 Books', 'price_modifier': -0.25},
                            {'value': '100', 'label': '100 Books', 'price_modifier': -0.30},
                        ]),
                        'default_value': '10',
                        'order': 1,
                        'is_required': True,
                    },
                    {
                        'field_name': 'pages_per_book',
                        'field_label': 'Pages per Book',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': '25', 'label': '25 Sets', 'price_modifier': 0},
                            {'value': '50', 'label': '50 Sets', 'price_modifier': 100},
                            {'value': '100', 'label': '100 Sets', 'price_modifier': 200},
                        ]),
                        'default_value': '50',
                        'order': 2,
                        'is_required': True,
                    },
                    {
                        'field_name': 'copies',
                        'field_label': 'Number of Copies',
                        'field_type': 'select',
                        'options': json.dumps([
                            {'value': '2', 'label': '2 Copies (Original + 1)', 'price_modifier': 0},
                            {'value': '3', 'label': '3 Copies (Original + 2)', 'price_modifier': 50},
                            {'value': '4', 'label': '4 Copies (Original + 3)', 'price_modifier': 100},
                        ]),
                        'default_value': '3',
                        'order': 3,
                        'is_required': True,
                    },
                    {
                        'field_name': 'numbering',
                        'field_label': 'Numbering',
                        'field_type': 'checkbox',
                        'options': json.dumps([
                            {'value': 'sequential', 'label': 'Sequential Numbering (+₹200)', 'price_modifier': 200},
                        ]),
                        'order': 4,
                        'is_required': False,
                    },
                ]
            },
        ]
        
        # Create additional products
        created_products = 0
        created_fields = 0
        
        for product_data in additional_products:
            category = categories[product_data['category']]
            
            # Check if product already exists
            if Product.objects.filter(name=product_data['name']).exists():
                self.stdout.write(f'Product already exists: {product_data["name"]}')
                continue
            
            # Create product
            product = Product.objects.create(
                name=product_data['name'],
                category=category,
                description=product_data['description'],
                base_price=product_data['base_price'],
                price_per_unit=product_data['base_price'],
                width_mm=product_data['width_mm'],
                height_mm=product_data['height_mm'],
                is_active=True,
                minimum_quantity=1
            )
            created_products += 1
            
            # Create form fields
            for field_data in product_data['form_fields']:
                field_data_copy = field_data.copy()
                field_data_copy['product'] = product
                ProductFormField.objects.create(**field_data_copy)
                created_fields += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created product: {product.name}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 Successfully added:')
        )
        self.stdout.write(f'   • {created_products} new products')
        self.stdout.write(f'   • {created_fields} form fields')
        self.stdout.write(f'   • {len(category_names)} categories organized')