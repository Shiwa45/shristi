
from django.test import TestCase
from django.urls import reverse
from apps.services.models import ServiceCategory, StaticProduct

class CoreViewsTest(TestCase):
    def setUp(self):
        self.category = ServiceCategory.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.product = StaticProduct.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            design_tool_enabled=True,
            base_price=100,
            featured_image='products/featured/test.jpg'
        )

    def test_home_page_uses_featured_image(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Product')
        self.assertContains(response, 'test.jpg')
