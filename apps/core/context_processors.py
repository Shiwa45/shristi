from .models import SiteSetting


def site_settings_context(request):
    """Provide site settings globally for header/footer."""
    site_settings = (
        SiteSetting.objects.filter(is_active=True)
        .prefetch_related('nav_links', 'footer_link_groups__links', 'social_links')
        .order_by('-updated_at')
        .first()
    )

    return {
        'site_settings': site_settings,
    }
