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
from apps.services.models import StaticProduct
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


# ENHANCED CART VIEWS FOR STATIC PRODUCTS (Phase 3)

@require_http_methods(["POST"])
def add_static_product_to_cart(request, product_id):
    """Add static product to cart with design integration"""
    try:
        data = json.loads(request.body)

        # Get the static product
        static_product = get_object_or_404(StaticProduct, id=product_id, is_active=True)

        # Extract cart data
        quantity = int(data.get('quantity', static_product.minimum_quantity))
        specifications = data.get('specifications', {})
        design_id = data.get('design_id')

        # Validate quantity
        if quantity < static_product.minimum_quantity:
            return JsonResponse({
                'success': False,
                'message': f'Minimum quantity is {static_product.minimum_quantity}'
            }, status=400)

        # Get or create cart
        cart = get_or_create_cart(request)

        # Get user design if provided
        user_design = None
        if design_id and request.user.is_authenticated:
            from apps.templates_mgmt.models import UserDesign
            try:
                user_design = UserDesign.objects.get(
                    id=design_id,
                    user=request.user,
                    static_product=static_product
                )
            except UserDesign.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Design not found'
                }, status=400)

        # Check if item already exists in cart
        existing_item = CartItem.objects.filter(
            cart=cart,
            static_product=static_product,
            user_design=user_design
        ).first()

        if existing_item:
            # Update existing item
            existing_item.quantity += quantity
            existing_item.specifications.update(specifications)
            existing_item.save()
            cart_item = existing_item
        else:
            # Create new cart item
            cart_item = CartItem.objects.create(
                cart=cart,
                static_product=static_product,
                user_design=user_design,
                quantity=quantity,
                unit_price=static_product.base_price,
                specifications=specifications
            )

        # Calculate pricing if needed
        if hasattr(static_product, 'get_pricing'):
            pricing_info = static_product.get_pricing(quantity, specifications)
            cart_item.unit_price = pricing_info.get('unit_price', static_product.base_price)
            cart_item.save()

        return JsonResponse({
            'success': True,
            'message': f'{static_product.name} added to cart',
            'cart_item_id': cart_item.id,
            'cart_count': cart.total_items,
            'cart_total': str(cart.subtotal),
            'item_total': str(cart_item.total_price)
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