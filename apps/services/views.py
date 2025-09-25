# apps/services/views.py - Complete Updated Version

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Min, Max, Avg, Count
from django.core.paginator import Paginator
from django.views.generic import ListView, DetailView
from django.utils.decorators import method_decorator
import json
from decimal import Decimal

from .models import (
    ServiceCategory, Product, ProductPricing, ProductImage,
    ProductSpecification, ProductFeature, ProductProcess,
    ProductFAQ, ProductTestimonial, ProductSample, ShippingOption
)


def service_categories_view(request):
    """Display all service categories"""
    categories = ServiceCategory.objects.filter(is_active=True).prefetch_related('products')
    
    # Get featured products
    featured_products = Product.objects.filter(is_featured=True, is_active=True)[:8]
    
    context = {
        'categories': categories,
        'featured_products': featured_products,
        'page_title': 'Our Services'
    }
    return render(request, 'services/categories.html', context)


def category_products_view(request, slug):
    """Display products in a specific category with filtering and pagination"""
    category = get_object_or_404(ServiceCategory, slug=slug, is_active=True)
    products = Product.objects.filter(
        category=category, 
        is_active=True
    ).select_related('category').prefetch_related('images', 'pricings')
    
    # Filtering
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    has_design_tool = request.GET.get('design_tool')
    sort_by = request.GET.get('sort', 'name')
    
    if price_min:
        products = products.filter(price_per_unit__gte=price_min)
    if price_max:
        products = products.filter(price_per_unit__lte=price_max)
    if has_design_tool:
        products = products.filter(has_design_tool=True)
    
    # Sorting
    if sort_by == 'price_low':
        products = products.order_by('price_per_unit')
    elif sort_by == 'price_high':
        products = products.order_by('-price_per_unit')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('order', 'name')
    
    # Pagination
    paginator = Paginator(products, 12)  # 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'products': page_obj,
        'page_obj': page_obj,
        'page_title': f'{category.name} Services'
    }
    return render(request, 'services/category.html', context)


def product_detail_view(request, slug):
    """Enhanced product detail view with all related data"""
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related(
            'images', 'pricings', 'specifications', 'features',
            'processes', 'faqs', 'testimonials', 'samples'
        ),
        slug=slug,
        is_active=True
    )
    
    # Get available options from pricing
    available_sizes = product.pricings.filter(
        is_active=True
    ).values_list('size', flat=True).distinct()
    
    available_paper_types = product.pricings.filter(
        is_active=True
    ).values_list('paper_type', flat=True).distinct()
    
    available_finishes = product.pricings.filter(
        is_active=True
    ).values_list('finish', flat=True).distinct()
    
    # Get quantity ranges
    quantity_range = product.pricings.filter(is_active=True).aggregate(
        min_qty=Min('min_quantity'),
        max_qty=Max('max_quantity')
    )
    
    # Get related products
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id).prefetch_related('images')[:4]
    
    # Get shipping options
    shipping_options = ShippingOption.objects.all()
    
    # Calculate average rating from testimonials
    avg_rating = product.testimonials.aggregate(
        avg=Avg('rating'),
        count=Count('id')
    )
    
    # Check if user has this item in cart
    in_cart = False
    if request.user.is_authenticated:
        try:
            from apps.orders.models import Cart
            cart = Cart.objects.get(user=request.user)
            in_cart = cart.items.filter(product=product).exists()
        except Cart.DoesNotExist:
            pass
    
    context = {
        'product': product,
        'available_sizes': list(available_sizes),
        'available_paper_types': list(available_paper_types),
        'available_finishes': list(available_finishes),
        'quantity_range': quantity_range,
        'related_products': related_products,
        'shipping_options': shipping_options,
        'avg_rating': avg_rating['avg'] or 4.5,  # Default rating
        'review_count': avg_rating['count'] or 0,
        'in_cart': in_cart,
    }
    
    return render(request, 'services/product_detail.html', context)


def product_search(request):
    """Search products across all categories"""
    query = request.GET.get('q', '')
    category_slug = request.GET.get('category')
    
    products = Product.objects.filter(is_active=True)
    
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(keywords__icontains=query)
        )
    
    if category_slug:
        products = products.filter(category__slug=category_slug)
    
    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'query': query,
        'page_obj': page_obj,
        'page_title': f'Search Results for "{query}"' if query else 'All Products'
    }
    return render(request, 'services/search.html', context)


@require_http_methods(["GET"])
def api_product_pricing(request, product_id):
    """API endpoint for dynamic pricing calculation"""
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Get parameters
        quantity = int(request.GET.get('quantity', 1))
        size = request.GET.get('size', '')
        paper_type = request.GET.get('paper_type', '')
        finish = request.GET.get('finish', '')
        binding_type = request.GET.get('binding_type', '')
        colors = request.GET.get('colors', '')
        rush_order = request.GET.get('rush', 'false').lower() == 'true'
        
        # Build query: require exact match on all selected options
        query = Q(product=product, is_active=True)
        query &= Q(min_quantity__lte=quantity)
        query &= (Q(max_quantity__gte=quantity) | Q(max_quantity__isnull=True))
        if size:
            query &= Q(size=size)
        if paper_type:
            query &= Q(paper_type=paper_type)
        if finish:
            query &= Q(finish=finish)
        if binding_type:
            query &= Q(binding_type=binding_type)
        if colors:
            query &= Q(colors=colors)
        # Add more strict matching for other options if needed
        # (e.g., print_sides, cover_finish, etc.)
        # Get the best matching pricing (require all selected fields to match)
        pricing = ProductPricing.objects.filter(query).order_by('price_per_unit').first()
        
        if pricing:
            calculation = pricing.calculate_total_price(quantity, rush_order)

            # Add additional service costs
            additional_costs = 0
            design_service = request.GET.get('design_service', 'false').lower() == 'true'
            isbn_allocation = request.GET.get('isbn_allocation', 'false').lower() == 'true'

            if design_service:
                additional_costs += 1500
            if isbn_allocation:
                additional_costs += 500

            final_total = calculation['total_price'] + additional_costs

            return JsonResponse({
                'success': True,
                'unit_price': float(calculation['unit_price']),
                'subtotal': float(calculation['subtotal']),
                'setup_cost': float(calculation['setup_cost']),
                'price': float(final_total),
                'base_price': float(pricing.price_per_unit) * quantity,
                'savings': float(calculation['savings']),
                'volume_discount': float(pricing.volume_discount_percentage),
                'turnaround_days': calculation['turnaround_days'],
                'additional_costs': additional_costs,
                'design_service_cost': 1500 if design_service else 0,
                'isbn_cost': 500 if isbn_allocation else 0,
                'currency': 'INR',
                'quantity': quantity,
                'pricing_tier': pricing.min_quantity
            })
        else:
            # Fallback to base product pricing
            unit_price = float(product.price_per_unit)
            if rush_order and product.express_production:
                unit_price *= 1.5

            subtotal = unit_price * quantity

            # Add additional service costs
            additional_costs = 0
            design_service = request.GET.get('design_service', 'false').lower() == 'true'
            isbn_allocation = request.GET.get('isbn_allocation', 'false').lower() == 'true'

            if design_service:
                additional_costs += 1500
            if isbn_allocation:
                additional_costs += 500

            total = subtotal + additional_costs

            return JsonResponse({
                'success': True,
                'unit_price': unit_price,
                'subtotal': subtotal,
                'setup_cost': 0,
                'price': total,
                'base_price': float(product.price_per_unit) * quantity,
                'savings': 0,
                'volume_discount': 0,
                'turnaround_days': 3 if rush_order else 5,
                'additional_costs': additional_costs,
                'design_service_cost': 1500 if design_service else 0,
                'isbn_cost': 500 if isbn_allocation else 0,
                'currency': 'INR',
                'quantity': quantity
            })
            
    except (ValueError, TypeError) as e:
        return JsonResponse({
            'success': False,
            'error': f'Invalid parameters: {str(e)}'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while calculating pricing'
        }, status=500)


@require_http_methods(["GET"])
def api_product_options(request, product_id):
    """Get available options for a product"""
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Get all unique options
        pricings = product.pricings.filter(is_active=True)
        
        options = {
            'sizes': list(pricings.values_list('size', flat=True).distinct().exclude(size='')),
            'paper_types': list(pricings.values_list('paper_type', flat=True).distinct().exclude(paper_type='')),
            'finishes': list(pricings.values_list('finish', flat=True).distinct().exclude(finish='')),
            'binding_types': list(pricings.values_list('binding_type', flat=True).distinct().exclude(binding_type='')),
            'colors': list(pricings.values_list('colors', flat=True).distinct().exclude(colors='')),
        }
        
        # Remove empty options
        options = {k: v for k, v in options.items() if v}
        
        return JsonResponse({
            'success': True,
            'options': options,
            'minimum_quantity': product.minimum_quantity,
            'express_available': product.express_production_available
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def api_bulk_pricing(request, product_id):
    """Get bulk pricing tiers for a product"""
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Get pricing tiers
        pricings = product.pricings.filter(is_active=True).order_by('min_quantity')
        
        tiers = []
        for pricing in pricings:
            tiers.append({
                'min_quantity': pricing.min_quantity,
                'max_quantity': pricing.max_quantity,
                'unit_price': float(pricing.price_per_unit),
                'setup_cost': float(pricing.setup_cost),
                'discount': float(pricing.volume_discount_percentage),
                'turnaround_days': pricing.turnaround_days
            })
        
        return JsonResponse({
            'success': True,
            'tiers': tiers,
            'currency': 'INR'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_POST
@csrf_protect
def api_quote_request(request):
    """Handle quote request submission"""
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        
        # Create quote request (you'll need a QuoteRequest model)
        product_id = data.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        
        quote_data = {
            'product': product,
            'quantity': data.get('quantity'),
            'specifications': {
                'size': data.get('size'),
                'paper_type': data.get('paper_type'),
                'finish': data.get('finish'),
                'binding_type': data.get('binding_type'),
                'colors': data.get('colors'),
                'corner_type': data.get('corner_type', 'rounded'),
                'selected_options': json.dumps(data.get('selected_options', {}))
            },
            'customer_info': {
                'name': data.get('name'),
                'email': data.get('email'),
                'phone': data.get('phone'),
                'company': data.get('company'),
                'requirements': data.get('requirements')
            }
        }
        
        # Here you would save to database and send email
        # For now, just return success
        
        return JsonResponse({
            'success': True,
            'message': 'Quote request submitted successfully',
            'quote_id': f'QT{uuid.uuid4().hex[:8].upper()}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# New views for the enhanced product detail page
def get_paper_options(request, product_id):
    """Get available paper options with images and descriptions"""
    product = get_object_or_404(Product, id=product_id)
    
    paper_options = []
    pricings = product.pricings.filter(is_active=True).values('paper_type').distinct()
    
    # Define paper types with their properties
    paper_types_info = {
        '75gsm Standard': {
            'name': 'Black & White Standard',
            'description': 'High-quality black and white printing on standard paper',
            'specs': ['75gsm', 'B&W', 'Standard'],
            'price_addon': 0,
            'image_class': 'paper-bw-standard',
            'icon': '📄'
        },
        '100gsm Premium': {
            'name': 'Black & White Premium', 
            'description': 'Premium black and white printing with enhanced clarity',
            'specs': ['100gsm', 'B&W', 'Premium'],
            'price_addon': 5,
            'image_class': 'paper-bw-premium',
            'icon': '📋'
        },
        '130gsm Art Paper': {
            'name': 'Color Premium',
            'description': 'Full-color printing with vibrant colors and premium finish',
            'specs': ['130gsm', 'Full Color', 'Art Paper'],
            'price_addon': 15,
            'image_class': 'paper-color-premium',
            'icon': '🎨'
        },
        '300gsm Cardstock': {
            'name': 'Standard Cardstock',
            'description': 'High-quality standard cardstock perfect for everyday use',
            'specs': ['300gsm', 'Matte', 'Standard'],
            'price_addon': 0,
            'image_class': 'paper-bw-standard',
            'icon': '📄'
        },
        '350gsm Cardstock': {
            'name': 'Premium Cardstock',
            'description': 'Premium quality cardstock with enhanced durability',
            'specs': ['350gsm', 'Gloss', 'Premium'],
            'price_addon': 8,
            'image_class': 'paper-bw-premium',
            'icon': '📋'
        },
        '400gsm Luxury': {
            'name': 'Luxury Cardstock',
            'description': 'Ultra-premium cardstock with spot UV finish',
            'specs': ['400gsm', 'Spot UV', 'Luxury'],
            'price_addon': 20,
            'image_class': 'paper-color-premium',
            'icon': '🎨'
        }
    }
    
    for pricing in pricings:
        paper_type = pricing['paper_type']
        if paper_type in paper_types_info:
            paper_options.append(paper_types_info[paper_type])
    
    return JsonResponse({'paper_options': paper_options})


def get_color_options(request, product_id):
    """Get available color printing options"""
    product = get_object_or_404(Product, id=product_id)
    
    color_options = []
    pricings = product.pricings.filter(is_active=True).values('colors').distinct()
    
    color_types = {
        '1+0': {'name': 'Black Front Only', 'description': 'Single side black printing'},
        '1+1': {'name': 'Black Both Sides', 'description': 'Double side black printing'},
        '4+0': {'name': 'Color Front Only', 'description': 'Full color front, blank back'},
        '4+4': {'name': 'Color Both Sides', 'description': 'Full color on both sides'},
        '4+1': {'name': 'Color Front, Black Back', 'description': 'Full color front, black back'}
    }
    
    for pricing in pricings:
        color_code = pricing['colors']
        if color_code in color_types:
            color_options.append({
                'code': color_code,
                **color_types[color_code]
            })
    
    return JsonResponse({'color_options': color_options})


@require_http_methods(["GET"])
def api_shipping_cost(request):
    """Calculate shipping cost based on location and weight"""
    try:
        weight = float(request.GET.get('weight', 0))
        location = request.GET.get('location', 'local')
        express = request.GET.get('express', 'false').lower() == 'true'
        
        # Simple shipping calculation
        if location == 'local':
            base_cost = 50 if weight < 5 else 100
        elif location == 'national':
            base_cost = 100 if weight < 5 else 200
        else:  # international
            base_cost = 500 if weight < 5 else 1000
            
        if express:
            base_cost *= 1.5
            
        return JsonResponse({
            'success': True,
            'shipping_cost': base_cost,
            'delivery_days': 2 if express else 5,
            'currency': 'INR'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)