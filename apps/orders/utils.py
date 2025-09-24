# apps/orders/utils.py
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem, Order, Coupon
from decimal import Decimal
from django.utils import timezone


class CartManager:
    """Utility class to manage shopping cart operations"""
    
    def __init__(self, request):
        self.request = request
        self.user = request.user if request.user.is_authenticated else None
        self.session = request.session
        
    def get_or_create_cart(self):
        """Get or create cart for current user/session"""
        if self.user:
            cart, created = Cart.objects.get_or_create(user=self.user)
        else:
            session_key = self.session.session_key
            if not session_key:
                self.session.save()
                session_key = self.session.session_key
            
            cart, created = Cart.objects.get_or_create(session_key=session_key)
        
        return cart
    
    def add_item(self, product, quantity=1, user_design=None, uploaded_file=None, specifications=None):
        """Add item to cart"""
        cart = self.get_or_create_cart()
        
        # Check if item already exists in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            user_design=user_design,
            defaults={
                'quantity': quantity,
                'unit_price': product.base_price,
                'uploaded_file': uploaded_file,
                'specifications': specifications or {}
            }
        )
        
        if not created:
            # Update quantity if item already exists
            cart_item.quantity += quantity
            cart_item.save()
        
        return cart_item
    
    def update_item_quantity(self, item_id, quantity):
        """Update cart item quantity"""
        cart = self.get_or_create_cart()
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()
        
        return cart_item
    
    def remove_item(self, item_id):
        """Remove item from cart"""
        cart = self.get_or_create_cart()
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        cart_item.delete()
        
    def clear_cart(self):
        """Clear all items from cart"""
        cart = self.get_or_create_cart()
        cart.items.all().delete()
    
    def get_cart_count(self):
        """Get total number of items in cart"""
        try:
            cart = self.get_or_create_cart()
            return cart.total_items
        except:
            return 0
    
    def get_cart_total(self):
        """Get cart total amount"""
        try:
            cart = self.get_or_create_cart()
            return cart.subtotal
        except:
            return Decimal('0.00')
    
    def apply_coupon(self, coupon_code):
        """Apply coupon to cart"""
        try:
            coupon = Coupon.objects.get(code=coupon_code.upper())
            cart = self.get_or_create_cart()
            
            if not coupon.is_valid:
                return False, "Coupon is not valid or has expired"
            
            cart_total = cart.subtotal
            if cart_total < coupon.minimum_amount:
                return False, f"Minimum order amount ₹{coupon.minimum_amount} required"
            
            discount = coupon.apply_discount(cart_total)
            return True, discount
            
        except Coupon.DoesNotExist:
            return False, "Invalid coupon code"
    
    def merge_carts(self, user):
        """Merge anonymous cart with user cart after login"""
        if not self.session.session_key:
            return
        
        try:
            # Get anonymous cart
            anonymous_cart = Cart.objects.get(session_key=self.session.session_key)
            
            # Get or create user cart
            user_cart, created = Cart.objects.get_or_create(user=user)
            
            # Merge items from anonymous cart to user cart
            for item in anonymous_cart.items.all():
                existing_item = user_cart.items.filter(
                    product=item.product,
                    user_design=item.user_design
                ).first()
                
                if existing_item:
                    existing_item.quantity += item.quantity
                    existing_item.save()
                else:
                    item.cart = user_cart
                    item.save()
            
            # Delete anonymous cart
            anonymous_cart.delete()
            
        except Cart.DoesNotExist:
            pass


