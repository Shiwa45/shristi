# apps/core/management/commands/update_slider_images.py
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from apps.core.models import HomepageSlider
import requests
from io import BytesIO


class Command(BaseCommand):
    help = 'Update slider images with placeholder images'

    def handle(self, *args, **options):
        # Sample placeholder images (you can replace these with actual images)
        image_urls = {
            'Professional Book Printing Services': 'https://via.placeholder.com/600x400/4F46E5/FFFFFF?text=Book+Printing',
            'Custom Paper Box Solutions': 'https://via.placeholder.com/600x400/059669/FFFFFF?text=Paper+Boxes',
            'Complete Stationery Solutions': 'https://via.placeholder.com/600x400/D97706/FFFFFF?text=Stationery'
        }
        
        for slider in HomepageSlider.objects.all():
            if slider.title in image_urls and not slider.image:
                try:
                    # Download placeholder image
                    response = requests.get(image_urls[slider.title])
                    if response.status_code == 200:
                        # Create filename
                        filename = f"slider_{slider.id}_{slider.title.lower().replace(' ', '_')}.png"
                        
                        # Save image
                        slider.image.save(
                            filename,
                            ContentFile(response.content),
                            save=True
                        )
                        
                        self.stdout.write(
                            self.style.SUCCESS(f'Updated image for: {slider.title}')
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'Failed to download image for: {slider.title}')
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error updating {slider.title}: {str(e)}')
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Skipped {slider.title} (already has image or not found)')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Slider image update completed')
        )