"""
Data migration: ensure every ProductFormField with field_name='printing_side'
has a 'Front & Back Both' option (value='both').

If both 'Front Side'/'Back Side' style options exist but no 'both' option,
it means the field was set up with individual side options only.  We add
the third combined option so the design-studio two-canvas feature works.
"""
import json
from django.db import migrations


def add_both_option(apps, schema_editor):
    ProductFormField = apps.get_model('services', 'ProductFormField')

    for field in ProductFormField.objects.filter(field_name='printing_side'):
        # Parse current options (stored as JSON text or list)
        raw = field.options or '[]'
        if isinstance(raw, list):
            opts = raw
        else:
            try:
                opts = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                opts = []

        # Skip if a 'both'-type option already exists
        existing_values = {str(o.get('value', '')).lower() for o in opts}
        if existing_values & {'both', 'front_back', 'front and back', 'front_back_both'}:
            continue

        # Append the combined option
        opts.append({
            'value': 'both',
            'label': 'Front & Back Both',
            'price_modifier': 0,
            'description': 'Print on both front and back sides',
        })

        if isinstance(field.options, list):
            field.options = opts
        else:
            field.options = json.dumps(opts)
        field.save()


def remove_both_option(apps, schema_editor):
    ProductFormField = apps.get_model('services', 'ProductFormField')

    for field in ProductFormField.objects.filter(field_name='printing_side'):
        raw = field.options or '[]'
        if isinstance(raw, list):
            opts = raw
        else:
            try:
                opts = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                continue

        filtered = [o for o in opts if str(o.get('value', '')).lower() != 'both']
        if len(filtered) == len(opts):
            continue  # nothing to remove

        if isinstance(field.options, list):
            field.options = filtered
        else:
            field.options = json.dumps(filtered)
        field.save()


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0013_alter_productformfield_field_type'),
    ]

    operations = [
        migrations.RunPython(add_both_option, remove_both_option),
    ]
