import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shirsti_printing.settings')
django.setup()

from apps.services.models import StaticProduct

# Map of Product Name -> Image Filename (relative to media root)
mapping = {
    # Generated Images (Keep these)
    "Address Labels": "products/address_labels.png",
    "Bi-fold Brochure": "products/bifold_brochure.png",
    "Flyers & Leaflets": "products/flyers.png",
    "Custom Paper Boxes": "products/paper_boxes.png",
    "Paper Bags": "products/paper_bags.png",
    "PVC ID Cards": "products/pvc_id_cards.png",
    "Custom Roll Up Standees": "products/standees.png",

    # Mapped to Address Labels (Rolls/Stickers)
    "Barcode Labels": "products/address_labels.png",
    "Warning Labels": "products/address_labels.png",
    "Product Labels": "products/address_labels.png",
    "Circle Stickers": "products/address_labels.png",
    "Custom Stickers": "products/address_labels.png",
    "Rectangle Stickers": "products/address_labels.png",
    "Square Stickers": "products/address_labels.png",
    "Button Badges": "products/address_labels.png",

    # Mapped to Brochures (Folded/Paper)
    "Tri-fold Brochure": "products/bifold_brochure.png",
    "Catalogues": "products/bifold_brochure.png",
    "Certificates": "products/bifold_brochure.png",
    "Tent Cards": "products/bifold_brochure.png",
    "Envelopes 10x 4.5": "products/bifold_brochure.png",
    "Envelopes A-5": "products/bifold_brochure.png",
    "Envelopes A-6": "products/bifold_brochure.png",

    # Mapped to Flyers (Single Sheet/Display)
    "Poster": "products/flyers.png",
    "Posters": "products/flyers.png",
    "Brochures": "products/bifold_brochure.png",
    "Flyers": "products/flyers.png",

    # NEW: Mapped to specific existing images
    "Danglers": "products/danglers.jpg",
    "Kraft Paper Product Box": "products/kraft_box.png",
    "Printed Corrugated Mailer Box (Single Color)": "products/corrugated_box.png",
    
    # Mapped to Paper Boxes (Packaging)
    "Pen Drives": "products/paper_boxes.png",

    # Mapped to Paper Bags
    "Premium Paper Bags": "products/paper_bags.png",

    # Mapped to ID Cards (Plastic/Hanging)
    "Event ID Cards": "products/pvc_id_cards.png",
    "Multicolour Lanyards": "products/pvc_id_cards.png",
    "Hang Tags": "products/pvc_id_cards.png",
    "NonTear Hang Tags": "products/pvc_id_cards.png",
    "Spot UV Hang Tags": "products/pvc_id_cards.png",
    "Standees": "products/standees.png",
}

for name, image_path in mapping.items():
    try:
        product = StaticProduct.objects.get(name=name)
        product.featured_image = image_path
        # product.hero_image = image_path 
        product.save()
        print(f"Updated {name} -> {image_path}")
    except StaticProduct.DoesNotExist:
        print(f"Product {name} not found")
    except Exception as e:
        print(f"Error updating {name}: {e}")
