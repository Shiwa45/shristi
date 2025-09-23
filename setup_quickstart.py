#!/usr/bin/env python3
"""
Quick Start Script for Shirsti Printing Company Django Project
Run this script after setting up the project structure to initialize everything quickly.
"""

import os
import sys
import subprocess
import django

def run_command(command, description):
    """Run a command and display status"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def setup_django_environment():
    """Set up Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shirsti_printing.settings')
    django.setup()

def create_sample_data():
    """Create sample data programmatically"""
    from apps.services.models import ServiceCategory, Product
    from apps.core.models import HomepageSlider
    from apps.templates_mgmt.models import TemplateCategory, DesignTemplate
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    print("🔄 Creating sample data...")
    
    # Create service categories
    categories_data = [
        {
            'name': 'Business Cards',
            'slug': 'business-cards',
            'description': 'Professional business cards with various finishing options',
            'icon': 'fas fa-id-card',
            'order': 1
        },
        {
            'name': 'Marketing Materials',
            'slug': 'marketing-materials',
            'description': 'Flyers, brochures, and promotional materials',
            'icon': 'fas fa-bullhorn',
            'order': 2
        },
        {
            'name': 'Stationery',
            'slug': 'stationery',
            'description': 'Letterheads, envelopes, and office stationery',
            'icon': 'fas fa-pen',
            'order': 3
        },
        {
            'name': 'Packaging',
            'slug': 'packaging',
            'description': 'Custom boxes and packaging solutions',
            'icon': 'fas fa-box',
            'order': 4
        },
    ]
    
    for cat_data in categories_data:
        category, created = ServiceCategory.objects.get_or_create(
            slug=cat_data['slug'],
            defaults=cat_data
        )
        if created:
            print(f"  ✅ Created category: {category.name}")
    
    # Create products
    business_card_cat = ServiceCategory.objects.get(slug='business-cards')
    marketing_cat = ServiceCategory.objects.get(slug='marketing-materials')
    stationery_cat = ServiceCategory.objects.get(slug='stationery')
    
    products_data = [
        {
            'name': 'Standard Business Card',
            'slug': 'standard-business-card',
            'category': business_card_cat,
            'description': 'Professional business cards with custom design options. High-quality printing on premium cardstock.',
            'width_mm': 90,
            'height_mm': 54,
            'bleed_mm': 3,
            'safe_zone_mm': 5,
            'has_design_tool': True,
            'base_price': 29.99,
            'price_per_unit': 0.15,
            'minimum_quantity': 100,
            'is_featured': True,
        },
        {
            'name': 'Premium Business Card',
            'slug': 'premium-business-card',
            'category': business_card_cat,
            'description': 'Luxury business cards with special finishes and premium materials.',
            'width_mm': 90,
            'height_mm': 54,
            'bleed_mm': 3,
            'safe_zone_mm': 5,
            'has_design_tool': True,
            'base_price': 49.99,
            'price_per_unit': 0.25,
            'minimum_quantity': 100,
            'is_featured': True,
        },
        {
            'name': 'A4 Flyer',
            'slug': 'a4-flyer',
            'category': marketing_cat,
            'description': 'Single or double-sided A4 flyers for marketing campaigns.',
            'width_mm': 210,
            'height_mm': 297,
            'bleed_mm': 3,
            'safe_zone_mm': 5,
            'has_design_tool': True,
            'base_price': 39.99,
            'price_per_unit': 0.20,
            'minimum_quantity': 50,
            'is_featured': True,
        },
        {
            'name': 'Letterhead',
            'slug': 'letterhead',
            'category': stationery_cat,
            'description': 'Professional letterheads for business correspondence.',
            'width_mm': 210,
            'height_mm': 297,
            'bleed_mm': 3,
            'safe_zone_mm': 5,
            'has_design_tool': True,
            'base_price': 34.99,
            'price_per_unit': 0.18,
            'minimum_quantity': 50,
            'is_featured': True,
        },
    ]
    
    for prod_data in products_data:
        product, created = Product.objects.get_or_create(
            slug=prod_data['slug'],
            defaults=prod_data
        )
        if created:
            print(f"  ✅ Created product: {product.name}")
    
    # Create template categories
    template_categories_data = [
        {
            'name': 'Business',
            'slug': 'business',
            'description': 'Professional business templates',
        },
        {
            'name': 'Creative',
            'slug': 'creative',
            'description': 'Creative and artistic templates',
        },
        {
            'name': 'Minimal',
            'slug': 'minimal',
            'description': 'Clean and minimal designs',
        },
    ]
    
    for temp_cat_data in template_categories_data:
        temp_category, created = TemplateCategory.objects.get_or_create(
            slug=temp_cat_data['slug'],
            defaults=temp_cat_data
        )
        if created:
            print(f"  ✅ Created template category: {temp_category.name}")
    
    # Create homepage slider
    slider_data = [
        {
            'title': 'Professional Printing Services',
            'subtitle': 'Design, Print, Deliver',
            'description': 'Create stunning designs with our professional design tool and get them printed with premium quality.',
            'button_text': 'Start Designing',
            'button_link': '/design-tool/',
            'order': 1,
        },
        {
            'title': 'Custom Business Cards',
            'subtitle': 'Make a Lasting Impression',
            'description': 'Design professional business cards that represent your brand perfectly.',
            'button_text': 'Design Business Cards',
            'button_link': '/design-tool/product/standard-business-card/',
            'order': 2,
        },
    ]
    
    for slide_data in slider_data:
        slider, created = HomepageSlider.objects.get_or_create(
            title=slide_data['title'],
            defaults=slide_data
        )
        if created:
            print(f"  ✅ Created slider: {slider.title}")
    
    print("✅ Sample data created successfully!")

def main():
    """Main setup function"""
    print("🚀 Starting Shirsti Printing Company Django Project Setup...")
    print("=" * 60)
    
    # Check if manage.py exists
    if not os.path.exists('manage.py'):
        print("❌ manage.py not found. Please run this script from the project root directory.")
        sys.exit(1)
    
    # Run migrations
    if not run_command("python manage.py makemigrations", "Creating migrations"):
        return False
    
    if not run_command("python manage.py migrate", "Applying migrations"):
        return False
    
    # Set up Django environment
    setup_django_environment()
    
    # Create sample data
    create_sample_data()
    
    # Collect static files
    run_command("python manage.py collectstatic --noinput", "Collecting static files")
    
    print("\n" + "=" * 60)
    print("🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Create superuser: python manage.py createsuperuser")
    print("2. Run development server: python manage.py runserver")
    print("3. Visit: http://127.0.0.1:8000/")
    print("\n🔗 Important URLs:")
    print("- Homepage: http://127.0.0.1:8000/")
    print("- Design Tool: http://127.0.0.1:8000/design-tool/")
    print("- Admin Panel: http://127.0.0.1:8000/admin/")
    print("- Business Card Designer: http://127.0.0.1:8000/design-tool/product/standard-business-card/")
    print("\n💡 Tips:")
    print("- Upload some template images in the admin panel")
    print("- Configure your email settings in .env for notifications")
    print("- Add a Pixabay API key for stock image search")

if __name__ == "__main__":
    main()