#!/usr/bin/env python
"""
Test Script for Phase 3: Design Tool Integration & Shopping Cart
This script tests the major functionality implemented in Phase 3
"""

import os
import sys
import django
import requests
from urllib.parse import urljoin

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shirsti_printing.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.services.models import ServiceCategory, StaticProduct
from apps.orders.models import Cart, CartItem
from apps.templates_mgmt.models import UserDesign, StaticProductTemplate

User = get_user_model()

class Phase3FunctionalityTest:
    """Test Phase 3 functionality"""

    def __init__(self):
        self.client = Client()
        self.base_url = 'http://localhost:8000'
        self.test_results = []

    def log_test(self, test_name, success, message=""):
        """Log test results"""
        status = "[PASS]" if success else "[FAIL]"
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message
        })
        print(f"{status}: {test_name}")
        if message:
            print(f"   └─ {message}")

    def setup_test_data(self):
        """Setup test data"""
        try:
            # Create test user
            self.user = User.objects.create_user(
                username='testuser',
                email='test@shirsti.com',
                password='testpass123'
            )

            # Create service category
            self.category = ServiceCategory.objects.create(
                name='Test Category',
                slug='test-category',
                description='Test category for Phase 3'
            )

            # Create static product
            self.product = StaticProduct.objects.create(
                name='Test Business Card',
                category=self.category,
                slug='test-business-card',
                description='Test business card product',
                base_price=99.00,
                width_mm=90,
                height_mm=54,
                design_tool_enabled=True,
                is_active=True
            )

            self.log_test("Setup test data", True, "Created user, category, and product")
            return True
        except Exception as e:
            self.log_test("Setup test data", False, str(e))
            return False

    def test_static_product_creation(self):
        """Test static product model"""
        try:
            product_count = StaticProduct.objects.count()
            self.log_test("Static Product Model", product_count > 0, f"Found {product_count} static products")
            return product_count > 0
        except Exception as e:
            self.log_test("Static Product Model", False, str(e))
            return False

    def test_cart_functionality(self):
        """Test cart functionality"""
        try:
            # Test cart creation
            cart = Cart.objects.create(user=self.user)

            # Test cart item creation
            cart_item = CartItem.objects.create(
                cart=cart,
                static_product=self.product,
                quantity=2,
                unit_price=self.product.base_price
            )

            # Test cart calculations
            subtotal = cart.subtotal
            total_items = cart.total_items

            success = (
                cart_item.quantity == 2 and
                cart_item.total_price == self.product.base_price * 2 and
                total_items == 2 and
                subtotal == self.product.base_price * 2
            )

            self.log_test("Cart Functionality", success,
                         f"Cart items: {total_items}, Subtotal: ₹{subtotal}")
            return success
        except Exception as e:
            self.log_test("Cart Functionality", False, str(e))
            return False

    def test_design_tool_integration(self):
        """Test design tool integration"""
        try:
            # Test UserDesign model
            user_design = UserDesign.objects.create(
                user=self.user,
                static_product=self.product,
                name='Test Design',
                canvas_data={'test': 'data'},
                width_mm=self.product.width_mm,
                height_mm=self.product.height_mm
            )

            # Test StaticProductTemplate model
            template = StaticProductTemplate.objects.create(
                static_product=self.product,
                name='Test Template',
                template_data={'template': 'data'},
                category='business'
            )

            success = (
                user_design.static_product == self.product and
                template.static_product == self.product
            )

            self.log_test("Design Tool Integration", success,
                         f"Created design and template for {self.product.name}")
            return success
        except Exception as e:
            self.log_test("Design Tool Integration", False, str(e))
            return False

    def test_url_patterns(self):
        """Test URL patterns are configured correctly"""
        try:
            # Test key URLs
            urls_to_test = [
                ('orders:cart', {}),
                ('design_tool:my_designs', {}),
                ('orders:quotes_list', {}),
            ]

            all_success = True
            for url_name, kwargs in urls_to_test:
                try:
                    url = reverse(url_name, kwargs=kwargs)
                    self.log_test(f"URL Pattern: {url_name}", True, f"Resolved to: {url}")
                except Exception as e:
                    self.log_test(f"URL Pattern: {url_name}", False, str(e))
                    all_success = False

            return all_success
        except Exception as e:
            self.log_test("URL Patterns", False, str(e))
            return False

    def test_template_files(self):
        """Test that template files exist"""
        try:
            import os
            from django.conf import settings

            templates_to_check = [
                'orders/cart.html',
                'orders/checkout.html',
                'orders/quote_detail.html',
                'orders/quotes_list.html',
                'design_tool/my_designs.html',
                'design_tool/static_product_editor.html',
                'services/static_products/partials/design_tool_section.html'
            ]

            all_exist = True
            for template_dir in settings.TEMPLATES[0]['DIRS']:
                for template in templates_to_check:
                    template_path = os.path.join(template_dir, template)
                    if os.path.exists(template_path):
                        self.log_test(f"Template: {template}", True, "File exists")
                    else:
                        self.log_test(f"Template: {template}", False, "File not found")
                        all_exist = False
                break  # Only check first template directory

            return all_exist
        except Exception as e:
            self.log_test("Template Files", False, str(e))
            return False

    def test_static_files(self):
        """Test that static files exist"""
        try:
            import os
            from django.conf import settings

            static_files_to_check = [
                'css/mobile-optimization.css',
                'js/performance-optimization.js',
                'js/sw.js',
                'js/products/design-tool-integration.js',
                'js/products/cart-integration.js',
                'css/products/product-detail.css'
            ]

            all_exist = True
            for static_dir in settings.STATICFILES_DIRS:
                for static_file in static_files_to_check:
                    file_path = os.path.join(static_dir, static_file)
                    if os.path.exists(file_path):
                        self.log_test(f"Static File: {static_file}", True, "File exists")
                    else:
                        self.log_test(f"Static File: {static_file}", False, "File not found")
                        all_exist = False
                break  # Only check first static directory

            return all_exist
        except Exception as e:
            self.log_test("Static Files", False, str(e))
            return False

    def test_views_import(self):
        """Test that views can be imported without errors"""
        try:
            # Test orders views
            from apps.orders import views as orders_views

            # Test design_tool views
            from apps.design_tool import views as design_views

            # Check for key view functions
            required_views = [
                'add_static_product_to_cart',
                'generate_quote_from_cart',
                'static_product_design_editor',
                'save_design_ajax'
            ]

            all_views_exist = True
            for view_name in required_views:
                if hasattr(orders_views, view_name) or hasattr(design_views, view_name):
                    self.log_test(f"View: {view_name}", True, "Function exists")
                else:
                    self.log_test(f"View: {view_name}", False, "Function not found")
                    all_views_exist = False

            return all_views_exist
        except Exception as e:
            self.log_test("Views Import", False, str(e))
            return False

    def run_all_tests(self):
        """Run all functionality tests"""
        print("Starting Phase 3 Functionality Tests...\n")

        # Setup test data
        if not self.setup_test_data():
            print("❌ Failed to setup test data. Aborting tests.")
            return False

        # Run tests
        tests = [
            self.test_static_product_creation,
            self.test_cart_functionality,
            self.test_design_tool_integration,
            self.test_url_patterns,
            self.test_template_files,
            self.test_static_files,
            self.test_views_import
        ]

        print("\n📋 Running Tests...\n")

        passed = 0
        total = 0

        for test in tests:
            if test():
                passed += 1
            total += 1

        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"   Total Tests: {total}")
        print(f"   Passed: {passed}")
        print(f"   Failed: {total - passed}")
        print(f"   Success Rate: {(passed/total)*100:.1f}%")

        if passed == total:
            print("🎉 All tests passed! Phase 3 implementation is ready.")
        else:
            print("⚠️  Some tests failed. Please review the issues above.")

        return passed == total

def main():
    """Main function to run tests"""
    tester = Phase3FunctionalityTest()
    return tester.run_all_tests()

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)