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
        # Fetch active categories with their static products
        categories = ServiceCategory.objects.filter(
            is_active=True
        ).prefetch_related(
            'static_products'
        ).order_by('order', 'name')

        menu_structure = []
        for category in categories:
            # Get active static products for this category
            products = category.static_products.filter(is_active=True).order_by('order', 'name')
            
            if products.exists():  # Only include categories that have products
                # Dictionary to track groups by name
                groups_map = {}
                # List to hold all top-level items (groups and standalone products)
                menu_items = []
                
                for product in products:
                    if product.group_name:
                        # It's part of a group
                        if product.group_name not in groups_map:
                            # Create new group entry
                            group_entry = {
                                'type': 'group',
                                'name': product.group_name,
                                'order': product.group_order,
                                'products': []
                            }
                            groups_map[product.group_name] = group_entry
                            menu_items.append(group_entry)
                        
                        # Add product to existing group
                        groups_map[product.group_name]['products'].append({
                            'name': product.name,
                            'slug': product.slug,
                            'is_featured': product.is_featured,
                            'url': product.get_absolute_url(),
                            'short_description': product.short_description,
                        })
                    else:
                        # It's a standalone product
                        menu_items.append({
                            'type': 'product',
                            'name': product.name,
                            'slug': product.slug,
                            'is_featured': product.is_featured,
                            'url': product.get_absolute_url(),
                            'short_description': product.short_description,
                            'order': product.group_order, # Use group_order for sorting
                        })
                
                # Sort menu_items by order
                menu_items.sort(key=lambda x: x.get('order', 0))
                
                category_data = {
                    'name': category.name,
                    'slug': category.slug,
                    'is_featured': category.is_featured,
                    'icon': category.icon,
                    'url': category.get_absolute_url(),
                    'menu_items': menu_items,
                }
                menu_structure.append(category_data)
        
        menu_data = {
            'services_menu': menu_structure,
            'services_menu_count': len(menu_structure)
        }
        
        # Cache for 1 hour
        cache.set(cache_key, menu_data, 3600)
    
    return menu_data