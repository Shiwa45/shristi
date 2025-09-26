# apps/core/management/commands/create_sample_sliders.py
from django.core.management.base import BaseCommand
from apps.core.models import HomepageSlider


class Command(BaseCommand):
    help = 'Create sample homepage sliders'

    def handle(self, *args, **options):
        # Clear existing sliders
        HomepageSlider.objects.all().delete()
        
        # Create sample sliders
        sliders_data = [
            {
                'title': 'Professional Book Printing Services',
                'subtitle': 'Quality Publishing Solutions',
                'description': 'Transform your manuscript into a beautifully printed book with our professional printing services. From novels to textbooks, we deliver exceptional quality.',
                'primary_cta_text': 'Start Printing',
                'primary_cta_url': '/services/books/',
                'secondary_cta_text': 'View Samples',
                'secondary_cta_url': '/portfolio/',
                'background_gradient_from': 'from-blue-50',
                'background_gradient_via': 'via-indigo-50',
                'background_gradient_to': 'to-purple-50',
                'order': 1,
            },
            {
                'title': 'Custom Paper Box Solutions',
                'subtitle': 'Premium Packaging Design',
                'description': 'Create stunning custom paper boxes for your products. Perfect for retail, gifts, and corporate branding with premium materials and finishes.',
                'primary_cta_text': 'Design Box',
                'primary_cta_url': '/services/packaging/',
                'secondary_cta_text': 'Get Quote',
                'secondary_cta_url': '/contact/',
                'background_gradient_from': 'from-green-50',
                'background_gradient_via': 'via-emerald-50',
                'background_gradient_to': 'to-teal-50',
                'order': 2,
            },
            {
                'title': 'Complete Stationery Solutions',
                'subtitle': 'Business & Personal Stationery',
                'description': 'Professional letterheads, business cards, envelopes, and more. Create a cohesive brand identity with our comprehensive stationery services.',
                'primary_cta_text': 'Browse Stationery',
                'primary_cta_url': '/services/stationery/',
                'secondary_cta_text': 'Custom Design',
                'secondary_cta_url': '/design-tool/',
                'background_gradient_from': 'from-orange-50',
                'background_gradient_via': 'via-amber-50',
                'background_gradient_to': 'to-yellow-50',
                'order': 3,
            }
        ]
        
        created_count = 0
        for slider_data in sliders_data:
            slider, created = HomepageSlider.objects.get_or_create(
                title=slider_data['title'],
                defaults=slider_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created slider: {slider.title}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Slider already exists: {slider.title}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} sliders')
        )