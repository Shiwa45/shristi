from django.core.management.base import BaseCommand
from django.core.cache import cache
from apps.services.templatetags.services_menu_tags import get_services_menu_data
from apps.services.context_processors import services_menu_context

class Command(BaseCommand):
    help = 'Warm up the services menu cache'

    def handle(self, *args, **options):
        self.stdout.write('Warming up services menu cache...')
        
        # Clear existing cache
        cache.delete('services_dropdown_menu_data')
        cache.delete('services_menu_context_data')
        
        # Warm up template tag cache
        menu_data = get_services_menu_data()
        self.stdout.write(f'Cached {len(menu_data)} service categories')
        
        # Warm up context processor cache
        class MockRequest:
            pass
        
        context_data = services_menu_context(MockRequest())
        self.stdout.write(f'Cached context data with {context_data["services_menu_count"]} categories')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully warmed up services menu cache')
        )