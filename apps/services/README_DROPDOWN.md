# Services Navigation Dropdown

This document describes the implementation of the dynamic services navigation dropdown menu.

## Overview

The services dropdown provides a user-friendly way to navigate through service categories and products. It features:

- Dynamic content from database
- Responsive design for mobile and desktop
- Accessibility compliance (ARIA, keyboard navigation)
- Performance optimization with caching
- Progressive enhancement (works without JavaScript)

## Files Created/Modified

### Backend Files
- `apps/services/templatetags/services_menu_tags.py` - Template tags for menu data
- `apps/services/context_processors.py` - Global context processor
- `apps/services/signals.py` - Cache invalidation signals
- `apps/services/apps.py` - Signal registration
- `apps/services/management/commands/warm_services_cache.py` - Cache warming command

### Frontend Files
- `templates/services/partials/services_dropdown.html` - Dropdown template
- `static/css/components/services_dropdown.css` - Dropdown styles
- `static/js/components/services_dropdown.js` - JavaScript enhancements
- `templates/base.html` - Integration with main navigation

### Test Files
- `apps/services/test_dropdown.py` - Comprehensive test suite

## Usage

### Template Tag Usage
```django
{% load services_menu_tags %}
{% services_dropdown_menu %}
```

### Context Processor
The menu data is automatically available in all templates as `services_menu`.

### Cache Management
```bash
# Warm up cache
python manage.py warm_services_cache

# Clear cache manually
python manage.py shell
>>> from django.core.cache import cache
>>> cache.delete('services_dropdown_menu_data')
>>> cache.delete('services_menu_context_data')
```

## Configuration

### Settings Required
Add to `TEMPLATES` context processors:
```python
'apps.services.context_processors.services_menu_context',
```

### Cache Configuration
The implementation uses Django's default cache. For production, configure Redis:
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

## Performance Features

### Caching Strategy
- Menu data cached for 1 hour
- Automatic cache invalidation on model changes
- Optimized database queries with `prefetch_related`

### Database Optimization
- Uses `select_related` and `prefetch_related` for efficient queries
- Filters inactive categories and products at database level
- Orders by `order` field then `name` for consistent sorting

## Accessibility Features

### ARIA Support
- `role="menu"` and `role="menuitem"` attributes
- `aria-expanded` states for dropdown visibility
- `aria-haspopup` indicators for submenu presence
- Proper `aria-label` descriptions

### Keyboard Navigation
- Tab navigation through menu items
- Enter/Space key activation
- Escape key to close dropdowns
- Arrow key navigation within submenus

### Screen Reader Support
- Semantic HTML structure
- Descriptive alt text and labels
- Focus management for keyboard users

## Mobile Features

### Touch Interactions
- Tap to open/close on mobile devices
- Touch-friendly sizing and spacing
- Swipe gestures for category navigation
- Prevent overscroll in mobile menu

### Responsive Design
- Mobile-first CSS approach
- Breakpoints at 768px and 480px
- Collapsible category sections on mobile
- Full-screen mobile menu overlay

## Browser Support

### Tested Browsers
- Chrome (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Edge (latest 2 versions)
- Mobile browsers (iOS Safari, Chrome Mobile)

### Progressive Enhancement
- Works without JavaScript (CSS-only fallback)
- Graceful degradation for older browsers
- Reduced motion support for accessibility

## Troubleshooting

### Common Issues

1. **Dropdown not appearing**
   - Check CSS file is loaded
   - Verify JavaScript file is included
   - Ensure template tag is loaded

2. **Cache not updating**
   - Check signal registration in apps.py
   - Verify cache backend configuration
   - Run cache warming command

3. **Mobile menu not working**
   - Check viewport meta tag
   - Verify touch event handlers
   - Test on actual mobile device

### Debug Commands
```bash
# Test template tag
python manage.py shell
>>> from apps.services.templatetags.services_menu_tags import services_dropdown_menu
>>> result = services_dropdown_menu()
>>> print(len(result['menu_categories']))

# Check cache status
>>> from django.core.cache import cache
>>> print(cache.get('services_dropdown_menu_data'))

# Run tests
python manage.py test apps.services.test_dropdown
```

## Maintenance

### Regular Tasks
- Monitor cache hit rates
- Update browser compatibility tests
- Review accessibility compliance
- Performance monitoring

### When Adding New Services
The dropdown automatically updates when:
- New ServiceCategory is created and marked active
- New Product is added to active category
- Cache is automatically invalidated via signals

### Performance Monitoring
Monitor these metrics:
- Database query count for menu loading
- Cache hit/miss ratios
- Page load times with dropdown
- Mobile interaction responsiveness

## Security Considerations

### Input Validation
- All user inputs are sanitized
- Slug parameters validated to prevent injection
- CSRF protection on form submissions

### Access Control
- Only active services displayed
- Proper permission checks for admin features
- Rate limiting on API endpoints

## Future Enhancements

### Potential Improvements
- A/B testing for menu variations
- Analytics tracking for menu usage
- Search functionality within dropdown
- Category icons and images
- Mega menu layout for large catalogs

### API Extensions
- REST API for menu data
- GraphQL support
- Real-time updates via WebSocket
- Personalized menu based on user preferences