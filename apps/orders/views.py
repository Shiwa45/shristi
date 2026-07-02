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
from .models import Cart, CartItem, Order, OrderItem, QuoteRequest, Coupon
from .utils import CartManager
from apps.services.models import StaticProduct
import json


class CartView(View):
    """Shopping cart page"""
    
    def get(self, request):
        cart_manager = CartManager(request)
        cart = cart_manager.get_or_create_cart()
        
        context = {
            'cart': cart,
            'cart_items': cart.items.select_related('static_product', 'user_design'),
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
        'order_items': order.items.select_related('static_product'),
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


def _to_int(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _calculate_book_item_pricing(item):
    """Estimate pricing for a Book Printing quote item.

    Mirrors the per-page engine in book_printing_detail.html exactly, reading the
    editable rates from the BookPrintingPricing singleton:
      cost_per_book = interior(per-page) + size + paper + binding + cover finish
      subtotal      = cost_per_book * qty + cover-design + inner-page-design + ISBN
      then bulk discount (>=100: 10%, >=50: 5%), then 18% GST.
    """
    from decimal import Decimal
    from apps.services.models import BookPrintingPricing

    bp = BookPrintingPricing.load()
    specs = item.specifications or {}
    qty = item.quantity or 1

    page_count = _to_int(specs.get('page_count'))
    bw_pages = _to_int(specs.get('bw_page_count'))
    color_pages = _to_int(specs.get('color_page_count'))
    total_pages = page_count if page_count else (bw_pages + color_pages)

    components = []
    interior = specs.get('interior_color')
    interior_cost = Decimal('0')
    if interior == 'bw_standard':
        pages = bw_pages if bw_pages > 0 else total_pages
        interior_cost = pages * bp.color_bw_standard_per_page
        components.append({'label': f'Interior: B&W Standard — {pages} pg × ₹{bp.color_bw_standard_per_page}', 'amount': interior_cost})
    elif interior == 'bw_premium':
        pages = bw_pages if bw_pages > 0 else total_pages
        interior_cost = pages * bp.color_bw_premium_per_page
        components.append({'label': f'Interior: B&W Premium — {pages} pg × ₹{bp.color_bw_premium_per_page}', 'amount': interior_cost})
    elif interior == 'color_standard':
        pages = color_pages if color_pages > 0 else total_pages
        interior_cost = pages * bp.color_standard_per_page
        components.append({'label': f'Interior: Colour Standard — {pages} pg × ₹{bp.color_standard_per_page}', 'amount': interior_cost})
    elif interior == 'color_premium':
        pages = color_pages if color_pages > 0 else total_pages
        interior_cost = pages * bp.color_premium_per_page
        components.append({'label': f'Interior: Colour Premium — {pages} pg × ₹{bp.color_premium_per_page}', 'amount': interior_cost})
    elif interior == 'combine_color':
        interior_cost = (bw_pages * bp.combine_bw_per_page) + (color_pages * bp.combine_color_per_page)
        components.append({'label': f'Interior: Combined — {bw_pages} B&W + {color_pages} colour pg', 'amount': interior_cost})

    size_map = {'a4': bp.size_a4, 'letter': bp.size_letter, 'executive': bp.size_executive, 'a5': bp.size_a5}
    paper_map = {'75gsm': bp.paper_75gsm, '100gsm': bp.paper_100gsm, '100gsm_art': bp.paper_100gsm_art, '130gsm_art': bp.paper_130gsm_art}
    binding_map = {'saddle_stitch': bp.binding_saddle_stitch, 'spiral_binding': bp.binding_spiral, 'paperback_perfect': bp.binding_paperback_perfect, 'hardcover': bp.binding_hardcover}
    finish_map = {'matte': bp.cover_matte, 'glossy': bp.cover_glossy}

    def _add(label, mapping, key):
        val = mapping.get(key)
        if val is None:
            return Decimal('0')
        components.append({'label': label, 'amount': Decimal(val)})
        return Decimal(val)

    size_cost = _add(f"Size: {specs.get('book_size', '')}", size_map, specs.get('book_size'))
    paper_cost = _add(f"Paper: {specs.get('paper_type', '')}", paper_map, specs.get('paper_type'))
    binding_cost = _add(f"Binding: {specs.get('binding_type', '')}", binding_map, specs.get('binding_type'))
    finish_cost = _add(f"Cover finish: {specs.get('cover_finish', '')}", finish_map, specs.get('cover_finish'))

    cost_per_book = interior_cost + size_cost + paper_cost + binding_cost + finish_cost

    design_cost = Decimal('0')
    if specs.get('cover_page_design') == 'yes':
        design_cost += bp.cover_design_price
    if specs.get('inner_page_design') == 'yes':
        design_cost += total_pages * bp.inner_page_design_per_page
    isbn_cost = bp.isbn_price if specs.get('isbn_allocation') == 'assign_isbn' else Decimal('0')

    books_subtotal = cost_per_book * qty
    gross_subtotal = books_subtotal + design_cost + isbn_cost

    if qty >= 100:
        discount_pct = 10
    elif qty >= 50:
        discount_pct = 5
    else:
        discount_pct = 0
    discount = gross_subtotal * Decimal(discount_pct) / Decimal(100)
    after_discount = gross_subtotal - discount
    tax = after_discount * Decimal('0.18')
    total = after_discount + tax

    q = lambda d: Decimal(d).quantize(Decimal('0.01'))
    return {
        'is_book': True,
        'components': [{'label': c['label'], 'amount': q(c['amount'])} for c in components],
        'cost_per_book': q(cost_per_book),
        'quantity': qty,
        'books_subtotal': q(books_subtotal),
        'design_cost': q(design_cost),
        'isbn_cost': q(isbn_cost),
        'gross_subtotal': q(gross_subtotal),
        'discount': q(discount),
        'discount_pct': discount_pct,
        'subtotal': q(after_discount),   # taxable base — used for grand totals
        'tax': q(tax),
        'total': q(total),
    }


def _calculate_item_pricing(item):
    """Estimate pricing for a quote item.

    Book Printing products use the per-page engine (_calculate_book_item_pricing).
    All other products price off base price + the price modifiers of the selected
    spec options, mirroring recalc() on the product pages: unit = base + Σ(modifiers),
    total = unit * qty * 1.18. Returns None when there is no product to price against.
    """
    from decimal import Decimal

    product = item.static_product
    if not product:
        return None

    if product.category and product.category.slug == 'book-printing':
        return _calculate_book_item_pricing(item)

    base = Decimal(str(product.base_price or 0))
    specs = item.specifications or {}

    # Build a {field_name: {value: price_modifier}} lookup from the product's fields.
    modifier_lookup = {}
    for field in product.form_fields.filter(is_active=True):
        opt_map = {}
        for opt in field.get_options():
            try:
                opt_map[str(opt.get('value'))] = Decimal(str(opt.get('price_modifier', 0) or 0))
            except (TypeError, ValueError):
                opt_map[str(opt.get('value'))] = Decimal('0')
        modifier_lookup[field.field_name] = opt_map

    modifiers = []
    modifier_total = Decimal('0')
    for field_name, value in specs.items():
        opt_map = modifier_lookup.get(field_name)
        if not opt_map:
            continue
        mod = opt_map.get(str(value), Decimal('0'))
        if mod:
            modifiers.append({'label': str(value), 'amount': mod})
            modifier_total += mod

    qty = item.quantity or 1
    unit_price = base + modifier_total
    subtotal = unit_price * qty
    tax = (subtotal * Decimal('0.18')).quantize(Decimal('0.01'))
    total = (subtotal + tax).quantize(Decimal('0.01'))

    return {
        'base_price': base.quantize(Decimal('0.01')),
        'modifiers': modifiers,
        'unit_price': unit_price.quantize(Decimal('0.01')),
        'quantity': qty,
        'subtotal': subtotal.quantize(Decimal('0.01')),
        'tax': tax,
        'total': total,
    }


@login_required
def quote_detail(request, quote_number):
    """Quote detail page"""
    from decimal import Decimal

    quote = get_object_or_404(
        QuoteRequest,
        quote_number=quote_number,
        user=request.user
    )

    quote_items = quote.items.select_related(
        'static_product', 'static_product__category'
    ).prefetch_related('static_product__form_fields')

    priced_items = []
    grand_subtotal = Decimal('0')
    grand_tax = Decimal('0')
    grand_total = Decimal('0')
    for item in quote_items:
        pricing = _calculate_item_pricing(item)
        priced_items.append({'item': item, 'pricing': pricing})
        if pricing:
            grand_subtotal += pricing['subtotal']
            grand_tax += pricing['tax']
            grand_total += pricing['total']

    has_pricing = grand_total > 0

    context = {
        'quote': quote,
        'quote_items': quote_items,
        'priced_items': priced_items,
        'has_pricing': has_pricing,
        'estimated_subtotal': grand_subtotal.quantize(Decimal('0.01')),
        'estimated_tax': grand_tax.quantize(Decimal('0.01')),
        'estimated_total': grand_total.quantize(Decimal('0.01')),
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


def submit_quote_view(request):
    """Handle Get Quote submission from product pages."""
    import logging
    from django.urls import reverse
    logger = logging.getLogger(__name__)

    def _send_quote_email(quote):
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            first_item = quote.items.select_related('static_product').first()
            product_name = first_item.description if first_item else 'Custom Product'
            specs = first_item.specifications if first_item else {}
            specs_text = '\n'.join(
                f"  • {k.replace('_', ' ').title()}: {v}" for k, v in specs.items()
            ) if specs else '  No specifications provided'
            subject = f'Quote Request Received — {quote.quote_number} | Shristi Printing'
            message = (
                f"Dear {quote.customer_name},\n\n"
                f"Thank you for your quote request! We have received it and our team will review it shortly.\n\n"
                f"QUOTE DETAILS\n"
                f"{'='*44}\n"
                f"Quote Number  : {quote.quote_number}\n"
                f"Product       : {product_name}\n"
                f"Quantity      : {quote.quantity}\n"
                f"Status        : Pending Review\n\n"
                f"SPECIFICATIONS\n"
                f"{'='*44}\n"
                f"{specs_text}\n\n"
                f"WHAT HAPPENS NEXT?\n"
                f"{'='*44}\n"
                f"1. Our team will review your requirements (within 24 hours)\n"
                f"2. We will send you a detailed quotation with pricing\n"
                f"3. You can approve and proceed with the order\n\n"
                f"Need to reach us? Email: quotes@shirsti.com | Phone: +91 98765 43210\n"
                f"Business Hours: Mon–Sat, 9 AM – 6 PM\n\n"
                f"Thank you for choosing Shristi Printing!\n"
                f"— The Shristi Printing Team"
            )
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@shirsti.com'),
                recipient_list=[quote.customer_email],
                fail_silently=True,
            )
        except Exception as e:
            logger.warning('Quote email failed for %s: %s', quote.quote_number, e)

    def _create_quote(user, data):
        try:
            specs = json.loads(data.get('specs', '{}'))
        except (json.JSONDecodeError, TypeError):
            specs = {}

        product_name = data.get('product_name', 'Custom Product')
        quantity = max(int(data.get('quantity') or 1), 1)
        spec_lines = '\n'.join(f"{k}: {v}" for k, v in specs.items())
        description = f"Quote for {product_name}\n\nSpecifications:\n{spec_lines}"

        quote = QuoteRequest.objects.create(
            user=user,
            customer_name=(f"{user.first_name} {user.last_name}".strip() or user.email),
            customer_email=user.email,
            customer_phone=user.phone or '',
            company_name=getattr(user, 'company_name', '') or '',
            description=description,
            quantity=quantity,
        )

        try:
            product = StaticProduct.objects.get(id=data.get('product_id'))
        except (StaticProduct.DoesNotExist, TypeError, ValueError):
            product = None

        from .models import QuoteRequestItem
        QuoteRequestItem.objects.create(
            quote_request=quote,
            static_product=product,
            description=product_name,
            quantity=quantity,
            specifications=specs,
        )

        _send_quote_email(quote)
        return quote

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        if not request.user.is_authenticated:
            request.session['pending_quote'] = {
                'product_id': request.POST.get('product_id'),
                'product_name': request.POST.get('product_name', ''),
                'quantity': request.POST.get('quantity', '1'),
                'specs': request.POST.get('specs', '{}'),
            }
            if is_ajax:
                return JsonResponse({'require_login': True})
            register_url = reverse('accounts:register')
            submit_url = reverse('orders:submit_quote')
            return redirect(f"{register_url}?next={submit_url}")

        quote = _create_quote(request.user, request.POST)
        quote_url = reverse('orders:quote_detail', kwargs={'quote_number': quote.quote_number})
        if is_ajax:
            return JsonResponse({
                'success': True,
                'quote_number': quote.quote_number,
                'redirect_url': quote_url,
            })
        messages.success(request, f'Quote {quote.quote_number} submitted! Our team will contact you soon.')
        return redirect(quote_url)

    # GET — user returned after login/register
    if request.user.is_authenticated:
        pending = request.session.pop('pending_quote', None)
        if pending:
            quote = _create_quote(request.user, pending)
            messages.success(request, f'Quote {quote.quote_number} submitted! Our team will contact you soon.')
            return redirect('orders:quote_detail', quote_number=quote.quote_number)

    return redirect('accounts:profile')


# Cart count API for navbar
def cart_count_api(request):
    """Get cart count for navbar"""
    cart_manager = CartManager(request)
    return JsonResponse({
        'count': cart_manager.get_cart_count(),
        'total': str(cart_manager.get_cart_total())
    })


# ENHANCED CART VIEWS FOR STATIC PRODUCTS (Phase 3)

@csrf_exempt
@require_http_methods(["POST"])
def add_static_product_to_cart(request, product_id):
    """Add static product to cart with optional design studio data"""
    try:
        data = json.loads(request.body)

        static_product = get_object_or_404(StaticProduct, id=product_id, is_active=True)

        min_qty = getattr(static_product, 'minimum_quantity', None) or 1
        quantity = max(int(data.get('quantity', min_qty)), min_qty)
        specifications = data.get('specifications', {})
        design_data = data.get('design_data')  # Fabric.js canvas JSON from studio

        cart = get_or_create_cart(request)

        # When design_data is provided (from studio), replace the existing cart item
        # outright so the latest design is always what the customer sees.
        if design_data:
            existing_item = CartItem.objects.filter(
                cart=cart,
                static_product=static_product,
                user_design=None,
            ).first()
            if existing_item:
                existing_item.quantity = quantity
                existing_item.specifications = specifications
                existing_item.design_data = design_data
                existing_item.save()
                cart_item = existing_item
            else:
                cart_item = CartItem.objects.create(
                    cart=cart,
                    static_product=static_product,
                    quantity=quantity,
                    unit_price=static_product.base_price,
                    specifications=specifications,
                    design_data=design_data,
                )
        else:
            # No design — classic add-to-cart (increment if product already in cart)
            existing_item = CartItem.objects.filter(
                cart=cart,
                static_product=static_product,
                user_design=None,
            ).first()
            if existing_item:
                existing_item.quantity += quantity
                existing_item.specifications.update(specifications)
                existing_item.save()
                cart_item = existing_item
            else:
                cart_item = CartItem.objects.create(
                    cart=cart,
                    static_product=static_product,
                    quantity=quantity,
                    unit_price=static_product.base_price,
                    specifications=specifications,
                )

        from django.urls import reverse
        return JsonResponse({
            'success': True,
            'message': f'{static_product.name} added to cart',
            'cart_item_id': cart_item.id,
            'cart_count': cart.total_items,
            'cart_total': str(cart.subtotal),
            'item_total': str(cart_item.total_price),
            # Absolute URL so the design studio (different origin) can navigate directly to Django
            'cart_url': request.build_absolute_uri(reverse('orders:cart')),
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error adding to cart: {str(e)}'
        }, status=500)


@require_http_methods(["POST"])
def update_cart_item_ajax(request, item_id):
    """Update cart item quantity via AJAX"""
    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))

        # Get cart item
        cart_item = get_object_or_404(CartItem, id=item_id)

        # Validate cart ownership
        cart = get_or_create_cart(request)
        if cart_item.cart != cart:
            return JsonResponse({
                'success': False,
                'message': 'Cart item not found'
            }, status=404)

        # Validate quantity
        if hasattr(cart_item, 'static_product') and cart_item.static_product:
            min_qty = cart_item.static_product.minimum_quantity
            if quantity < min_qty:
                return JsonResponse({
                    'success': False,
                    'message': f'Minimum quantity is {min_qty}'
                }, status=400)

        # Update quantity
        cart_item.quantity = quantity
        cart_item.save()

        # Recalculate pricing if needed
        if hasattr(cart_item.static_product, 'get_pricing'):
            pricing_info = cart_item.static_product.get_pricing(quantity, cart_item.specifications)
            cart_item.unit_price = pricing_info.get('unit_price', cart_item.static_product.base_price)
            cart_item.save()

        return JsonResponse({
            'success': True,
            'message': 'Cart updated',
            'cart_count': cart.total_items,
            'cart_total': str(cart.subtotal),
            'item_total': str(cart_item.total_price),
            'unit_price': str(cart_item.unit_price)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating cart: {str(e)}'
        }, status=500)


@require_http_methods(["POST"])
def remove_cart_item_ajax(request, item_id):
    """Remove cart item via AJAX"""
    try:
        # Get cart item
        cart_item = get_object_or_404(CartItem, id=item_id)

        # Validate cart ownership
        cart = get_or_create_cart(request)
        if cart_item.cart != cart:
            return JsonResponse({
                'success': False,
                'message': 'Cart item not found'
            }, status=404)

        # Remove item
        product_name = cart_item.static_product.name if cart_item.static_product else 'Item'
        cart_item.delete()

        return JsonResponse({
            'success': True,
            'message': f'{product_name} removed from cart',
            'cart_count': cart.total_items,
            'cart_total': str(cart.subtotal)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error removing item: {str(e)}'
        }, status=500)


@require_http_methods(["POST"])
def apply_coupon_ajax(request):
    """Apply coupon to cart via AJAX"""
    try:
        data = json.loads(request.body)
        coupon_code = data.get('coupon_code', '').strip().upper()

        if not coupon_code:
            return JsonResponse({
                'success': False,
                'message': 'Please enter a coupon code'
            }, status=400)

        # Get cart
        cart = get_or_create_cart(request)
        if cart.total_items == 0:
            return JsonResponse({
                'success': False,
                'message': 'Your cart is empty'
            }, status=400)

        # Check if coupon exists and is valid
        try:
            coupon = Coupon.objects.get(code=coupon_code, is_active=True)
        except Coupon.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid coupon code'
            }, status=400)

        if not coupon.is_valid:
            return JsonResponse({
                'success': False,
                'message': 'This coupon has expired or reached its usage limit'
            }, status=400)

        # Check minimum amount
        if cart.subtotal < coupon.minimum_amount:
            return JsonResponse({
                'success': False,
                'message': f'Minimum order amount for this coupon is ₹{coupon.minimum_amount}'
            }, status=400)

        # Calculate discount
        discount_amount = coupon.apply_discount(cart.subtotal)

        return JsonResponse({
            'success': True,
            'message': f'Coupon "{coupon_code}" applied successfully',
            'discount_amount': str(discount_amount),
            'cart_total': str(cart.subtotal),
            'final_total': str(cart.subtotal - discount_amount),
            'coupon_description': coupon.description
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error applying coupon: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def cart_summary_ajax(request):
    """Get cart summary for quick view"""
    try:
        cart = get_or_create_cart(request)
        cart_items = cart.items.select_related('static_product', 'user_design')

        items_data = []
        for item in cart_items:
            items_data.append({
                'id': item.id,
                'product_name': item.static_product.name if item.static_product else 'Unknown Product',
                'quantity': item.quantity,
                'unit_price': str(item.unit_price),
                'total_price': str(item.total_price),
                'has_design': bool(item.user_design),
                'design_name': item.user_design.name if item.user_design else None,
                'thumbnail': item.user_design.preview_image.url if item.user_design and item.user_design.preview_image else None
            })

        return JsonResponse({
            'success': True,
            'cart_count': cart.total_items,
            'cart_total': str(cart.subtotal),
            'items': items_data
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error loading cart: {str(e)}'
        }, status=500)


# Helper function
def get_or_create_cart(request):
    """Get or create cart for user/session"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        # For anonymous users, use session
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)

    return cart


# QUOTE GENERATION SYSTEM (Phase 3)

@require_http_methods(["POST"])
def generate_quote_from_cart(request):
    """Generate professional quote from current cart"""
    try:
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'message': 'Please log in to generate a quote'
            }, status=401)

        data = json.loads(request.body)
        customer_notes = data.get('customer_notes', '')

        # Get cart
        cart = get_or_create_cart(request)
        if cart.total_items == 0:
            return JsonResponse({
                'success': False,
                'message': 'Your cart is empty'
            }, status=400)

        # Calculate quote validity (30 days from now)
        from datetime import datetime, timedelta
        from django.utils import timezone
        valid_until = timezone.now() + timedelta(days=30)

        # Create quote
        quote = Quote.objects.create(
            user=request.user,
            cart_snapshot=serialize_cart_snapshot(cart),
            subtotal=cart.subtotal,
            tax_amount=cart.subtotal * 0.18,  # 18% GST
            shipping_cost=0,  # Free shipping for quotes
            discount_amount=0,
            total_amount=cart.subtotal * 1.18,
            valid_until=valid_until,
            customer_notes=customer_notes
        )

        return JsonResponse({
            'success': True,
            'message': 'Quote generated successfully',
            'quote_number': quote.quote_number,
            'quote_id': quote.id,
            'valid_until': quote.valid_until.isoformat(),
            'total_amount': str(quote.total_amount)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error generating quote: {str(e)}'
        }, status=500)


@login_required
def quote_detail_view(request, quote_number):
    """View quote details"""
    quote = get_object_or_404(Quote, quote_number=quote_number, user=request.user)

    # Mark as viewed if not already
    if quote.status == 'draft':
        quote.status = 'sent'
        quote.sent_at = timezone.now()
        quote.save()

    if quote.status == 'sent' and not quote.viewed_at:
        quote.viewed_at = timezone.now()
        quote.status = 'viewed'
        quote.save()

    context = {
        'quote': quote,
        'cart_items': quote.cart_snapshot.get('items', []),
        'can_accept': quote.can_accept,
        'is_valid': quote.is_valid
    }

    return render(request, 'orders/quote_detail.html', context)


@require_http_methods(["POST"])
def accept_quote(request, quote_number):
    """Accept a quote and convert to order"""
    try:
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'message': 'Please log in to accept quote'
            }, status=401)

        quote = get_object_or_404(Quote, quote_number=quote_number, user=request.user)

        if not quote.can_accept:
            return JsonResponse({
                'success': False,
                'message': 'This quote cannot be accepted'
            }, status=400)

        # Update quote status
        quote.status = 'accepted'
        quote.responded_at = timezone.now()
        quote.save()

        # Create order from quote
        order = Order.objects.create(
            user=request.user,
            status='pending',
            customer_name=request.user.get_full_name() or request.user.username,
            customer_email=request.user.email,
            subtotal=quote.subtotal,
            tax_amount=quote.tax_amount,
            shipping_cost=quote.shipping_cost,
            total_amount=quote.total_amount
        )

        # Create order items from quote snapshot
        for item_data in quote.cart_snapshot.get('items', []):
            OrderItem.objects.create(
                order=order,
                static_product_id=item_data.get('product_id'),
                product_name=item_data.get('product_name'),
                quantity=item_data.get('quantity'),
                unit_price=item_data.get('unit_price'),
                total_price=item_data.get('total_price'),
                specifications=item_data.get('specifications', {}),
                user_design_id=item_data.get('design_id')
            )

        return JsonResponse({
            'success': True,
            'message': 'Quote accepted successfully',
            'order_number': order.order_number,
            'redirect_url': f'/orders/order/{order.order_number}/'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error accepting quote: {str(e)}'
        }, status=500)


@require_http_methods(["POST"])
def submit_book_printing_order(request, product_id):
    """Submit book printing order with category-specific form data"""
    try:
        data = json.loads(request.body)
        
        # Get the static product
        static_product = get_object_or_404(StaticProduct, id=product_id, is_active=True)
        
        # Validate that this is a book printing product
        if not static_product.category or static_product.category.slug != 'book-printing':
            return JsonResponse({
                'success': False,
                'message': 'This endpoint is only for book printing products'
            }, status=400)
        
        # Extract form data
        form_data = data.get('form_data', {})
        customer_info = data.get('customer_info', {})
        
        # Validate required fields
        required_fields = ['interior_color', 'book_size', 'page_count', 'paper_type', 'binding_type', 'cover_finish']
        missing_fields = [field for field in required_fields if not form_data.get(field)]
        
        if missing_fields:
            return JsonResponse({
                'success': False,
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }, status=400)
        
        # Calculate quantity (minimum 25 for book printing)
        quantity = max(int(form_data.get('quantity', 25)), 25)
        
        # Calculate pricing based on specifications
        unit_price = calculate_book_printing_price(static_product, form_data)
        total_price = unit_price * quantity
        
        # Create specifications object
        specifications = {
            'interior_color': form_data.get('interior_color'),
            'book_size': form_data.get('book_size'),
            'page_count': form_data.get('page_count'),
            'bw_page_count': form_data.get('bw_page_count'),
            'color_page_count': form_data.get('color_page_count'),
            'paper_type': form_data.get('paper_type'),
            'binding_type': form_data.get('binding_type'),
            'cover_finish': form_data.get('cover_finish'),
            'design_service': form_data.get('design_service'),
            'isbn_allocation': form_data.get('isbn_allocation'),
            'special_instructions': form_data.get('special_instructions', ''),
        }
        
        # Handle file uploads if present
        uploaded_files = {}
        if 'cover_page_file' in request.FILES:
            uploaded_files['cover_page'] = request.FILES['cover_page_file']
        if 'inner_pages_file' in request.FILES:
            uploaded_files['inner_pages'] = request.FILES['inner_pages_file']
        
        # Add to cart (for authenticated users) or quote request (for anonymous)
        if request.user.is_authenticated:
            # Get or create cart
            cart = get_or_create_cart(request)
            
            # Check if similar item already exists in cart
            existing_item = CartItem.objects.filter(
                cart=cart,
                static_product=static_product
            ).first()
            
            if existing_item:
                # Update existing item
                existing_item.quantity += quantity
                existing_item.specifications.update(specifications)
                existing_item.save()
            else:
                # Create new cart item
                CartItem.objects.create(
                    cart=cart,
                    static_product=static_product,
                    quantity=quantity,
                    unit_price=unit_price,
                    specifications=specifications
                )
            
            return JsonResponse({
                'success': True,
                'message': 'Book added to cart successfully!',
                'redirect_url': '/orders/checkout/'
            })
        
        else:
            # Create quote request for anonymous users
            quote_request = QuoteRequest.objects.create(
                user=None,  # Anonymous
                customer_name=customer_info.get('name', 'Anonymous Customer'),
                customer_email=customer_info.get('email', ''),
                customer_phone=customer_info.get('phone', ''),
                description=f"Book Printing Order: {static_product.name}",
                requirements=json.dumps(specifications, indent=2),
                quantity=quantity,
                quoted_amount=total_price * 1.18
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Quote request submitted successfully! We will contact you shortly.',
                'quote_number': quote_request.quote_number,
                'estimated_total': str(total_price * 1.18)
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error submitting order: {str(e)}'
        }, status=500)


def calculate_book_printing_price(product, form_data):
    """Calculate book printing price based on specifications"""
    base_price = float(product.base_price)
    
    # Interior color modifiers
    color_modifiers = {
        'bw_standard': -50,
        'bw_premium': 0,
        'color_standard': 200,
        'color_premium': 300,
        'combine_color': 0  # Will be calculated separately
    }
    
    interior_color = form_data.get('interior_color')
    if interior_color in color_modifiers:
        base_price += color_modifiers[interior_color]
    
    # Handle combine color pricing
    if interior_color == 'combine_color':
        bw_pages = int(form_data.get('bw_page_count', 0))
        color_pages = int(form_data.get('color_page_count', 0))
        # Add pricing based on page counts
        base_price += (bw_pages * 2) + (color_pages * 8)  # Example pricing
    else:
        page_count = int(form_data.get('page_count', 4))
        # Add pricing based on total page count
        if interior_color in ['color_standard', 'color_premium']:
            base_price += page_count * 6  # Color page pricing
        else:
            base_price += page_count * 2  # B&W page pricing
    
    # Book size modifiers
    size_modifiers = {
        'a4': 0,
        'letter': 25,
        'executive': 50,
        'a5': -25
    }
    
    book_size = form_data.get('book_size')
    if book_size in size_modifiers:
        base_price += size_modifiers[book_size]
    
    # Paper type modifiers
    paper_modifiers = {
        '75gsm': 0,
        '100gsm': 50,
        '100gsm_art': 100,
        '130gsm_art': 150
    }
    
    paper_type = form_data.get('paper_type')
    if paper_type in paper_modifiers:
        base_price += paper_modifiers[paper_type]
    
    # Binding type modifiers
    binding_modifiers = {
        'saddle_stitch': 0,
        'spiral_binding': 50,
        'paperback_perfect': 100,
        'hardcover': 300
    }
    
    binding_type = form_data.get('binding_type')
    if binding_type in binding_modifiers:
        base_price += binding_modifiers[binding_type]
    
    # Cover finish modifiers
    finish_modifiers = {
        'matte': 0,
        'glossy': 25
    }
    
    cover_finish = form_data.get('cover_finish')
    if cover_finish in finish_modifiers:
        base_price += finish_modifiers[cover_finish]
    
    # Design service
    if form_data.get('design_service') == 'yes_design':
        base_price += 1500  # Rs. 1500 for design service
    
    # ISBN allocation
    if form_data.get('isbn_allocation') == 'assign_isbn':
        base_price += 500  # Rs. 500 for ISBN
    
    return max(base_price, 50)  # Minimum price of Rs. 50


@require_http_methods(["GET"])
def download_quote_pdf(request, quote_number):
    """Download quote as PDF"""
    from django.http import HttpResponse
    from django.template.loader import get_template
    import io

    try:
        # Try to import reportlab for PDF generation
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.units import inch
    except ImportError:
        # Fallback to HTML if reportlab not available
        return render(request, 'orders/quote_pdf_fallback.html', {
            'quote': get_object_or_404(Quote, quote_number=quote_number, user=request.user)
        })

    quote = get_object_or_404(Quote, quote_number=quote_number, user=request.user)

    # Create PDF buffer
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    # Build PDF content
    story = []

    # Header
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.darkblue
    )
    story.append(Paragraph("SHIRSTI PRINTING - QUOTE", title_style))
    story.append(Spacer(1, 12))

    # Quote info
    info_data = [
        ['Quote Number:', quote.quote_number],
        ['Date:', quote.created_at.strftime('%B %d, %Y')],
        ['Valid Until:', quote.valid_until.strftime('%B %d, %Y')],
        ['Customer:', quote.user.get_full_name() or quote.user.username],
        ['Email:', quote.user.email]
    ]

    info_table = Table(info_data, colWidths=[2*inch, 3*inch])
    info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 20))

    # Items table
    story.append(Paragraph("ITEMS", styles['Heading2']))
    story.append(Spacer(1, 12))

    items_data = [['Product', 'Quantity', 'Unit Price', 'Total']]
    for item in quote.cart_snapshot.get('items', []):
        items_data.append([
            item.get('product_name', 'Unknown'),
            str(item.get('quantity', 0)),
            f"₹{item.get('unit_price', 0)}",
            f"₹{item.get('total_price', 0)}"
        ])

    items_table = Table(items_data, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(items_table)
    story.append(Spacer(1, 20))

    # Totals
    totals_data = [
        ['Subtotal:', f"₹{quote.subtotal}"],
        ['Tax (18% GST):', f"₹{quote.tax_amount}"],
        ['Shipping:', f"₹{quote.shipping_cost}"],
        ['TOTAL:', f"₹{quote.total_amount}"]
    ]

    totals_table = Table(totals_data, colWidths=[2*inch, 2*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 14),
        ('LINEBELOW', (0, -2), (-1, -2), 1, colors.black),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 30))

    # Footer
    footer_text = """
    <para align="center">
    <b>Terms & Conditions</b><br/>
    • This quote is valid for 30 days from the date of issue<br/>
    • All prices include design and setup charges<br/>
    • 50% advance payment required to start production<br/>
    • Delivery time: 3-5 business days after design approval<br/><br/>

    <b>Contact Us</b><br/>
    Email: orders@shirsti.com | Phone: +91-XXXXX-XXXXX<br/>
    Website: www.shirsti.com
    </para>
    """
    story.append(Paragraph(footer_text, styles['Normal']))

    # Build PDF
    doc.build(story)

    # Return response
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="quote_{quote.quote_number}.pdf"'

    return response


def serialize_cart_snapshot(cart):
    """Serialize cart data for quote storage"""
    cart_items = cart.items.select_related('static_product', 'user_design')

    items_data = []
    for item in cart_items:
        item_data = {
            'product_id': item.static_product.id if item.static_product else None,
            'product_name': item.static_product.name if item.static_product else 'Unknown Product',
            'quantity': item.quantity,
            'unit_price': str(item.unit_price),
            'total_price': str(item.total_price),
            'specifications': item.specifications,
            'design_id': item.user_design.id if item.user_design else None,
            'design_name': item.user_design.name if item.user_design else None,
            'design_thumbnail': item.user_design.preview_image.url if item.user_design and item.user_design.preview_image else None
        }
        items_data.append(item_data)

    return {
        'items': items_data,
        'total_items': cart.total_items,
        'subtotal': str(cart.subtotal),
        'generated_at': timezone.now().isoformat()
    }