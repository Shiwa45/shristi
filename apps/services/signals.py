from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import ServiceCategory, StaticProduct

@receiver([post_save, post_delete], sender=ServiceCategory)
@receiver([post_save, post_delete], sender=StaticProduct)
def invalidate_services_menu_cache(sender, instance, **kwargs):
    """
    Invalidate the services menu cache whenever a category or product is changed.
    """
    cache_key = 'services_menu_context_data'
    cache.delete(cache_key)
    print(f"Cache invalidated for key: {cache_key}")
