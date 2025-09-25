#!/usr/bin/env python3
"""
Import products from Creative Print Arts into the Django database
Based on the product structure and pricing from creativeprintarts.com
"""

import os
import sys
import django
from decimal import Decimal

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shirsti_printing.settings')
django.setup()

from apps.services.models import (
    ServiceCategory, Product, ProductPricing, ProductSpecification,
    ProductImage, ShippingOption
)

def create_categories():
    """Create service categories based on Creative Print Arts"""
    categories_data = [
        {
            'name': 'Book Printing',
            'slug': 'book-printing',
            'description': 'Professional book printing services with various binding options and paper types',
            'icon': 'fas fa-book',
            'is_featured': True,
            'order': 1
        },
        {
            'name': 'Document Printing',
            'slug': 'document-printing',
            'description': 'High-quality document printing for business and personal use',
            'icon': 'fas fa-file-alt',
            'is_featured': True,
            'order': 2
        },
        {
            'name': 'Business Cards',
            'slug': 'business-cards',
            'description': 'Professional business cards with various finishes and paper options',
            'icon': 'fas fa-id-card',
            'is_featured': True,
            'order': 3
        },
        {
            'name': 'Letter Heads',
            'slug': 'letter-heads',
            'description': 'Custom letterheads for corporate and professional use',
            'icon': 'fas fa-envelope',
            'is_featured': False,
            'order': 4
        },
        {
            'name': 'Bill Books',
            'slug': 'bill-books',
            'description': 'Customized bill books and receipt books for businesses',
            'icon': 'fas fa-receipt',
            'is_featured': False,
            'order': 5
        },
        {
            'name': 'Stickers',
            'slug': 'stickers',
            'description': 'Custom stickers and labels in various shapes and sizes',
            'icon': 'fas fa-tags',
            'is_featured': False,
            'order': 6
        }
    ]

    created_categories = {}
    for cat_data in categories_data:
        category, created = ServiceCategory.objects.get_or_create(
            slug=cat_data['slug'],
            defaults=cat_data
        )
        created_categories[cat_data['slug']] = category
        if created:
            print(f"Created category: {category.name}")
        else:
            print(f"Category already exists: {category.name}")

    return created_categories

def create_products(categories):
    """Create products based on Creative Print Arts offerings"""
    products_data = [
        # Book Printing Products
        {
            'name': 'Paperback Book Printing',
            'slug': 'paperback-book-printing',
            'category': categories['book-printing'],
            'description': 'High-quality paperback book printing with perfect binding. Ideal for novels, non-fiction books, and educational materials.',
            'short_description': 'Professional paperback books with perfect binding',
            'hero_title': 'Professional Paperback Book Printing',
            'hero_subtitle': 'Transform your manuscript into a beautifully printed paperback book',
            'hero_quote': 'From manuscript to masterpiece - quality printing you can trust',
            'width_mm': 148,
            'height_mm': 210,  # A5 size
            'bleed_mm': 3.0,
            'safe_zone_mm': 5.0,
            'dpi': 300,
            'has_design_tool': True,
            'allows_upload': True,
            'allows_custom_size': True,
            'base_price': 50.00,
            'price_per_unit': 8.00,
            'minimum_quantity': 25,
            'meta_title': 'Paperback Book Printing Services - Quality & Affordable',
            'is_active': True,
            'is_featured': True,
            'order': 1,
            'express_production': True,
            'bulk_discount_text': 'Save up to 20% on orders over 500 copies',
            'trust_badges': 'Quality Guaranteed,Fast Delivery,Eco-Friendly'
        },
        {
            'name': 'Hardcover Book Printing',
            'slug': 'hardcover-book-printing',
            'category': categories['book-printing'],
            'description': 'Premium hardcover book printing with dust jacket options. Perfect for coffee table books, memoirs, and special editions.',
            'short_description': 'Premium hardcover books with dust jacket options',
            'hero_title': 'Premium Hardcover Book Printing',
            'hero_subtitle': 'Create lasting impressions with professional hardcover books',
            'hero_quote': 'Durability meets elegance in every hardcover book',
            'width_mm': 148,
            'height_mm': 210,
            'bleed_mm': 3.0,
            'safe_zone_mm': 5.0,
            'dpi': 300,
            'has_design_tool': True,
            'allows_upload': True,
            'allows_custom_size': True,
            'base_price': 100.00,
            'price_per_unit': 15.00,
            'minimum_quantity': 25,
            'meta_title': 'Hardcover Book Printing - Premium Quality Books',
            'is_active': True,
            'is_featured': True,
            'order': 2,
            'express_production': False,
            'bulk_discount_text': 'Save up to 15% on orders over 300 copies',
            'trust_badges': 'Premium Quality,Durable Binding,Professional Finish'
        },
        # Document Printing
        {
            'name': 'Document Printing A4',
            'slug': 'document-printing-a4',
            'category': categories['document-printing'],
            'description': 'Professional A4 document printing for reports, presentations, and official documents. Available in color and black & white.',
            'short_description': 'Professional A4 document printing in color and B&W',
            'hero_title': 'Professional Document Printing',
            'hero_subtitle': 'High-quality printing for all your business documents',
            'hero_quote': 'Clear, crisp documents that make an impact',
            'width_mm': 210,
            'height_mm': 297,  # A4 size
            'bleed_mm': 0,
            'safe_zone_mm': 10.0,
            'dpi': 600,
            'has_design_tool': False,
            'allows_upload': True,
            'allows_custom_size': False,
            'base_price': 0.00,
            'price_per_unit': 2.00,
            'minimum_quantity': 1,
            'meta_title': 'A4 Document Printing Services - Fast & Reliable',
            'is_active': True,
            'is_featured': True,
            'order': 1,
            'express_production': True,
            'bulk_discount_text': 'Volume discounts available for orders over 1000 sheets',
            'trust_badges': 'Same Day Delivery,High Resolution,Eco Paper'
        },
        # Business Cards
        {
            'name': 'Standard Business Cards',
            'slug': 'standard-business-cards',
            'category': categories['business-cards'],
            'description': 'Professional business cards on quality paper with various finish options. Standard size with full-color printing.',
            'short_description': 'Professional business cards with quality finishes',
            'hero_title': 'Professional Business Cards',
            'hero_subtitle': 'Make a lasting first impression with quality business cards',
            'hero_quote': 'Your brand in your hands - premium business cards',
            'width_mm': 85,
            'height_mm': 55,  # Standard business card
            'bleed_mm': 2.0,
            'safe_zone_mm': 3.0,
            'dpi': 300,
            'has_design_tool': True,
            'allows_upload': True,
            'allows_custom_size': False,
            'base_price': 50.00,
            'price_per_unit': 1.50,
            'minimum_quantity': 100,
            'meta_title': 'Business Card Printing - Professional & Affordable',
            'is_active': True,
            'is_featured': True,
            'order': 1,
            'express_production': True,
            'bulk_discount_text': 'Better rates for quantities over 500',
            'trust_badges': 'Free Design Support,Multiple Finishes,Quick Turnaround'
        },
        {
            'name': 'Premium Business Cards',
            'slug': 'premium-business-cards',
            'category': categories['business-cards'],
            'description': 'Premium business cards with special finishes like spot UV, embossing, and foil stamping. Made with thick card stock.',
            'short_description': 'Premium business cards with special finishes',
            'hero_title': 'Premium Business Cards',
            'hero_subtitle': 'Stand out with luxury finishes and premium materials',
            'hero_quote': 'Elevate your brand with premium business cards',
            'width_mm': 85,
            'height_mm': 55,
            'bleed_mm': 2.0,
            'safe_zone_mm': 3.0,
            'dpi': 300,
            'has_design_tool': True,
            'allows_upload': True,
            'allows_custom_size': False,
            'base_price': 100.00,
            'price_per_unit': 3.50,
            'minimum_quantity': 100,
            'meta_title': 'Premium Business Cards - Luxury Finishes Available',
            'is_active': True,
            'is_featured': True,
            'order': 2,
            'express_production': False,
            'bulk_discount_text': 'Premium discounts available for bulk orders',
            'trust_badges': 'Luxury Finishes,Thick Card Stock,Designer Support'
        },
        # Letter Heads
        {
            'name': 'Corporate Letterhead',
            'slug': 'corporate-letterhead',
            'category': categories['letter-heads'],
            'description': 'Professional corporate letterheads printed on premium paper. Perfect for official correspondence and business communications.',
            'short_description': 'Professional letterheads for corporate use',
            'hero_title': 'Corporate Letterhead Printing',
            'hero_subtitle': 'Professional letterheads that represent your brand',
            'hero_quote': 'Every letter tells your brand story',
            'width_mm': 210,
            'height_mm': 297,  # A4 size
            'bleed_mm': 3.0,
            'safe_zone_mm': 10.0,
            'dpi': 300,
            'has_design_tool': True,
            'allows_upload': True,
            'allows_custom_size': False,
            'base_price': 100.00,
            'price_per_unit': 4.00,
            'minimum_quantity': 100,
            'meta_title': 'Corporate Letterhead Printing - Professional Quality',
            'is_active': True,
            'is_featured': False,
            'order': 1,
            'express_production': True,
            'bulk_discount_text': 'Volume pricing available for corporate orders',
            'trust_badges': 'Premium Paper,Professional Design,Fast Delivery'
        }
    ]

    created_products = {}
    for prod_data in products_data:
        product, created = Product.objects.get_or_create(
            slug=prod_data['slug'],
            defaults=prod_data
        )
        created_products[prod_data['slug']] = product
        if created:
            print(f"Created product: {product.name}")
        else:
            print(f"Product already exists: {product.name}")

    return created_products

def create_pricing_tiers(products):
    """Create detailed pricing tiers for all products"""

    # Paperback Book Pricing
    paperback_pricing = [
        {
            'product': products['paperback-book-printing'],
            'size': 'A5 (5.83 x 8.27 in)',
            'page_count': 50,
            'paper_type': '75 GSM White Paper',
            'binding_type': 'Perfect Bound',
            'finish': 'Matte',
            'colors': 'Black & White Interior',
            'cover_finish': 'Matte Lamination',
            'min_quantity': 25,
            'max_quantity': 99,
            'price_per_unit': Decimal('12.00'),
            'setup_cost': Decimal('500.00'),
            'turnaround_days': 7,
            'is_featured': True
        },
        {
            'product': products['paperback-book-printing'],
            'size': 'A5 (5.83 x 8.27 in)',
            'page_count': 50,
            'paper_type': '75 GSM White Paper',
            'binding_type': 'Perfect Bound',
            'finish': 'Matte',
            'colors': 'Black & White Interior',
            'cover_finish': 'Matte Lamination',
            'min_quantity': 100,
            'max_quantity': 299,
            'price_per_unit': Decimal('10.00'),
            'setup_cost': Decimal('500.00'),
            'volume_discount_percentage': Decimal('10.00'),
            'turnaround_days': 7
        },
        {
            'product': products['paperback-book-printing'],
            'size': 'A5 (5.83 x 8.27 in)',
            'page_count': 100,
            'paper_type': '100 GSM White Paper',
            'binding_type': 'Perfect Bound',
            'finish': 'Matte',
            'colors': 'Full Color Interior',
            'cover_finish': 'Glossy Lamination',
            'min_quantity': 50,
            'max_quantity': 199,
            'price_per_unit': Decimal('18.00'),
            'setup_cost': Decimal('750.00'),
            'turnaround_days': 10
        }
    ]

    # Hardcover Book Pricing
    hardcover_pricing = [
        {
            'product': products['hardcover-book-printing'],
            'size': 'A5 (5.83 x 8.27 in)',
            'page_count': 100,
            'paper_type': '100 GSM Art Paper',
            'binding_type': 'Hard Cover',
            'finish': 'Premium',
            'colors': 'Full Color Interior',
            'cover_finish': 'Dust Jacket',
            'min_quantity': 25,
            'max_quantity': 99,
            'price_per_unit': Decimal('25.00'),
            'setup_cost': Decimal('1000.00'),
            'turnaround_days': 14,
            'is_featured': True
        },
        {
            'product': products['hardcover-book-printing'],
            'size': 'A4 (8.27 x 11.69 in)',
            'page_count': 150,
            'paper_type': '130 GSM Art Paper',
            'binding_type': 'Hard Cover',
            'finish': 'Premium',
            'colors': 'Full Color Interior',
            'cover_finish': 'Cloth Hardcover',
            'min_quantity': 50,
            'max_quantity': 199,
            'price_per_unit': Decimal('35.00'),
            'setup_cost': Decimal('1500.00'),
            'turnaround_days': 21
        }
    ]

    # Document Printing Pricing
    document_pricing = [
        {
            'product': products['document-printing-a4'],
            'size': 'A4 (8.27 x 11.69 in)',
            'page_count': 1,
            'paper_type': '80 GSM White Paper',
            'binding_type': 'Loose Sheets',
            'colors': 'Black & White',
            'print_sides': 'Single-sided',
            'min_quantity': 1,
            'max_quantity': 99,
            'price_per_unit': Decimal('3.00'),
            'setup_cost': Decimal('0.00'),
            'turnaround_days': 1,
            'is_featured': True
        },
        {
            'product': products['document-printing-a4'],
            'size': 'A4 (8.27 x 11.69 in)',
            'page_count': 1,
            'paper_type': '80 GSM White Paper',
            'binding_type': 'Loose Sheets',
            'colors': 'Full Color',
            'print_sides': 'Single-sided',
            'min_quantity': 1,
            'max_quantity': 99,
            'price_per_unit': Decimal('8.00'),
            'setup_cost': Decimal('0.00'),
            'turnaround_days': 1
        },
        {
            'product': products['document-printing-a4'],
            'size': 'A4 (8.27 x 11.69 in)',
            'page_count': 1,
            'paper_type': '80 GSM White Paper',
            'binding_type': 'Spiral Binding',
            'colors': 'Black & White',
            'print_sides': 'Double-sided',
            'min_quantity': 25,
            'max_quantity': 199,
            'price_per_unit': Decimal('5.50'),
            'setup_cost': Decimal('50.00'),
            'turnaround_days': 2
        }
    ]

    # Business Cards Pricing
    business_card_pricing = [
        {
            'product': products['standard-business-cards'],
            'size': 'Standard (85 x 55 mm)',
            'paper_type': '300 GSM Art Card',
            'binding_type': 'Cut to Size',
            'finish': 'Matte',
            'colors': 'Full Color',
            'print_sides': 'Double-sided',
            'min_quantity': 100,
            'max_quantity': 499,
            'price_per_unit': Decimal('2.50'),
            'setup_cost': Decimal('200.00'),
            'turnaround_days': 3,
            'is_featured': True
        },
        {
            'product': products['standard-business-cards'],
            'size': 'Standard (85 x 55 mm)',
            'paper_type': '300 GSM Art Card',
            'binding_type': 'Cut to Size',
            'finish': 'Glossy',
            'colors': 'Full Color',
            'print_sides': 'Double-sided',
            'min_quantity': 500,
            'max_quantity': 999,
            'price_per_unit': Decimal('2.00'),
            'setup_cost': Decimal('200.00'),
            'volume_discount_percentage': Decimal('15.00'),
            'turnaround_days': 3
        },
        {
            'product': products['premium-business-cards'],
            'size': 'Standard (85 x 55 mm)',
            'paper_type': '400 GSM Premium Card',
            'binding_type': 'Cut to Size',
            'finish': 'Spot UV',
            'colors': 'Full Color',
            'print_sides': 'Double-sided',
            'optional_finishing': 'Spot UV Coating',
            'min_quantity': 100,
            'max_quantity': 499,
            'price_per_unit': Decimal('5.50'),
            'setup_cost': Decimal('500.00'),
            'turnaround_days': 7,
            'is_featured': True
        }
    ]

    # Corporate Letterhead Pricing
    letterhead_pricing = [
        {
            'product': products['corporate-letterhead'],
            'size': 'A4 (8.27 x 11.69 in)',
            'paper_type': '100 GSM Premium Paper',
            'binding_type': 'Loose Sheets',
            'finish': 'Premium',
            'colors': 'Full Color',
            'print_sides': 'Single-sided',
            'min_quantity': 100,
            'max_quantity': 499,
            'price_per_unit': Decimal('6.00'),
            'setup_cost': Decimal('300.00'),
            'turnaround_days': 3,
            'is_featured': True
        },
        {
            'product': products['corporate-letterhead'],
            'size': 'A4 (8.27 x 11.69 in)',
            'paper_type': '120 GSM Premium Paper',
            'binding_type': 'Loose Sheets',
            'finish': 'Premium',
            'colors': 'Full Color',
            'print_sides': 'Single-sided',
            'optional_finishing': 'Embossing',
            'min_quantity': 500,
            'max_quantity': 999,
            'price_per_unit': Decimal('8.50'),
            'setup_cost': Decimal('300.00'),
            'volume_discount_percentage': Decimal('12.00'),
            'turnaround_days': 5
        }
    ]

    # Combine all pricing data
    all_pricing_data = (
        paperback_pricing + hardcover_pricing + document_pricing +
        business_card_pricing + letterhead_pricing
    )

    created_count = 0
    for pricing_data in all_pricing_data:
        # Create unique constraint check
        existing = ProductPricing.objects.filter(
            product=pricing_data['product'],
            size=pricing_data.get('size', ''),
            paper_type=pricing_data.get('paper_type', ''),
            binding_type=pricing_data.get('binding_type', ''),
            finish=pricing_data.get('finish', ''),
            colors=pricing_data.get('colors', ''),
            min_quantity=pricing_data['min_quantity']
        ).first()

        if not existing:
            pricing = ProductPricing.objects.create(**pricing_data)
            created_count += 1
            print(f"Created pricing: {pricing}")
        else:
            print(f"Pricing already exists: {existing}")

    print(f"Created {created_count} pricing tiers")
    return created_count

def create_shipping_options():
    """Create shipping options"""
    shipping_data = [
        {
            'name': 'Standard Delivery',
            'description': 'Standard delivery across India',
            'price': Decimal('50.00'),
            'estimated_days': 7,
            'is_express': False
        },
        {
            'name': 'Express Delivery',
            'description': 'Fast delivery for urgent orders',
            'price': Decimal('150.00'),
            'estimated_days': 3,
            'is_express': True
        },
        {
            'name': 'Metro City Express',
            'description': 'Same day delivery in metro cities',
            'price': Decimal('250.00'),
            'estimated_days': 1,
            'is_express': True
        }
    ]

    created_count = 0
    for ship_data in shipping_data:
        shipping, created = ShippingOption.objects.get_or_create(
            name=ship_data['name'],
            defaults=ship_data
        )
        if created:
            created_count += 1
            print(f"Created shipping option: {shipping.name}")
        else:
            print(f"Shipping option already exists: {shipping.name}")

    return created_count

def main():
    """Main import function"""
    print("Starting Creative Print Arts product import...")

    try:
        # Create categories
        print("\n1. Creating service categories...")
        categories = create_categories()

        # Create products
        print("\n2. Creating products...")
        products = create_products(categories)

        # Create pricing tiers
        print("\n3. Creating pricing tiers...")
        pricing_count = create_pricing_tiers(products)

        # Create shipping options
        print("\n4. Creating shipping options...")
        shipping_count = create_shipping_options()

        print(f"\n✅ Import completed successfully!")
        print(f"Categories: {len(categories)}")
        print(f"Products: {len(products)}")
        print(f"Pricing tiers: {pricing_count}")
        print(f"Shipping options: {shipping_count}")

    except Exception as e:
        print(f"Error during import: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()