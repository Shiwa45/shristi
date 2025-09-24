# apps/services/views.py
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import ServiceCategory, Product


def services_list_view(request):
    """List all service categories"""
    categories = ServiceCategory.objects.filter(is_active=True).prefetch_related('products')
    
    context = {
        'categories': categories,
        'page_title': 'Our Services'
    }
    return render(request, 'services/list.html', context)


def category_view(request, slug):
    """Display products in a specific category"""
    category = get_object_or_404(ServiceCategory, slug=slug, is_active=True)
    
    # Get products with filtering
    products = Product.objects.filter(category=category, is_active=True)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Filtering
    has_design_tool = request.GET.get('design_tool')
    if has_design_tool == 'yes':
        products = products.filter(has_design_tool=True)
    elif has_design_tool == 'no':
        products = products.filter(has_design_tool=False)
    
    # Sorting
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'price_low':
        products = products.order_by('price_per_unit')
    elif sort_by == 'price_high':
        products = products.order_by('-price_per_unit')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('name')
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Related categories
    related_categories = ServiceCategory.objects.filter(
        is_active=True
    ).exclude(id=category.id)[:4]
    
    context = {
        'category': category,
        'page_obj': page_obj,
        'products': page_obj.object_list,
        'related_categories': related_categories,
        'search_query': search_query,
        'sort_by': sort_by,
        'has_design_tool': has_design_tool,
        'page_title': f'{category.name} - Printing Services'
    }
    
    return render(request, 'services/category.html', context)


def product_detail_view(request, slug):
    """Product detail page"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    
    # Related products from same category
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:4]
    
    # Product specifications for display
    specifications = {
        'Dimensions': f'{product.width_mm} × {product.height_mm} mm',
        'Bleed': f'{product.bleed_mm} mm',
        'Safe Zone': f'{product.safe_zone_mm} mm',
        'Print Resolution': f'{product.dpi} DPI',
        'Minimum Quantity': product.minimum_quantity,
    }
    
    context = {
        'product': product,
        'related_products': related_products,
        'specifications': specifications,
        'page_title': f'{product.name} - {product.category.name}'
    }
    
    return render(request, 'services/product_detail.html', context)


def products_search_view(request):
    """Global product search"""
    search_query = request.GET.get('q', '')
    products = Product.objects.filter(is_active=True)
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(products, 16)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'products': page_obj.object_list,
        'search_query': search_query,
        'page_title': f'Search Results for "{search_query}"' if search_query else 'Product Search'
    }
    
    return render(request, 'services/search.html', context)


@require_http_methods(["GET"])
def api_product_suggestions(request):
    """API endpoint for product search suggestions"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    products = Product.objects.filter(
        Q(name__icontains=query) | Q(category__name__icontains=query),
        is_active=True
    )[:10]
    
    suggestions = []
    for product in products:
        suggestions.append({
            'id': product.id,
            'name': product.name,
            'category': product.category.name,
            'url': product.get_absolute_url(),
            'has_design_tool': product.has_design_tool
        })
    
    return JsonResponse({'suggestions': suggestions})


@require_http_methods(["GET"])
def api_product_pricing(request, product_id):
    """API endpoint for dynamic pricing based on quantity"""
    try:
        product = Product.objects.get(id=product_id, is_active=True)
        size = request.GET.get('size', '')
        paper_type = request.GET.get('paper_type', '')
        finish = request.GET.get('finish', '')
        quantity = int(request.GET.get('quantity', 1))

        # Find the best matching ProductPricing
        pricing_qs = product.pricings.filter(
            size=size,
            paper_type=paper_type,
            finish=finish,
            min_quantity__lte=quantity,
            is_active=True
        ).order_by('-min_quantity')

        if pricing_qs.exists():
            pricing = pricing_qs.first()
            unit_price = float(pricing.price_per_unit)
            total_price = unit_price * quantity
            return JsonResponse({
                'success': True,
                'unit_price': unit_price,
                'price': total_price,
                'currency': 'INR',
                'quantity': quantity
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'No pricing found for selected options.'
            }, status=404)
    except (Product.DoesNotExist, ValueError) as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    

# apps/services/views.py - Add this to your existing product_detail_view

def product_detail_view_enhanced(request, slug):
    """Enhanced product detail view with cart integration"""
    product = get_object_or_404(Product, slug=slug)
    
    # Check if product is in user's cart
    in_cart = False
    if request.user.is_authenticated:
        cart_manager = CartManager(request)
        cart = cart_manager.get_or_create_cart()
        in_cart = cart.items.filter(product=product).exists()
    
    # Get related products
    related_products = Product.objects.filter(
        service=product.service
    ).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'in_cart': in_cart,
        'related_products': related_products,
        'variations': product.variations.all() if hasattr(product, 'variations') else [],
    }
    
    return render(request, 'services/product_detail.html', context)


