import os
import zipfile
import xml.etree.ElementTree as ET
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.services.models import StaticProduct, ProductFormField, ServiceCategory
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Import product fields from Excel files in WEBSITE 2025 directory'

    def handle(self, *args, **options):
        base_dir = os.path.join(settings.BASE_DIR, 'WEBSITE 2025')
        self.stdout.write(f"Scanning directory: {base_dir}")

        if not os.path.exists(base_dir):
            self.stdout.write(self.style.ERROR(f"Directory not found: {base_dir}"))
            return

        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.endswith('.xlsx') and not file.startswith('~$'):
                    file_path = os.path.join(root, file)
                    self.process_excel_file(file_path, root)

    def process_excel_file(self, file_path, root_dir):
        filename = os.path.basename(file_path)
        product_name = os.path.splitext(filename)[0]
        category_name = os.path.basename(root_dir)
        
        self.stdout.write(f"Processing: {product_name} (Category: {category_name})")

        try:
            data = self.read_excel_data(file_path)
            if not data:
                self.stdout.write(self.style.WARNING(f"No data found in {filename}"))
                return

            self.update_product_fields(product_name, category_name, data)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error processing {filename}: {str(e)}"))

    def read_excel_data(self, file_path):
        """
        Reads Excel file using standard zipfile and xml libraries.
        Returns a list of rows, where each row is a list of cell values.
        """
        rows = []
        with zipfile.ZipFile(file_path, 'r') as z:
            # 1. Parse Shared Strings
            shared_strings = []
            if 'xl/sharedStrings.xml' in z.namelist():
                with z.open('xl/sharedStrings.xml') as f:
                    tree = ET.parse(f)
                    root = tree.getroot()
                    # Namespace usually: http://schemas.openxmlformats.org/spreadsheetml/2006/main
                    ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                    for si in root.findall('main:si', ns):
                        t = si.find('main:t', ns)
                        if t is not None and t.text:
                            shared_strings.append(t.text)
                        else:
                            # Handle rich text or empty
                            shared_strings.append("")

            # 2. Parse Sheet 1
            if 'xl/worksheets/sheet1.xml' in z.namelist():
                with z.open('xl/worksheets/sheet1.xml') as f:
                    tree = ET.parse(f)
                    root = tree.getroot()
                    ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                    
                    sheet_data = root.find('main:sheetData', ns)
                    if sheet_data is not None:
                        for row in sheet_data.findall('main:row', ns):
                            row_values = []
                            for cell in row.findall('main:c', ns):
                                cell_type = cell.get('t')
                                v = cell.find('main:v', ns)
                                if v is not None:
                                    value = v.text
                                    if cell_type == 's':  # Shared String
                                        try:
                                            idx = int(value)
                                            if 0 <= idx < len(shared_strings):
                                                row_values.append(shared_strings[idx])
                                            else:
                                                row_values.append(value)
                                        except ValueError:
                                            row_values.append(value)
                                    else:
                                        row_values.append(value)
                                else:
                                    # Check for inline string
                                    is_tag = cell.find('main:is', ns)
                                    if is_tag is not None:
                                        t_tag = is_tag.find('main:t', ns)
                                        if t_tag is not None:
                                            row_values.append(t_tag.text)
                            
                            if row_values:
                                rows.append(row_values)
        return rows

    def update_product_fields(self, product_name, category_name, data):
        # 1. Find or Create Category
        # Map folder names to category slugs if needed, or just use slugify
        category_slug = slugify(category_name)
        
        # Try to match with existing categories or default to 'marketing-material' or 'stationery'
        # based on known categories in models.py
        known_categories = ['book-printing', 'paper-boxes', 'marketing-material', 'stationery']
        
        target_category_slug = 'marketing-material' # Default
        if 'stationery' in category_slug or 'business-card' in category_slug or 'letter-head' in category_slug:
            target_category_slug = 'stationery'
        elif 'box' in category_slug:
            target_category_slug = 'paper-boxes'
        elif 'book' in category_slug:
            target_category_slug = 'book-printing'
            
        category, _ = ServiceCategory.objects.get_or_create(
            slug=target_category_slug,
            defaults={'name': target_category_slug.replace('-', ' ').title()}
        )

        # 2. Find or Create Product
        product, created = StaticProduct.objects.get_or_create(
            name=product_name,
            defaults={
                'slug': slugify(product_name),
                'category': category,
                'base_price': 100.00, # Default
                'description': f"High quality {product_name}",
                'short_description': f"Custom {product_name} printing",
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created new product: {product_name}"))
        else:
            self.stdout.write(f"Updating existing product: {product_name}")

        # 3. Process Fields from Data
        # Assumption: Data is key-value pairs or list of options.
        # Let's look at the example data structure from previous step:
        # ['Printing Side', 'Front Side', 'Qty. ', 'Both Side', 'Non Tear Business Cards', 'url...', 'Paper Quality', 'Non Tearable (250 micron)']
        
        # It seems unstructured. We need to infer fields.
        # Heuristic:
        # - "Qty." is a special field.
        # - URL is metadata.
        # - "Non Tear Business Cards" is likely the title (already have it).
        # - "Printing Side" -> Options: "Front Side", "Both Side"
        # - "Paper Quality" -> Options: "Non Tearable..."
        
        # Let's try to group them.
        # We'll iterate and look for "headers" (likely short strings) followed by options.
        
        # Better approach for this specific unstructured data:
        # Collect all strings.
        # Identify known headers: "Printing Side", "Paper Quality", "Lamination", "Corner", "Qty"
        
        all_values = [item for sublist in data for item in sublist if item and str(item).strip()]
        
        # Clear existing fields to avoid duplicates on re-run
        product.form_fields.all().delete()
        
        current_field = None
        current_options = []
        
        # Define potential field headers to recognize start of a new field
        known_headers = [
            'Printing Side', 'Paper Quality', 'Lamination', 'Corner', 'Size', 'Paper Type', 
            'Fold', 'Binding', 'Cover', 'Interior', 'Quantity', 'Qty', 'Qty.'
        ]
        
        # Also, if we see a URL, we can save it to product description or a specific field if we want
        
        # Simple parsing logic:
        # If value in known_headers -> Start new field.
        # Else -> Add to options of current field.
        
        fields_found = {} # {field_name: [options]}
        
        for value in all_values:
            clean_value = str(value).strip()
            
            # Skip URL and Title if they appear in the list
            if clean_value.startswith('http'):
                continue
            if clean_value.lower() == product_name.lower():
                continue
                
            # Check if it's a header
            is_header = False
            for header in known_headers:
                if header.lower() in clean_value.lower():
                    # It's a header
                    current_field = clean_value.replace('.', '').strip() # Remove trailing dots
                    if current_field not in fields_found:
                        fields_found[current_field] = []
                    is_header = True
                    break
            
            if not is_header and current_field:
                # It's an option for the current field
                fields_found[current_field].append(clean_value)

        # Create Fields
        order = 0
        for field_label, options in fields_found.items():
            order += 1
            field_name = slugify(field_label).replace('-', '_')
            
            field_type = 'select'
            if len(options) == 0:
                field_type = 'text'
            elif len(options) < 4: # Few options -> Radio or Visual Card
                field_type = 'radio' # We can style this as cards in template
            
            # Special case for Quantity
            if 'qty' in field_name or 'quantity' in field_name:
                # We usually handle quantity separately in the cart, but if it's a specific dropdown:
                field_type = 'select'
            
            # Create the field
            form_field = ProductFormField.objects.create(
                static_product=product,
                field_name=field_name,
                field_label=field_label,
                field_type=field_type,
                order=order,
                is_required=True,
                is_active=True,
                section_order=1 # Default section
            )
            
            # Add options
            formatted_options = []
            for opt in options:
                formatted_options.append({
                    "value": slugify(opt),
                    "label": opt,
                    "price_modifier": 0 # Default
                })
            
            import json
            form_field.options = json.dumps(formatted_options)
            form_field.save()
            
            self.stdout.write(f"  Added field: {field_label} ({len(options)} options)")

