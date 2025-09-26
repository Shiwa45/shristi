from django.test import TestCase, Client
from django.core.cache import cache
from django.template import Context, Template
from django.contrib.auth import get_user_model
from apps.services.models import ServiceCategory, Product
from apps.services.templatetags.services_menu_tags import services_dropdown_menu, get_services_menu_data

User = get_user_model()

class ServicesDropdownTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test categories
        self.category1 = ServiceCategory.objects.create(
            name='Book Printing',
            slug='book-printing',
            is_active=True,
            is_featured=True,
            order=1
        )
        
        self.category2 = ServiceCategory.objects.create(
            name='Business Cards',
            slug='business-cards',
            is_active=True,
            is_featured=False,
            order=2
        )
        
        # Create test products
        self.product1 = Product.objects.create(
            name='Children Book Printing',
            slug='children-book-printing',
            category=self.category1,
            description='High-quality children book printing',
            width_mm=210,
            height_mm=297,
            is_active=True,
            is_featured=True,
            price_per_unit=50.00
        )
        
        self.product2 = Product.objects.create(
            name='Standard Business Cards',
            slug='standard-business-cards',
            category=self.category2,
            description='Professional business cards',
            width_mm=85,
            height_mm=55,
            is_active=True,
            is_featured=False,
            price_per_unit=25.00
        )
        
        # Clear cache before tests
        cache.clear()
    
    def test_template_tag_returns_correct_data(self):
        """Test that the template tag returns properly structured data"""
        result = services_dropdown_menu()
        
        self.assertIn('menu_categories', result)
        self.assertEqual(len(result['menu_categories']), 2)
        
        # Check first category
        first_category = result['menu_categories'][0]
        self.assertEqual(first_category['category'].name, 'Book Printing')
        self.assertEqual(len(first_category['products']), 1)
        self.assertEqual(first_category['products'][0].name, 'Children Book Printing')
    
    def test_template_tag_caching(self):
        """Test that template tag properly caches data"""
        # First call should hit database
        result1 = services_dropdown_menu()
        
        # Second call should use cache
        result2 = services_dropdown_menu()
        
        self.assertEqual(len(result1['menu_categories']), len(result2['menu_categories']))
        
        # Verify cache key exists
        cached_data = cache.get('services_dropdown_menu_data')
        self.assertIsNotNone(cached_data)
    
    def test_context_processor_provides_menu_data(self):
        """Test that context processor provides menu data globally"""
        from apps.services.context_processors import services_menu_context
        
        # Mock request object
        class MockRequest:
            pass
        
        request = MockRequest()
        context = services_menu_context(request)
        
        self.assertIn('services_menu', context)
        self.assertIn('services_menu_count', context)
        self.assertEqual(context['services_menu_count'], 2)
    
    def test_dropdown_template_rendering(self):
        """Test that dropdown template renders correctly"""
        template = Template(
            "{% load services_menu_tags %}"
            "{% services_dropdown_menu %}"
        )
        
        rendered = template.render(Context({}))
        
        # Check that category names appear in rendered output
        self.assertIn('Book Printing', rendered)
        self.assertIn('Business Cards', rendered)
        self.assertIn('Children Book Printing', rendered)
        self.assertIn('Standard Business Cards', rendered)
    
    def test_inactive_categories_excluded(self):
        """Test that inactive categories are not included in menu"""
        # Create inactive category
        inactive_category = ServiceCategory.objects.create(
            name='Inactive Category',
            slug='inactive-category',
            is_active=False,
            order=3
        )
        
        result = services_dropdown_menu()
        category_names = [cat['category'].name for cat in result['menu_categories']]
        
        self.assertNotIn('Inactive Category', category_names)
    
    def test_categories_without_products_excluded(self):
        """Test that categories without active products are excluded"""
        # Create category without products
        empty_category = ServiceCategory.objects.create(
            name='Empty Category',
            slug='empty-category',
            is_active=True,
            order=4
        )
        
        result = services_dropdown_menu()
        category_names = [cat['category'].name for cat in result['menu_categories']]
        
        self.assertNotIn('Empty Category', category_names)
    
    def test_cache_invalidation_on_category_change(self):
        """Test that cache is cleared when categories are modified"""
        # Populate cache
        services_dropdown_menu()
        self.assertIsNotNone(cache.get('services_dropdown_menu_data'))
        
        # Modify category
        self.category1.name = 'Updated Book Printing'
        self.category1.save()
        
        # Cache should be cleared
        self.assertIsNone(cache.get('services_dropdown_menu_data'))
    
    def test_cache_invalidation_on_product_change(self):
        """Test that cache is cleared when products are modified"""
        # Populate cache
        services_dropdown_menu()
        self.assertIsNotNone(cache.get('services_dropdown_menu_data'))
        
        # Modify product
        self.product1.name = 'Updated Children Book Printing'
        self.product1.save()
        
        # Cache should be cleared
        self.assertIsNone(cache.get('services_dropdown_menu_data'))
    
    def test_featured_products_marked_correctly(self):
        """Test that featured products are properly identified"""
        result = services_dropdown_menu()
        
        # Find the featured product
        for category_data in result['menu_categories']:
            for product in category_data['products']:
                if product.name == 'Children Book Printing':
                    self.assertTrue(product.is_featured)
                elif product.name == 'Standard Business Cards':
                    self.assertFalse(product.is_featured)
    
    def test_menu_ordering(self):
        """Test that categories and products are ordered correctly"""
        result = services_dropdown_menu()
        
        # Categories should be ordered by order field, then name
        category_names = [cat['category'].name for cat in result['menu_categories']]
        self.assertEqual(category_names[0], 'Book Printing')  # order=1
        self.assertEqual(category_names[1], 'Business Cards')  # order=2
    
    def tearDown(self):
        """Clean up after tests"""
        cache.clear()