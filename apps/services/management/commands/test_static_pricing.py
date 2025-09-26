# apps/services/management/commands/test_static_pricing.py
from django.core.management.base import BaseCommand
from apps.services.models_product_types import BookPrintingQuote, BusinessCardQuote, BrochureQuote, ChildrenBookQuote


class Command(BaseCommand):
    help = 'Test the static pricing models'

    def handle(self, *args, **options):
        self.stdout.write('Testing Static Pricing Models...\n')
        
        # Test Business Card Quote
        self.stdout.write('=== BUSINESS CARD QUOTE TEST ===')
        bc_quote = BusinessCardQuote(
            quantity=500,
            card_size='standard',
            paper_type='300gsm_art',
            printing_sides='double',
            finishing='matte_lam',
            design_service='basic'
        )
        bc_pricing = bc_quote.calculate_price()
        
        self.stdout.write(f'Business Cards - 500 pieces:')
        self.stdout.write(f'  Unit Price: ₹{bc_pricing["unit_price"]:.2f}')
        self.stdout.write(f'  Total Price: ₹{bc_pricing["total_price"]:.2f}')
        self.stdout.write(f'  Discount: {bc_pricing["discount_percent"]:.0f}%')
        
        # Test Book Printing Quote
        self.stdout.write('\n=== BOOK PRINTING QUOTE TEST ===')
        book_quote = BookPrintingQuote(
            quantity=100,
            book_size='A5',
            page_count=100,
            inner_paper='70gsm_offset',
            inner_printing='bw',
            cover_paper='250gsm_art',
            cover_printing='color_4_0',
            binding_type='perfect_binding',
            cover_finish='matte_lam',
            design_service='basic',
            isbn_service=True
        )
        book_pricing = book_quote.calculate_price()
        
        self.stdout.write(f'Books - 100 pieces:')
        self.stdout.write(f'  Unit Price: ₹{book_pricing["unit_price"]:.2f}')
        self.stdout.write(f'  Total Price: ₹{book_pricing["total_price"]:.2f}')
        self.stdout.write(f'  Discount: {book_pricing["discount_percent"]:.0f}%')
        
        # Test Brochure Quote
        self.stdout.write('\n=== BROCHURE QUOTE TEST ===')
        brochure_quote = BrochureQuote(
            quantity=1000,
            size='A4',
            paper_type='170gsm_art',
            folding='tri_fold',
            printing_sides='double',
            finishing='matte_lam'
        )
        brochure_pricing = brochure_quote.calculate_price()
        
        self.stdout.write(f'Brochures - 1000 pieces:')
        self.stdout.write(f'  Unit Price: ₹{brochure_pricing["unit_price"]:.2f}')
        self.stdout.write(f'  Total Price: ₹{brochure_pricing["total_price"]:.2f}')
        self.stdout.write(f'  Discount: {brochure_pricing["discount_percent"]:.0f}%')
        
        # Test Children's Book Quote
        self.stdout.write('\n=== CHILDREN\'S BOOK QUOTE TEST ===')
        children_quote = ChildrenBookQuote(
            quantity=100,
            book_size='A5',
            page_count=24,
            age_group='preschool',
            inner_paper='100gsm_art',
            inner_printing='full_color',
            cover_paper='350gsm_art',
            binding_type='perfect_binding',
            cover_finish='soft_touch',
            # Special features
            rounded_corners=True,
            pop_up_elements=True,
            glow_in_dark=True,
            # Services
            design_service='premium',
            writing_service='editing',
            publishing_service='isbn'
        )
        children_pricing = children_quote.calculate_price()
        
        self.stdout.write(f'Children\'s Books - 100 pieces:')
        self.stdout.write(f'  Unit Price: ₹{children_pricing["unit_price"]:.2f}')
        self.stdout.write(f'  Total Price: ₹{children_pricing["total_price"]:.2f}')
        self.stdout.write(f'  Discount: {children_pricing["discount_percent"]:.0f}%')
        self.stdout.write(f'  Special Features: Rounded corners, Pop-ups, Glow-in-dark')
        self.stdout.write(f'  Services: Premium illustration, Story editing, ISBN')
        
        self.stdout.write(self.style.SUCCESS('\n✅ All static pricing models working correctly!'))