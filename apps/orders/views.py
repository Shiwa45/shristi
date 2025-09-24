# apps/orders/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from .models import Cart, CartItem, Order, QuoteRequest, Coupon
from .utils import CartManager
from apps.services.models import Product
import json


class CartView(View):
    """Shopping cart page"""
    
    def get(self, request):
        cart_manager = CartManager(request)
        cart = cart_manager.get_or_create_cart()
        
        context = {
            'cart': cart,
            'cart_items': cart.items.select_related('product', 'user_design'),
            'cart_total': cart.subtotal,
            'cart_count': cart.total_items,
        }
        return render(request, 'orders/cart.html', context)


class AddToCartView(View):
    """Add item to cart via AJAX"""
    
    def post(self, request, product_id):
        try:
            product = get_object_or_404(Product, id=product_id)
            data = json.loads(request.body)
            
            quantity = int(data.get('quantity', 1))
            specifications = data.get('specifications', {})
            design_id = data.get('design_id')
            
            cart_manager = CartManager(request)
            
            # Get user design if provided
            user_design = None
            if design_id and request.user.is_authenticated:
                from templates_mgmt.models import UserDesign
                try:
                    user_design = UserDesign.objects.get(id=design_id, user=request.user)
                except UserDesign.DoesNotExist:
                    pass
            
            cart_item = cart_manager.add_item(
                product=product,
                quantity=quantity,
                user_design=user_design,
                specifications=specifications
            )
            
            return JsonResponse({
                'success': True,
                'message': f'{product.name} added to cart',
                'cart_count': cart_manager.get_cart_count(),
                'cart_total': str(cart_manager.get_cart_total())
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Error adding item to cart'
            }, status=400)


class UpdateCartView(View):
    """Update cart item quantity"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            quantity = int(data.get('quantity', 1))
            
            cart_manager = CartManager(request)
            
            if quantity > 0:
                cart_manager.update_item_quantity(item_id, quantity)
                message = 'Cart updated successfully'
            else:
                cart_manager.remove_item(item_id)
                message = 'Item removed from cart'
            
            return JsonResponse({
                'success': True,
                'message': message,
                'cart_count': cart_manager.get_cart_count(),
                'cart_total': str(cart_manager.get_cart_total())
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Error updating cart'
            }, status=400)


class RemoveFromCartView(View):
    """Remove item from cart"""
    
    def post(self, request, item_id):
        try:
            cart_manager = CartManager(request)
            cart_manager.remove_item(item_id)
            
            return JsonResponse({
                'success': True,
                'message': 'Item removed from cart',
                'cart_count': cart_manager.get_cart_count(),
                'cart_total': str(cart_manager.get_cart_total())
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Error removing item'
            }, status=400)


class ApplyCouponView(View):
    """Apply coupon to cart"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            coupon_code = data.get('coupon_code', '').strip()
            
            if not coupon_code:
                return JsonResponse({
                    'success': False,
                    'message': 'Please enter a coupon code'
                })
            
            cart_manager = CartManager(request)
            is_valid, result = cart_manager.apply_coupon(coupon_code)
            
            if is_valid:
                return JsonResponse({
                    'success': True,
                    'message': f'Coupon applied! You saved ₹{result}',
                    'discount': str(result),
                    'coupon_code': coupon_code.upper()
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': result
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Error applying coupon'
            }, status=400)


@login_required
def orders_index(request):
    """User orders listing"""
    orders = Order.objects.filter(user=request.user).exclude(status='draft').order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'orders': page_obj,
        'status_filter': status_filter,
        'order_statuses': Order.STATUS_CHOICES,
    }
    return render(request, 'orders/index.html', context)


@login_required
def order_detail(request, order_number):
    """Order detail page"""
    order = get_object_or_404(
        Order, 
        order_number=order_number, 
        user=request.user
    )
    
    context = {
        'order': order,
        'order_items': order.items.select_related('product'),
        'status_history': order.status_history.select_related('changed_by')[:10],
    }
    return render(request, 'orders/detail.html', context)


@login_required
def cancel_order(request, order_number):
    """Cancel order"""
    if request.method == 'POST':
        order = get_object_or_404(
            Order, 
            order_number=order_number, 
            user=request.user
        )
        
        if order.can_cancel:
            old_status = order.status
            order.status = 'cancelled'
            order.save()
            
            # Create status history
            from .models import OrderStatusHistory
            OrderStatusHistory.objects.create(
                order=order,
                old_status=old_status,
                new_status='cancelled',
                notes='Cancelled by customer',
                changed_by=request.user
            )
            
            messages.success(request, f'Order {order.order_number} has been cancelled.')
        else:
            messages.error(request, 'This order cannot be cancelled.')
    
    return redirect('orders:detail', order_number=order_number)


# Quote Request Views
@login_required
def quote_request_view(request):
    """Create quote request"""
    if request.method == 'POST':
        # Handle quote request form submission
        quote_data = {
            'user': request.user,
            'customer_name': request.POST.get('customer_name'),
            'customer_email': request.POST.get('customer_email'),
            'customer_phone': request.POST.get('customer_phone'),
            'company_name': request.POST.get('company_name', ''),
            'description': request.POST.get('description'),
            'requirements': request.POST.get('requirements', ''),
            'quantity': int(request.POST.get('quantity', 1)),
            'budget_range': request.POST.get('budget_range', ''),
        }
        
        quote_request = QuoteRequest.objects.create(**quote_data)
        
        # Handle file upload
        if 'reference_files' in request.FILES:
            quote_request.reference_files = request.FILES['reference_files']
            quote_request.save()
        
        messages.success(request, f'Quote request {quote_request.quote_number} has been submitted.')
        return redirect('orders:quote_detail', quote_number=quote_request.quote_number)
    
    return render(request, 'orders/quote_request.html')


@login_required
def quote_detail(request, quote_number):
    """Quote detail page"""
    quote = get_object_or_404(
        QuoteRequest, 
        quote_number=quote_number, 
        user=request.user
    )
    
    context = {
        'quote': quote,
        'quote_items': quote.items.select_related('product'),
    }
    return render(request, 'orders/quote_detail.html', context)


@login_required
def quotes_list(request):
    """List all quote requests for user"""
    quotes = QuoteRequest.objects.filter(user=request.user).order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        quotes = quotes.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(quotes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'quotes': page_obj,
        'status_filter': status_filter,
        'quote_statuses': QuoteRequest.STATUS_CHOICES,
    }
    return render(request, 'orders/quotes_list.html', context)


# Cart count API for navbar
def cart_count_api(request):
    """Get cart count for navbar"""
    cart_manager = CartManager(request)
    return JsonResponse({
        'count': cart_manager.get_cart_count(),
        'total': str(cart_manager.get_cart_total())
    })