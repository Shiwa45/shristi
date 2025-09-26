from django.core.cache import cache
from apps.services.models import ServiceCategory

def services_menu_context(request):
    """
    Context processor to provide services menu data globally across all templates.
    This makes the menu data available in every template without explicitly passing it.
    """
    cache_key = 'services_menu_context_data'
    menu_data = cache.get(cache_key)
    
    if menu_data is None:
        # Fetch active categories with their products
        categories = ServiceCategory.objects.filter(
            is_active=True
        ).prefetch_related(
            'products'
        ).order_by('order', 'name')
        
        menu_structure = []
        for category in categories:
            # Get active products for this category
            products = category.products.filter(is_active=True).order_by('order', 'name')
            
            if products.exists():  # Only include categories that have products
                category_data = {
                    'name': category.name,
                    'slug': category.slug,
                    'is_featured': category.is_featured,
                    'icon': category.icon,
                    'url': category.get_absolute_url(),
                    'products': [
                        {
                            'name': product.name,
                            'slug': product.slug,
                            'is_featured': product.is_featured,
                            'url': product.get_absolute_url(),
                            'short_description': product.short_description,
                        }
                        for product in products
                    ]
                }
                menu_structure.append(category_data)
        
        menu_data = {
            'services_menu': menu_structure,
            'services_menu_count': len(menu_structure)
        }
        
        # Cache for 1 hour
        cache.set(cache_key, menu_data, 3600)
    
    return menu_data