import csv
import json
import os
from django.core.management.base import BaseCommand
from apps.services.models import StaticProduct, ProductFormField

class Command(BaseCommand):
    help = 'Export all product fields to a CSV file'

    def handle(self, *args, **options):
        output_file = 'product_fields_export.csv'
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'Product ID',
                'Product Name',
                'Category',
                'Field ID',
                'Field Label',
                'Field Name',
                'Field Type',
                'Is Required',
                'Field Order',
                'Price Affecting',
                'Options (JSON)'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            products = StaticProduct.objects.all().order_by('category__name', 'name')
            
            for product in products:
                form_fields = ProductFormField.objects.filter(static_product=product).order_by('order')
                
                if not form_fields.exists():
                    # Write row for product with no fields
                    writer.writerow({
                        'Product ID': product.id,
                        'Product Name': product.name,
                        'Category': product.category.name if product.category else 'Uncategorized',
                        'Field ID': '',
                        'Field Label': 'NO FIELDS',
                        'Field Name': '',
                        'Field Type': '',
                        'Is Required': '',
                        'Field Order': '',
                        'Price Affecting': '',
                        'Options (JSON)': ''
                    })
                
                for field in form_fields:
                    writer.writerow({
                        'Product ID': product.id,
                        'Product Name': product.name,
                        'Category': product.category.name if product.category else 'Uncategorized',
                        'Field ID': field.id,
                        'Field Label': field.field_label,
                        'Field Name': field.field_name,
                        'Field Type': field.field_type,
                        'Is Required': field.is_required,
                        'Field Order': field.order,
                        'Price Affecting': field.is_price_affecting,
                        'Options (JSON)': field.options
                    })

        self.stdout.write(self.style.SUCCESS(f'Successfully exported product fields to {output_file}'))
