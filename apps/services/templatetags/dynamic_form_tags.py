from django import template
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from apps.services.models import ProductFormField
import json

register = template.Library()

def create_default_fields_for_product(product):
    """Create default fields HTML for products without dynamic fields"""
    # Basic fallback form for products without dynamic fields configured
    product_name = product.name.lower()

    # Determine if this is a book-related product
    if any(keyword in product_name for keyword in ['book', 'annual', 'children', 'comic', 'coloring']):
        return render_to_string('services/partials/fallback_book_form.html', {'product': product})
    else:
        return render_to_string('services/partials/fallback_generic_form.html', {'product': product})

@register.simple_tag
def render_product_form_fields(product, form_data=None):
    """Render all form fields for a StaticProduct grouped by sections"""
    # Only handle StaticProduct models now
    if hasattr(product, 'form_fields'):
        fields = product.form_fields.filter(is_active=True).order_by('section_order', 'field_section', 'order')
    else:
        return ""

    if not fields.exists():
        # If no dynamic fields exist, try to create default fields based on product name/category
        default_fields_html = create_default_fields_for_product(product)
        return default_fields_html

    form_data = form_data or {}

    # Group fields by section
    sections = {}
    for field in fields:
        section_key = field.field_section
        if section_key not in sections:
            sections[section_key] = {
                'name': field.get_field_section_display(),
                'order': field.section_order,
                'fields': []
            }

        # Check if field should be shown based on conditional logic
        if field.should_show(form_data):
            sections[section_key]['fields'].append(field)

    # Sort sections by order
    sorted_sections = sorted(sections.items(), key=lambda x: x[1]['order'])

    return render_to_string('services/partials/dynamic_form_sections.html', {
        'sections': sorted_sections,
        'form_data': form_data,
        'product': product
    })

@register.simple_tag
def render_form_field(field, form_data=None, field_id_prefix=""):
    """Render a single form field based on its type"""
    form_data = form_data or {}
    current_value = form_data.get(field.field_name, field.default_value)

    context = {
        'field': field,
        'current_value': current_value,
        'form_data': form_data,
        'field_id': f"{field_id_prefix}{field.field_name}",
        'field_options': field.get_options(),
    }

    template_name = f'services/partials/field_types/{field.field_type}.html'

    try:
        return render_to_string(template_name, context)
    except:
        # Fallback to generic field template
        return render_to_string('services/partials/field_types/generic.html', context)

@register.filter
def get_field_css_classes(field):
    """Get CSS classes for a field based on its configuration"""
    classes = ['form-field']

    if field.css_classes:
        classes.append(field.css_classes)

    if field.grid_columns > 1:
        classes.append(f'col-span-{field.grid_columns}')

    if field.is_required:
        classes.append('required')

    return ' '.join(classes)

@register.filter
def field_has_conditional_logic(field):
    """Check if field has conditional display logic"""
    return bool(field.show_condition)

@register.filter
def get_field_triggers(field):
    """Get the fields that this field can trigger"""
    return field.get_triggered_fields()

@register.simple_tag
def get_field_price_modifier(field, selected_value, quantity=1):
    """Calculate price modifier for a field value"""
    if not field.is_price_affecting:
        return 0

    return field.calculate_price_modifier(selected_value, quantity)

@register.filter
def jsonify(value):
    """Convert Python object to JSON string for JavaScript"""
    return mark_safe(json.dumps(value))

@register.simple_tag
def render_field_section_header(section_name, section_display_name, section_order):
    """Render section header with proper styling"""
    return render_to_string('services/partials/field_section_header.html', {
        'section_name': section_name,
        'section_display_name': section_display_name,
        'section_order': section_order
    })

@register.filter
def get_conditional_fields_data(product):
    """Get data for conditional field logic in JavaScript"""
    if hasattr(product, 'form_fields'):
        fields = product.form_fields.filter(is_active=True)
    else:
        return {}

    conditional_data = {}

    for field in fields:
        if field.show_condition:
            conditional_data[field.field_name] = {
                'condition': field.get_show_condition(),
                'triggers': field.get_triggered_fields()
            }

    return conditional_data

@register.simple_tag
def get_field_validation_rules(field):
    """Get validation rules for a field"""
    rules = {}

    if field.is_required:
        rules['required'] = True

    if field.min_value is not None:
        rules['min'] = float(field.min_value)

    if field.max_value is not None:
        rules['max'] = float(field.max_value)

    if field.field_type == 'number':
        rules['type'] = 'number'
    elif field.field_type == 'file':
        rules['type'] = 'file'
        # You can add file type restrictions here

    return rules