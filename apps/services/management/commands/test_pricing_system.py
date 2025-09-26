# apps/services/management/commands/test_pricing_system.py
from django.core.management.base import BaseCommand
from apps.services.models import Product, ProductFormField


class Command(BaseCommand):
    help = 'Test the pricing system functionality'

    def handle(self, *args, **options):
        # Test a specific product
        try:
            product = Product.objects.filter(name__icontains='business').first()
            if not product:
                self.stdout.write(self.style.ERROR('No business card product found'))
                return
            
            self.stdout.write(f'Testing product: {product.name}')
            self.stdout.write(f'Base price: ₹{product.base_price}')
            
            # Get form fields
            form_fields = product.form_fields.filter(is_active=True).order_by('order')
            self.stdout.write(f'Form fields: {form_fields.count()}')
            
            for field in form_fields:
                self.stdout.write(f'\n--- {field.field_label} ({field.field_type}) ---')
                options = field.get_options()
                for option in options:
                    modifier = option.get('price_modifier', 0)
                    if modifier > 0:
                        self.stdout.write(f'  {option["label"]} (+₹{modifier})')
                    elif modifier < 0:
                        self.stdout.write(f'  {option["label"]} ({modifier*100:.0f}% off)')
                    else:
                        self.stdout.write(f'  {option["label"]} (base price)')
            
            # Test price calculation
            self.stdout.write(f'\n--- Price Calculation Test ---')
            base_price = float(product.base_price)
            
            # Test quantity discount
            quantity_field = form_fields.filter(field_name='quantity').first()
            if quantity_field:
                options = quantity_field.get_options()
                for option in options:
                    qty = int(option['value'])
                    modifier = option.get('price_modifier', 0)
                    
                    if modifier < 0:  # Percentage discount
                        unit_price = base_price * (1 + modifier)
                    else:
                        unit_price = base_price + modifier
                    
                    total_price = unit_price * qty
                    
                    self.stdout.write(f'  {qty} cards: ₹{unit_price:.2f} each = ₹{total_price:.2f} total')
            
            self.stdout.write(self.style.SUCCESS('\n✅ Pricing system test completed'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))