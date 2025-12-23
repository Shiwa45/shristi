from django.core.management.base import BaseCommand
from apps.services.models import StaticProduct, ProductFormField
import pandas as pd
import os
import json
from django.utils.text import slugify
from decimal import Decimal

class Command(BaseCommand):
    help = 'Import product fields from Excel files'

    def handle(self, *args, **options):
        self.stdout.write('Starting import...')
        
        base_dir = '/home/shiwansh/shristi'
        
        # Mapping of Excel files to Product Slugs
        file_mapping = {
            'Bill Book, Black & White Bill Book.xlsx': 'bill-books',
            'Bill Book, Colour Bill Book.xlsx': 'bill-books',
            'Standard Business Card.xlsx': 'business-cards',
            'Corporate Letter Head.xlsx': 'letterheads',
            # Add other mappings if files exist
        }

        for filename, slug in file_mapping.items():
            file_path = os.path.join(base_dir, filename)
            if not os.path.exists(file_path):
                self.stdout.write(self.style.WARNING(f'File not found: {filename}'))
                continue

            try:
                product = StaticProduct.objects.get(slug=slug)
                self.stdout.write(f'Processing {filename} for {product.name}...')
                
                if 'Bill Book' in filename:
                    self.process_bill_book(file_path, product)
                elif 'Business Card' in filename:
                    self.process_business_card(file_path, product)
                elif 'Letter Head' in filename:
                    self.process_letter_head(file_path, product)
                
                product.save()
                self.stdout.write(self.style.SUCCESS(f'Successfully updated {product.name}'))
                
            except StaticProduct.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Product with slug {slug} not found'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing {filename}: {str(e)}'))

    def create_or_update_field(self, product, field_name, field_label, options, section='product_specs', field_type='select'):
        if not options:
            return

        # Format options for ProductFormField
        formatted_options = []
        for opt in options:
            formatted_options.append({
                'value': slugify(opt['name']),
                'label': opt['name'],
                'price_modifier': float(opt['price_modifier']),
                'description': ''
            })

        # Create or update field
        field, created = ProductFormField.objects.update_or_create(
            static_product=product,
            field_name=field_name,
            defaults={
                'field_label': field_label,
                'field_type': field_type,
                'field_section': section,
                'options': json.dumps(formatted_options),
                'is_active': True,
                'is_required': True,
                'is_price_affecting': True,
                # 'price_modifier_type': 'fixed' # Not in ProductFormField
            }
        )
        action = "Created" if created else "Updated"
        self.stdout.write(f"{action} form field: {field_label} for {product.name}")

    def process_bill_book(self, file_path, product):
        df = pd.read_excel(file_path, header=None)
        
        # Extract Binding Types
        # Looking for "Binding Type" and options below it
        bindings = []
        papers = []
        
        # Convert to string for easier searching
        # We'll search for the cell containing "Binding Type"
        for r_idx, row in df.iterrows():
            for c_idx, cell in enumerate(row):
                cell_str = str(cell).strip()
                
                if 'Binding Type' in cell_str:
                    # Assume options are in the same column or next, in subsequent rows
                    # Based on inspection: "options:-Saddle Stitch,Spiral Binding..."
                    # It might be in a single cell or multiple rows.
                    # Let's check the cell content itself first
                    if 'options:-' in cell_str:
                        opts = cell_str.split('options:-')[1].split(',')
                        for opt in opts:
                            bindings.append({'name': opt.strip(), 'price_modifier': 0})
                    else:
                        # Look at next rows
                        pass
                
                if 'Paper type' in cell_str:
                    if 'options:-' in cell_str:
                        opts = cell_str.split('options:-')[1].split(',')
                        for opt in opts:
                            papers.append({'name': opt.strip(), 'price_modifier': 0})

        # If we found data, update the product
        if bindings:
            product.available_bindings = bindings
            self.create_or_update_field(product, 'binding_type', 'Binding Type', bindings, section='printing_options')
            self.stdout.write(f"Updated bindings for {product.name}: {len(bindings)} found")
            
        if papers:
            product.available_papers = papers
            self.create_or_update_field(product, 'paper_type', 'Paper Type', papers, section='product_specs')
            self.stdout.write(f"Updated papers for {product.name}: {len(papers)} found")
            
        # Also look for "Book Type" (Original + Duplicate etc)
        book_types = []
        start_collecting = False
        for r_idx, row in df.iterrows():
            row_str = str(row.values)
            if 'Book Type' in row_str:
                start_collecting = True
                continue
            
            if start_collecting:
                val = str(row[3]) if len(row) > 3 else 'nan'
                if val != 'nan' and val != 'None':
                    book_types.append({'name': val.strip(), 'price_modifier': 0})
                
                if len(book_types) > 0 and (val == 'nan' or val == 'None'):
                    pass
        
        if book_types:
            current_papers = product.available_papers if product.available_papers else []
            # Merge book types into papers, assuming they are variations of paper type
            for bt in book_types:
                # Check if a paper with the same name already exists
                if not any(p['name'] == bt['name'] for p in current_papers):
                    current_papers.append(bt)
            product.available_papers = current_papers
            
            # Also create a specific field for Book Type if needed, or just update Paper Type
            # Let's update Paper Type with the merged list
            self.create_or_update_field(product, 'paper_type', 'Paper Type', current_papers, section='product_specs')
            self.stdout.write(f"Added {len(book_types)} book types to papers")

    def process_business_card(self, file_path, product):
        df = pd.read_excel(file_path, header=None)
        
        # Global search for Finishes
        finishes = []
        known_finishes = ['matt', 'glossy', 'lamination', 'spot uv', 'foil', 'soft touch']
        
        for r_idx, row in df.iterrows():
            for c_idx, cell in enumerate(row):
                cell_str = str(cell).strip()
                cell_lower = cell_str.lower()
                
                # Check if cell contains any known finish
                for kf in known_finishes:
                    if kf in cell_lower:
                        # Avoid adding the label "Lamination" itself if it's just a label
                        if cell_lower == 'lamination' or cell_lower == 'lamination :-':
                            continue
                            
                        # Clean up
                        # If it contains "Lamination", maybe it's "Matt Lamination"
                        # Add it
                        # Avoid duplicates
                        if not any(f['name'] == cell_str for f in finishes):
                            finishes.append({'name': cell_str, 'price_modifier': 0})
                            self.stdout.write(f"DEBUG: Added finish: {cell_str}")

        if finishes:
            product.available_finishes = finishes
            self.create_or_update_field(product, 'finishing_options', 'Finishing Options', finishes, section='finishing_options', field_type='checkbox')
            self.stdout.write(f"Updated finishes for {product.name}: {len(finishes)} found")

        # Extract Quantity Tiers - Global Search
        tiers = []
        
        # Iterate all cells to find Quantity -> Price pattern
        # Pattern: Cell is Int (Qty) -> Neighbor (Right or Down) is Price
        
        for r_idx, row in df.iterrows():
            for c_idx, cell in enumerate(row):
                try:
                    val = str(cell).strip()
                    if val.isdigit():
                        qty = int(val)
                        if qty < 25: # Ignore small numbers like page counts or indices
                            continue
                            
                        # Check Right Neighbor
                        if c_idx + 1 < len(row):
                            val_right = str(row[c_idx+1]).strip()
                            if self.is_price(val_right):
                                self.add_tier(tiers, qty, val_right)
                                continue
                                
                        # Check Down Neighbor
                        if r_idx + 1 < len(df):
                            val_down = str(df.iloc[r_idx+1, c_idx]).strip()
                            if self.is_price(val_down):
                                self.add_tier(tiers, qty, val_down)
                                continue
                except:
                    continue
                
        if tiers:
            product.specifications['pricing_tiers'] = tiers
            self.stdout.write(f"Updated pricing tiers for {product.name}: {len(tiers)} found")

    def is_price(self, val):
        return val.startswith('₹') or 'Rs' in val or 'price' in val.lower()

    def add_tier(self, tiers, qty, price_str):
        try:
            clean_price = price_str.replace('₹', '').replace('Rs', '').replace(',', '').replace('per item', '').strip()
            price = float(clean_price)
            unit_price = price / qty
            
            # Avoid duplicates
            if not any(t['min_qty'] == qty for t in tiers):
                tiers.append({
                    'min_qty': qty,
                    'max_qty': qty,
                    'unit_price': unit_price,
                    'total_price': price
                })
                self.stdout.write(f"DEBUG: Added tier: {qty} @ {price}")
        except:
            pass

    def process_letter_head(self, file_path, product):
        df = pd.read_excel(file_path, header=None)
        
        # Extract Paper Type
        papers = []
        paper_type_found = False
        target_col = -1
        start_row = -1
        
        for r_idx, row in df.iterrows():
            for c_idx, cell in enumerate(row):
                cell_str = str(cell).strip()
                if 'Paper Type' in cell_str:
                    paper_type_found = True
                    # Values seem to be in the next column, starting next row?
                    # Found at 11,3: Paper Type *
                    # Found at 12,4: JK ...
                    target_col = c_idx + 1
                    start_row = r_idx + 1
                    break
            if paper_type_found:
                break
        
        if paper_type_found and target_col < len(df.columns):
            # Collect values from target_col starting from start_row
            for r in range(start_row, len(df)):
                val = str(df.iloc[r, target_col]).strip()
                if val != 'nan' and val != 'None' and val != '':
                    papers.append({'name': val, 'price_modifier': 0})
                else:
                    # Stop if we hit empty? 
                    # But maybe there are gaps. Let's assume contiguous for now or check a few rows.
                    # If we have found some papers and hit empty, maybe stop.
                    if len(papers) > 0:
                        # Check next few rows to be sure?
                        # For now, just stop to avoid reading garbage
                        break
        
        if papers:
            product.available_papers = papers
            self.create_or_update_field(product, 'paper_type', 'Paper Type', papers, section='product_specs')
            self.stdout.write(f"Updated papers for {product.name}: {len(papers)} found")
            
        # Extract Pricing (similar to Business Card)
        tiers = []
        for i in range(len(df) - 1):
            try:
                val1 = str(df.iloc[i, 0]).strip()
                val2 = str(df.iloc[i+1, 0]).strip()
                
                if val1.isdigit() and (val2.startswith('₹') or 'Rs' in val2):
                    qty = int(val1)
                    price_str = val2.replace('₹', '').replace('Rs', '').replace(',', '').strip()
                    price = float(price_str)
                    unit_price = price / qty
                    
                    tiers.append({
                        'min_qty': qty,
                        'max_qty': qty,
                        'unit_price': unit_price,
                        'total_price': price
                    })
            except:
                continue
                
        if tiers:
            product.specifications['pricing_tiers'] = tiers
            self.stdout.write(f"Updated pricing tiers for {product.name}: {len(tiers)} found")
