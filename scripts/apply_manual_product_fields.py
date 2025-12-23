import os
import sys
import django
import json

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shirsti_printing.settings')
django.setup()

from apps.services.models import StaticProduct, ProductFormField
from django.utils.text import slugify

# Data provided by user
DATA = {
    # ... (Keep existing Address Labels etc if needed, but easier to just redefine whole dict or merge)
    # Merging logic (previous list + new request keys)
    "Address Labels": {
        "Shape": ["Round", "Square / Rectangle", "Round Edge Square/ Rectangle", "Oval", "Custom/Any Shape", "Arch"],
        "Size": ["2in x 2in", "1in x 1in", "1in x 2in", "1.5in x 1.5in", "1.5in x 3in", "2in x 3in", "2in x 4in",
                 "2.5in x 2.5in", "2.5in x 4in", "3in x 3in", "3in x 4in", "3in x 6in", "3in x 8in", "4in x 4in",
                 "4in x 6in", "4in x 8in", "6in x 6in", "Custom Size"],
        "Quantity": ["25", "50", "100", "200", "300", "400", "500", "750", "1000", "1250", "1500", "2000", "3000",
                     "4000", "5000", "7500", "10000", "20000"]
    },
    "Button Badges": {
        "Size": ["40 mm Dia (Small Size)", "60 mm Dia (Big Size)"],
        "Qty.": ["100", "200", "300", "400", "500"]
    },
    "Tent Card": {
        "Size": ["A-5 (5.8 x 8.3 inches) Portrait", "A-4 (11.7 x 8.3 inches) Landscape", "A-5 (8.3 x 5.8 inches) Landscape",
                 "A-6 (4.1 x 5.8 inches) Portrait", "A-6 (5.8 x 4.1 inches) Landscape"],
        "Select Paper Material": ["250 Gsm Art paper", "300 Gsm Art paper"],
        "Qty.": ["100", "200", "300", "400", "500"]
    },
    "Certificates": {
        "Size": ["A-5 (5.8 x 8.3 inches)", "A-4 (11.7 x 8.3 inches)", "A-3 (11.7 x 16.5 inches)"],
        "Select Paper Material": ["350 Gsm Art paper", "300 Gsm Art paper"],
        "Qty.": ["100", "200", "300", "400", "500"]
    },
    "Standard Business Card": {
        "Printing Side": ["Front Side", "Back Side"],
        "Corner Style": ["Straight Corners", "Rounded Corners"],
        "Lamination": ["None", "Matt Lamnation", "Gloss Lamnation"],
        "Qty.": ["200", "300", "400", "500", "600", "700", "800", "900", "1000"]
    },
    "TEXTURE BUSINESS CARD": {
        "Paper Materials": ["Fine Needle Point", "Rendezvous Hi Print", "Contrast Ivory", "Contrast N White",
                            "Contrast Laid White", "Mermaid Linen", "Leathack 85 White", "Leathack 205 White"],
        "Printing Side": ["Front Side", "Back Side"],
        "Qty.": ["200", "300", "400", "500", "600", "700", "800", "900", "1000"]
    },
    "Corporate Letter Head": {
        "Size": ["A-4"],
        "Paper Type": ["JK Excecl Bond Paper 100 Gsm", "DO Paper 100 Gsm"],
        "Qty.": ["500", "1000", "1500", "2000"]
    },
    "Standard Letter Head": {
        "Size": ["A-4"],
        "Paper Type": ["JK Excecl Bond Paper 100 Gsm", "DO Paper 100 Gsm"],
        "Printed Sides": ["Single Side", "Both Side"],
        "Qty.": ["200", "300", "400", "500", "600", "700", "800", "900", "1000"]
    },
    # Envelopes: Special handling in code loop, but defining defaults here
    "Envelopes": {
        "Size": ["10 x 4.5"], # Default, will be overridden by loop
        "Paper Type": ["80 Gsm", "100 gsm", "120 gsm"],
        "Printing": ["Black & White", "Colour"],
        "Qty.": ["100", "200", "300", "400", "500", "1000", "2000", "3000"]
    },
    "Black & White Bill Book": {
        "Book Type": ["Original + Duplicate", "Original + 1 Duplicate", "Original + 2 Duplicate", "Original + 3 Duplicate"],
        "1 st Duplicate Sheet Colour": ["Pink", "Yellow", "Light Green", "Light Blue"],
        "2 nd Duplicate Sheet Colour": ["Pink", "Yellow", "Light Green", "Light Blue"],
        "3rd Duplicate Sheet Colour": ["Pink", "Yellow", "Light Green", "Light Blue"],
        "Invoice Numbering": ["With Invoice Number", "Without Invoice Number"],
        "Starting Inoice Number": ["No."],
        "Qty.": ["2", "5", "10", "15", "20"]
    },
    "Colour Bill Book": {
        "Book Type": ["Original + Duplicate", "Original + 1 Duplicate", "Original + 2 Duplicate", "Original + 3 Duplicate"],
        "1 st Duplicate Sheet Colour": ["Pink", "Yellow", "Light Green", "Light Blue"],
        "2 nd Duplicate Sheet Colour": ["Pink", "Yellow", "Light Green", "Light Blue"],
        "3rd Duplicate Sheet Colour": ["Pink", "Yellow", "Light Green", "Light Blue"],
        "Invoice Numbering": ["With Invoice Number", "Without Invoice Number"],
        "Starting Inoice Number": ["No."],
        "Qty.": ["2", "5", "10", "15", "20"]
    },
    "Event ID Cards": {
        "ID Card Finish": ["Matt Lamination", "Gloosy Lamination"],
        "Orientation": ["Portrait", "Landscape"],
        "Print Location": ["Front Side", "Back Side"],
        "Qty.": ["100", "200", "300", "400", "500", "1000", "2000", "3000"]
    },
    "Multicolour Lanyards": {
        "Attachment Type": ["SD Lever Hook"],
        "Qty.": ["100", "200", "300", "400", "500", "1000", "2000", "3000"]
    },
    "PVC ID Cards": {
        "ID Card Finish": ["Matt Lamination", "Gloosy Lamination"],
        "Orientation": ["Portrait", "Landscape"],
        "Print Location": ["Front Side", "Back Side"],
        "Qty.": ["100", "200", "300", "400", "500", "1000", "2000", "3000"]
    },
    "Custom Paper Boxes": {
        "Size L x W x H": ["1.5 x 1.5 x 4 inch", "2 x 2 x 2 inch", "3 x 3 x 3.5 inch", "4 x 4 x 3 inch", "Custom Size"],
        "Select Paper Type": ["300 gsm Board (Matt Finish)", "300 gsm Board (Gloss Finish)", "300 gsm Board (Spot UV)", "300 gsm Board (Raised Foiling)"],
        "Foil Colour": ["Gold Foil", "Silver Foil"],
        "Qty.": ["100", "200", "300", "400", "500"]
    },
    "Hang Tags": {
        "Select Shape": ["Normal", "Classic", "Round", "Other"],
        "Size": ["2 x 3.5 inch", "2.5 x 2.5 inch", "2.5 x 4 inch", "2.5 x 5 inch", "3.5 x 4.5 inch", "2.5 x 3 inch", "1 x 4 inch", "2 x 2 inch", "2.75 x 4.25 inch", "Other Size"],
        "Paper Qualit": ["300 gsm Standard Art Board", "400 gsm Standard Art Board"],
        "Printed Side": ["Single Side", "Both Side"]
    },
    "Paper Bag": {
        "Size": ["Small - 6 x 4 x 9 inch", "Medium - 9 x 8.25 x 7.5 inch", "Big - 12 x 5 x 9 inch", "Other Size"],
        "Print Color": ["Single Color", "Four Color"],
        "Paper Quality": ["120 gsm White Paper", "130 gsm White Art Paper", "170 gsm White Art Paper"],
        "Printed Side": ["Both Side"],
        "Qty.": ["100", "200", "300", "400", "500"]
    },
    # Note: Flyer, Dangler, Premium Paper Bag, Mailer Box, Spot UV not found in DB
    # Adding Poster sub-services data back to merge
    "Size A-3": {
  	      "Size": ["A-3", "A-4", "Custom Size"],
 	      "Paper Quality": ["170 Gsm", "250 Gsm", "300 Gsm"],
	      "Lamination": ["None", "Matt Lamination", "Gloss Lamination"],
	      "Printed Sides": ["Single Side"],
	      "Glued Edges": ["None", "0.5 inch Wide Glued Edges"],
	      "Corner Style": ["Straight Corners"],
	      "Qty.": ["100", "200", "300", "400", "500"]
    },
    "Size A-4": {
  	      "Size": ["A-3", "A-4", "Custom Size"],
 	      "Paper Quality": ["170 Gsm", "250 Gsm", "300 Gsm"],
	      "Lamination": ["None", "Matt Lamination", "Gloss Lamination"],
	      "Printed Sides": ["Single Side"],
	      "Glued Edges": ["None", "0.5 inch Wide Glued Edges"],
	      "Corner Style": ["Straight Corners"],
	      "Qty.": ["100", "200", "300", "400", "500"]
    },
    "Custom Size": {
  	      "Size": ["A-3", "A-4", "Custom Size"],
 	      "Paper Quality": ["170 Gsm", "250 Gsm", "300 Gsm"],
	      "Lamination": ["None", "Matt Lamination", "Gloss Lamination"],
	      "Printed Sides": ["Single Side"],
	      "Glued Edges": ["None", "0.5 inch Wide Glued Edges"],
	      "Corner Style": ["Straight Corners"],
	      "Qty.": ["100", "200", "300", "400", "500"]
    }
}

def apply_updates():
    print("Applying manual field updates...")
    
    # Handle Envelopes explicitly
    envelope_data = DATA.pop("Envelopes", None)
    if envelope_data:
        # Find all envelope products (Envelopes A-4, Envelopes 10x4.5 etc)
        # Using a startswith or contains logic
        env_products = StaticProduct.objects.filter(name__icontains="Envelope")
        for prod in env_products:
            print(f"\nProcessing Envelope: {prod.name}...")
            ProductFormField.objects.filter(static_product=prod).delete()
            
            # 1. Size Field - Dynamic based on name
            size_val = "10 x 4.5" # Fallback
            if "A-4" in prod.name: size_val = "A-4"
            elif "A-3" in prod.name: size_val = "A-3"
            elif "A-5" in prod.name: size_val = "A-5"
            elif "A-6" in prod.name: size_val = "A-6"
            elif "10x 4.5" in prod.name: size_val = "10 x 4.5"
            
            # Create Size Field
            ProductFormField.objects.create(
                static_product=prod,
                field_name='size',
                field_label='Size',
                field_type='select',
                order=1,
                is_required=True,
                is_price_affecting=True,
                options=json.dumps([{"value": size_val, "label": size_val, "price_modifier": 0}])
            )
            
            # 2. Other fields from 'envelope_data'
            order = 2
            for label, options_list in envelope_data.items():
                if label == "Size": continue # Skipped, handled above
                
                clean_options = [{"value": o, "label": o, "price_modifier": 0} for o in options_list]
                ProductFormField.objects.create(
                    static_product=prod,
                    field_name=slugify(label).replace('-', '_'),
                    field_label=label,
                    field_type='select',
                    order=order,
                    is_required=True,
                    is_price_affecting=True,
                    options=json.dumps(clean_options)
                )
                order += 1
    
    # Process regular dictionary items
    for product_name, fields in DATA.items():
        print(f"\nProcessing {product_name}...")
        
        # 1. Find Product
        # Try generic lookup
        product = StaticProduct.objects.filter(name__iexact=product_name).first()
        if not product:
            # Try fuzzy or partial?
            # Creating new if not exists? No, user said "apply them". match existing.
            print(f"X Product '{product_name}' not found in DB.")
            continue
            
        # 2. Clear Existing Fields
        curr_count = ProductFormField.objects.filter(static_product=product).count()
        ProductFormField.objects.filter(static_product=product).delete()
        print(f"  - Deleted {curr_count} existing fields.")
        
        # 3. Create New Fields
        order = 1
        for label, options_list in fields.items():
            # Determine type
            ftype = 'select'
            # Check if Quantity
            if 'quantity' in label.lower():
                ftype = 'select' # User provided specific quantity steps, so dropdown is better than free input
                
            # Clean options
            clean_options = []
            for opt in options_list:
                clean_options.append({
                    "value": opt,
                    "label": opt,
                    "price_modifier": 0
                })
            
            # Create
            ProductFormField.objects.create(
                static_product=product,
                field_name=slugify(label).replace('-', '_'),
                field_label=label,
                field_type=ftype,
                order=order,
                is_required=True,
                is_price_affecting=True,
                options=json.dumps(clean_options)
            )
            print(f"  + Added '{label}' with {len(clean_options)} options")
            order += 1
            
    print("\nDone!")

if __name__ == "__main__":
    apply_updates()
