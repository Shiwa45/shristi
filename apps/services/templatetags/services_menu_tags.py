from django import template
from django.core.cache import cache
from apps.services.models import ServiceCategory, Product

register = template.Library()

@register.inclusion_tag('services/partials/services_dropdown.html')
def services_dropdown_menu():
    """
    Template tag to render the services dropdown menu with categories and products.
    Uses caching to optimize performance.
    """
    cache_key = 'services_dropdown_menu_data'
    menu_data = cache.get(cache_key)
    
    if menu_data is None:
        # Fetch active categories with their products in optimized query
        categories = ServiceCategory.objects.filter(
            is_active=True
        ).prefetch_related(
            'products'
        ).order_by('order', 'name')
        
        menu_data = []
        for category in categories:
            # Get active products for this category
            products = category.products.filter(is_active=True).order_by('order', 'name')
            
            if products.exists():  # Only include categories that have products
                category_data = {
                    'category': category,
                    'products': list(products)
                }
                menu_data.append(category_data)
        
        # Cache for 1 hour
        cache.set(cache_key, menu_data, 3600)
    
    return {'menu_categories': menu_data}

@register.simple_tag
def get_services_menu_data():
    """
    Simple tag to get services menu data for use in templates.
    """
    cache_key = 'services_dropdown_menu_data'
    menu_data = cache.get(cache_key)
    
    if menu_data is None:
        categories = ServiceCategory.objects.filter(
            is_active=True
        ).prefetch_related(
            'products'
        ).order_by('order', 'name')
        
        menu_data = []
        for category in categories:
            products = category.products.filter(is_active=True).order_by('order', 'name')
            
            if products.exists():
                category_data = {
                    'category': category,
                    'products': list(products)
                }
                menu_data.append(category_data)
        
        cache.set(cache_key, menu_data, 3600)
    
    return menu_data

@register.simple_tag
def clear_services_menu_cache():
    """
    Tag to clear the services menu cache when categories or products are updated.
    """
    cache.delete('services_dropdown_menu_data')
    return ''