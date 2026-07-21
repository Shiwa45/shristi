from decimal import Decimal

from django.test import TestCase

from apps.services.models import BookPrintingPricing, ServiceCategory, StaticProduct
from apps.services.pricing import calculate_book_pricing


class BookPricingMatrixTests(TestCase):
    def setUp(self):
        category = ServiceCategory.objects.create(name='Book Printing', slug='book-printing')
        self.product = StaticProduct.objects.create(
            name='Matrix Test Book',
            slug='matrix-test-book',
            category=category,
            description='Test product',
            short_description='Test product',
            base_price=Decimal('1.00'),
        )
        pricing = BookPrintingPricing.load()
        pricing.page_price_matrix = {
            'bw_premium': {'a4': {'75gsm': 1.40}},
            'bw_standard': {'a5': {'100gsm': 0.82}},
            'color_premium': {'a4': {'75gsm': 2.80}},
            'color_standard': {},
        }
        pricing.binding_saddle_stitch = Decimal('0')
        pricing.cover_matte = Decimal('0')
        pricing.bulk_qty_1 = 200
        pricing.bulk_qty_2 = 250
        pricing.bulk_qty_3 = 300
        pricing.save()

    def test_standard_book_uses_exact_dependent_matrix_rate(self):
        result = calculate_book_pricing(self.product, {
            'interior_color': 'bw_standard',
            'book_size': 'a5',
            'paper_type': '100gsm',
            'page_count': '10',
            'binding_type': 'saddle_stitch',
            'cover_finish': 'matte',
        }, 25)

        # 10 pages × ₹0.82; no legacy size or paper add-ons are permitted.
        self.assertEqual(result['cost_per_book'], Decimal('8.20'))
        self.assertEqual(result['gross_subtotal'], Decimal('205.00'))

    def test_combined_colour_uses_the_two_premium_matrix_rates(self):
        result = calculate_book_pricing(self.product, {
            'interior_color': 'combine_color',
            'book_size': 'a4',
            'paper_type': '75gsm',
            'bw_page_count': '3',
            'color_page_count': '2',
            'binding_type': 'saddle_stitch',
            'cover_finish': 'matte',
        }, 1)

        # 3 B&W premium pages × ₹1.40 + 2 colour premium pages × ₹2.80.
        self.assertEqual(result['cost_per_book'], Decimal('9.80'))
        self.assertEqual(result['gross_subtotal'], Decimal('9.80'))
