from django.core.management.base import BaseCommand
from apps.core.models import HomepageSlider


class Command(BaseCommand):
    help = 'Create initial homepage sliders for book printing, paperbox printing, and stationery'

    def handle(self, *args, **options):
        # Clear existing sliders
        HomepageSlider.objects.all().delete()

        # Create Book Printing Slider (Order 1)
        book_slider = HomepageSlider.objects.create(
            title="Premium Book Printing Services",
            subtitle="Professional Publishing Solutions",
            description="Transform your manuscripts into beautifully printed books with our professional binding, high-quality paper, and expert finishing services.",
            order=1,
            primary_cta_text="Start Your Book",
            primary_cta_url="/services/categories/",
            secondary_cta_text="View Samples",
            secondary_cta_url="/portfolio/",
            background_gradient_from="from-blue-50",
            background_gradient_via="via-indigo-50",
            background_gradient_to="to-purple-50",
            is_active=True
        )

        # Create Paperbox Printing Slider (Order 2)
        paperbox_slider = HomepageSlider.objects.create(
            title="Custom Paperbox Solutions",
            subtitle="Packaging That Makes an Impact",
            description="Design and print custom paperboxes for your products with premium materials, vibrant colors, and professional finishing options.",
            order=2,
            primary_cta_text="Design Boxes",
            primary_cta_url="/services/categories/",
            secondary_cta_text="Get Quote",
            secondary_cta_url="/contact/",
            background_gradient_from="from-green-50",
            background_gradient_via="via-emerald-50",
            background_gradient_to="to-teal-50",
            is_active=True
        )

        # Create Stationery Slider (Order 3)
        stationery_slider = HomepageSlider.objects.create(
            title="Professional Stationery Printing",
            subtitle="Business Identity Solutions",
            description="Create professional business cards, letterheads, envelopes, and complete stationery sets that reflect your brand's excellence.",
            order=3,
            primary_cta_text="Browse Stationery",
            primary_cta_url="/services/categories/",
            secondary_cta_text="Design Now",
            secondary_cta_url="/design-tool/",
            background_gradient_from="from-orange-50",
            background_gradient_via="via-amber-50",
            background_gradient_to="to-yellow-50",
            is_active=True
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {HomepageSlider.objects.count()} homepage sliders:\n'
                f'1. {book_slider.title}\n'
                f'2. {paperbox_slider.title}\n'
                f'3. {stationery_slider.title}'
            )
        )