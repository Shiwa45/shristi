# apps/orders/checkout_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from django.http import JsonResponse
from .models import Cart, Order, OrderItem, OrderStatusHistory, Coupon, CouponUsage
from .utils import CartManager
from decimal import Decimal
import json


@method_decorator(login_required, name='dispatch')
class CheckoutView(View):
    """Multi-step checkout process - Step 1: Review Cart"""
    
    def get(self, request):
        cart_manager = CartManager(request)
        cart = cart_manager.get_or_create_cart()
        
        if not cart.items.exists():
            messages.error(request, 'Your cart is empty.')
            return redirect('orders:cart')
        
        context = {
            'cart': cart,
            'cart_items': cart.items.select_related('product', 'user_design'),
            'step': 1,
            'steps': [
                {'number': 1, 'name': 'Review Cart', 'current': True},
                {'number': 2, 'name': 'Shipping Info', 'current': False},
                {'number': 3, 'name': 'Payment', 'current': False},
                {'number': 4, 'name': 'Confirmation', 'current': False},
            ]
        }
        return render(request, 'orders/checkout/review.html', context)
    
    def post(self, request):
        # Handle coupon application or proceed to next step
        action = request.POST.get('action')
        
        if action == 'apply_coupon':
            return self.apply_coupon(request)
        elif action == 'proceed':
            return redirect('orders:checkout_shipping')
        
        return redirect('orders:checkout')
    
    def apply_coupon(self, request):
        coupon_code = request.POST.get('coupon_code', '').strip()
        cart_manager = CartManager(request)
        
        is_valid, result = cart_manager.apply_coupon(coupon_code)
        
        if is_valid:
            messages.success(request, f'Coupon applied! You saved ₹{result}')
            # Store coupon in session for later use
            request.session['applied_coupon'] = {
                'code': coupon_code.upper(),
                'discount': str(result)
            }
        else:
            messages.error(request, result)
        
        return redirect('orders:checkout')


@method_decorator(login_required, name='dispatch')
class CheckoutShippingView(View):
    """Checkout Step 2: Shipping Information"""
    
    def get(self, request):
        cart_manager = CartManager(request)
        cart = cart_manager.get_or_create_cart()
        
        if not cart.items.exists():
            messages.error(request, 'Your cart is empty.')
            return redirect('orders:cart')
        
        # Pre-fill with user's profile information if available
        initial_data = {
            'customer_name': request.user.get_full_name() or request.user.username,
            'customer_email': request.user.email,
        }
        
        # Check if user has previous orders to pre-fill address
        previous_order = Order.objects.filter(user=request.user).first()
        if previous_order:
            initial_data.update({
                'customer_phone': previous_order.customer_phone,
                'billing_address_line1': previous_order.billing_address_line1,
                'billing_address_line2': previous_order.billing_address_line2,
                'billing_city': previous_order.billing_city,
                'billing_state': previous_order.billing_state,
                'billing_pincode': previous_order.billing_pincode,
                'billing_country': previous_order.billing_country,
            })
        
        context = {
            'cart': cart,
            'initial_data': initial_data,
            'step': 2,
            'steps': [
                {'number': 1, 'name': 'Review Cart', 'current': False},
                {'number': 2, 'name': 'Shipping Info', 'current': True},
                {'number': 3, 'name': 'Payment', 'current': False},
                {'number': 4, 'name': 'Confirmation', 'current': False},
            ]
        }
        return render(request, 'orders/checkout/shipping.html', context)
    
    def post(self, request):
        # Validate and store shipping information in session
        shipping_data = {
            'customer_name': request.POST.get('customer_name', '').strip(),
            'customer_email': request.POST.get('customer_email', '').strip(),
            'customer_phone': request.POST.get('customer_phone', '').strip(),
            'billing_address_line1': request.POST.get('billing_address_line1', '').strip(),
            'billing_address_line2': request.POST.get('billing_address_line2', '').strip(),
            'billing_city': request.POST.get('billing_city', '').strip(),
            'billing_state': request.POST.get('billing_state', '').strip(),
            'billing_pincode': request.POST.get('billing_pincode', '').strip(),
            'billing_country': request.POST.get('billing_country', 'India'),
            'shipping_same_as_billing': request.POST.get('shipping_same_as_billing') == 'on',
        }
        
        # Add shipping address if different from billing
        if not shipping_data['shipping_same_as_billing']:
            shipping_data.update({
                'shipping_address_line1': request.POST.get('shipping_address_line1', '').strip(),
                'shipping_address_line2': request.POST.get('shipping_address_line2', '').strip(),
                'shipping_city': request.POST.get('shipping_city', '').strip(),
                'shipping_state': request.POST.get('shipping_state', '').strip(),
                'shipping_pincode': request.POST.get('shipping_pincode', '').strip(),
                'shipping_country': request.POST.get('shipping_country', 'India'),
            })
        
        # Basic validation
        required_fields = ['customer_name', 'customer_email', 'customer_phone', 
                          'billing_address_line1', 'billing_city', 'billing_state', 'billing_pincode']
        
        for field in required_fields:
            if not shipping_data.get(field):
                messages.error(request, f'Please fill in all required fields.')
                return self.get(request)
        
        # Store in session
        request.session['shipping_data'] = shipping_data
        
        return redirect('orders:checkout_payment')


@method_decorator(login_required, name='dispatch')
class CheckoutPaymentView(View):
    """Checkout Step 3: Payment Selection"""
    
    def get(self, request):
        # Check if shipping data is in session
        if 'shipping_data' not in request.session:
            messages.error(request, 'Please complete shipping information first.')
            return redirect('orders:checkout_shipping')
        
        cart_manager = CartManager(request)
        cart = cart_manager.get_or_create_cart()
        
        if not cart.items.exists():
            messages.error(request, 'Your cart is empty.')
            return redirect('orders:cart')
        
        # Calculate totals
        subtotal = cart.subtotal
        applied_coupon = request.session.get('applied_coupon')
        discount_amount = Decimal(applied_coupon['discount']) if applied_coupon else Decimal('0.00')
        discounted_subtotal = subtotal - discount_amount
        tax_amount = discounted_subtotal * Decimal('0.18')  # 18% GST
        shipping_cost = Decimal('0.00')  # Free shipping for now
        total_amount = discounted_subtotal + tax_amount + shipping_cost
        
        context = {
            'cart': cart,
            'subtotal': subtotal,
            'discount_amount': discount_amount,
            'tax_amount': tax_amount,
            'shipping_cost': shipping_cost,
            'total_amount': total_amount,
            'applied_coupon': applied_coupon,
            'step': 3,
            'steps': [
                {'number': 1, 'name': 'Review Cart', 'current': False},
                {'number': 2, 'name': 'Shipping Info', 'current': False},
                {'number': 3, 'name': 'Payment', 'current': True},
                {'number': 4, 'name': 'Confirmation', 'current': False},
            ]
        }
        return render(request, 'orders/checkout/payment.html', context)
    
    def post(self, request):
        payment_method = request.POST.get('payment_method')
        
        if not payment_method:
            messages.error(request, 'Please select a payment method.')
            return self.get(request)
        
        # Store payment method in session
        request.session['payment_method'] = payment_method
        
        return redirect('orders:checkout_confirm')


@method_decorator(login_required, name='dispatch')
class CheckoutConfirmView(View):
    """Checkout Step 4: Order Confirmation and Creation"""
    
    def get(self, request):
        # Check required session data
        if 'shipping_data' not in request.session or 'payment_method' not in request.session:
            messages.error(request, 'Please complete all checkout steps.')
            return redirect('orders:checkout')
        
        cart_manager = CartManager(request)
        cart = cart_manager.get_or_create_cart()
        
        if not cart.items.exists():
            messages.error(request, 'Your cart is empty.')
            return redirect('orders:cart')
        
        # Calculate final totals
        subtotal = cart.subtotal
        applied_coupon = request.session.get('applied_coupon')
        discount_amount = Decimal(applied_coupon['discount']) if applied_coupon else Decimal('0.00')
        discounted_subtotal = subtotal - discount_amount
        tax_amount = discounted_subtotal * Decimal('0.18')
        shipping_cost = Decimal('0.00')
        total_amount = discounted_subtotal + tax_amount + shipping_cost
        
        context = {
            'cart': cart,
            'cart_items': cart.items.select_related('product', 'user_design'),
            'shipping_data': request.session['shipping_data'],
            'payment_method': request.session['payment_method'],
            'subtotal': subtotal,
            'discount_amount': discount_amount,
            'tax_amount': tax_amount,
            'shipping_cost': shipping_cost,
            'total_amount': total_amount,
            'applied_coupon': applied_coupon,
            'step': 4,
            'steps': [
                {'number': 1, 'name': 'Review Cart', 'current': False},
                {'number': 2, 'name': 'Shipping Info', 'current': False},
                {'number': 3, 'name': 'Payment', 'current': False},
                {'number': 4, 'name': 'Confirmation', 'current': True},
            ]
        }
        return render(request, 'orders/checkout/confirm.html', context)
    
    def post(self, request):
        try:
            # Create the order
            order = self.create_order(request)
            
            # Clear session data
            self.clear_checkout_session(request)
            
            # Send confirmation email (implement later)
            # self.send_confirmation_email(order)
            
            messages.success(request, f'Order {order.order_number} has been placed successfully!')
            return redirect('orders:checkout_success', order_number=order.order_number)
            
        except Exception as e:
            messages.error(request, 'There was an error processing your order. Please try again.')
            return redirect('orders:checkout_confirm')
    
    def create_order(self, request):
        cart_manager = CartManager(request)
        cart = cart_manager.get_or_create_cart()
        shipping_data = request.session['shipping_data']
        payment_method = request.session['payment_method']
        applied_coupon = request.session.get('applied_coupon')
        
        # Calculate totals
        subtotal = cart.subtotal
        discount_amount = Decimal(applied_coupon['discount']) if applied_coupon else Decimal('0.00')
        discounted_subtotal = subtotal - discount_amount
        tax_amount = discounted_subtotal * Decimal('0.18')
        shipping_cost = Decimal('0.00')
        total_amount = discounted_subtotal + tax_amount + shipping_cost
        
        # Create order
        order_data = {
            'user': request.user,
            'status': 'pending' if payment_method == 'cod' else 'pending',
            'payment_status': 'pending',
            'subtotal': subtotal,
            'discount_amount': discount_amount,
            'tax_amount': tax_amount,
            'shipping_cost': shipping_cost,
            'total_amount': total_amount,
            'notes': request.POST.get('notes', ''),
        }
        
        # Add shipping data
        order_data.update(shipping_data)
        
        # Add coupon information
        if applied_coupon:
            order_data.update({
                'coupon_code': applied_coupon['code'],
                'coupon_discount': discount_amount
            })
        
        order = Order.objects.create(**order_data)
        
        # Create order items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                user_design=cart_item.user_design,
                uploaded_file=cart_item.uploaded_file,
                product_name=cart_item.product.name,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                total_price=cart_item.total_price,
                specifications=cart_item.specifications
            )
        
        # Create initial status history
        OrderStatusHistory.objects.create(
            order=order,
            old_status='',
            new_status=order.status,
            notes='Order created',
            changed_by=request.user
        )
        
        # Record coupon usage
        if applied_coupon:
            try:
                coupon = Coupon.objects.get(code=applied_coupon['code'])
                CouponUsage.objects.create(
                    coupon=coupon,
                    user=request.user,
                    order=order,
                    discount_amount=discount_amount
                )
                coupon.used_count += 1
                coupon.save()
            except Coupon.DoesNotExist:
                pass
        
        # Clear cart
        cart.items.all().delete()
        
        return order
    
    def clear_checkout_session(self, request):
        """Clear checkout-related session data"""
        session_keys = ['shipping_data', 'payment_method', 'applied_coupon']
        for key in session_keys:
            if key in request.session:
                del request.session[key]


@method_decorator(login_required, name='dispatch')
class CheckoutSuccessView(View):
    """Order success page"""
    
    def get(self, request, order_number):
        order = get_object_or_404(
            Order,
            order_number=order_number,
            user=request.user
        )
        
        context = {
            'order': order,
            'order_items': order.items.select_related('product'),
        }
        return render(request, 'orders/checkout/success.html', context)