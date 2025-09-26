from django import template

register = template.Library()

@register.filter
def count_with_field(queryset, field_value):
    """
    Usage: {{ queryset|count_with_field:"field=value" }}
    Example: {{ category.products.all|count_with_field:"has_design_tool=True" }}
    """
    if not queryset:
        return 0
    try:
        field, value = field_value.split('=')
        value = value.strip()
        # Convert value to correct type
        if value.lower() == 'true':
            value = True
        elif value.lower() == 'false':
            value = False
        return queryset.filter(**{field.strip(): value}).count()
    except Exception:
        return 0
