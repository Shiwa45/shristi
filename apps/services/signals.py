from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import ServiceCategory, Product

@receiver([post_save, post_delete], sender=ServiceCategory)
def clear_services_menu_cache_on_category_change(sender, **kwargs):
    """Clear services menu cache when categories are modified"""
    cache.delete('services_dropdown_menu_data')
    cache.delete('services_menu_context_data')

@receiver([post_save, post_delete], sender=Product)
def clear_services_menu_cache_on_product_change(sender, **kwargs):
    """Clear services menu cache when products are modified"""
    cache.delete('services_dropdown_menu_data')
    cache.delete('services_menu_context_data')