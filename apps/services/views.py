# apps/services/views.py - Updated for Static Products

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import ServiceCategory, StaticProduct

def services_home(request):
    """Services home page showing all categories"""
    categories = ServiceCategory.objects.filter(is_active=True).prefetch_related(
        'static_products'
    ).order_by('order', 'name')

    # Get featured products
    featured_products = StaticProduct.objects.filter(
        is_active=True,
        is_featured=True
    ).select_related('category')[:6]

    context = {
        'categories': categories,
        'featured_products': featured_products,
        'page_title': 'Our Printing Services'
    }

    # Determine template based on URL path
    if request.path.endswith('/categories/'):
        template = 'services/categories.html'
    else:
        template = 'services/categories.html'  # Use categories.html for services home too

    return render(request, template, context)


def category_detail(request, slug):
    """Category detail page showing all products in category"""
    category = get_object_or_404(ServiceCategory, slug=slug, is_active=True)
    
    products = StaticProduct.objects.filter(
        category=category,
        is_active=True
    ).order_by('order', 'name')
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'products': page_obj,
        'page_obj': page_obj,
        'page_title': f'{category.name} - Shirsti Printing'
    }
    return render(request, 'services/category_detail.html', context)


def static_product_detail(request, category_slug, product_slug):
    """Enhanced static product detail page with all features"""
    category = get_object_or_404(ServiceCategory, slug=category_slug, is_active=True)
    product = get_object_or_404(
        StaticProduct,
        slug=product_slug,
        category=category,
        is_active=True
    )

    # Get related products (same category, excluding current)
    related_products = StaticProduct.objects.filter(
        category=category,
        is_active=True
    ).exclude(id=product.id).select_related('category')[:4]

    # If no related products in same category, get from other categories
    if len(related_products) < 4:
        additional_products = StaticProduct.objects.filter(
            is_active=True,
            is_featured=True
        ).exclude(id=product.id).exclude(
            id__in=[p.id for p in related_products]
        ).select_related('category')[:4-len(related_products)]
        related_products = list(related_products) + list(additional_products)

    context = {
        'category': category,
        'product': product,
        'related_products': related_products,
        'page_title': f'{product.name} - {category.name} - Shirsti Printing',
        'meta_description': product.short_description,
        'canonical_url': request.build_absolute_uri(),
    }
    return render(request, 'services/static_products/product_detail.html', context)

def product_detail(request, category_slug, product_slug):
    """Handle StaticProduct model only"""
    return static_product_detail(request, category_slug, product_slug)


def product_pricing_api(request, product_id):
    """API endpoint for dynamic pricing calculation"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        product = get_object_or_404(StaticProduct, id=product_id, is_active=True)
        
        # Get parameters from request
        quantity = int(request.GET.get('quantity', 100))
        size = request.GET.get('size')
        paper = request.GET.get('paper')
        finish = request.GET.get('finish')
        binding = request.GET.get('binding')
        color = request.GET.get('color')
        rush_order = request.GET.get('rush_order', 'false').lower() == 'true'
        design_service = request.GET.get('design_service', 'false').lower() == 'true'
        
        # Calculate price using the model method
        total_price = product.calculate_price(
            quantity=quantity,
            size=size,
            paper=paper,
            finish=finish,
            binding=binding,
            color=color,
            rush_order=rush_order,
            design_service=design_service
        )
        
        # Calculate breakdown for display
        base_price = product.base_price
        
        # Calculate modifiers
        size_modifier = 0
        if size and product.available_sizes:
            for size_option in product.available_sizes:
                if size_option.get('name') == size:
                    size_modifier = float(size_option.get('price_modifier', 0))
                    break
        
        paper_modifier = 0
        if paper and product.available_papers:
            for paper_option in product.available_papers:
                if paper_option.get('name') == paper:
                    paper_modifier = float(paper_option.get('price_modifier', 0))
                    break
        
        finish_modifier = 0
        if finish and product.available_finishes:
            for finish_option in product.available_finishes:
                if finish_option.get('name') == finish:
                    finish_modifier = float(finish_option.get('price_modifier', 0))
                    break
        
        # Calculate discount percentage
        discount_percent = 0
        if product.quantity_tiers:
            for tier in product.quantity_tiers:
                if tier.get('min_qty', 0) <= quantity <= tier.get('max_qty', float('inf')):
                    discount_percent = tier.get('discount_percent', 0)
                    break
        
        unit_price = float(base_price) + size_modifier + paper_modifier + finish_modifier
        subtotal_before_discount = unit_price * quantity
        discount_amount = subtotal_before_discount * (discount_percent / 100)
        subtotal_after_discount = subtotal_before_discount - discount_amount
        
        rush_amount = 0
        if rush_order and product.rush_order_available:
            rush_amount = subtotal_after_discount * (product.rush_order_percentage / 100)
        
        design_amount = 0
        if design_service and product.design_service_available:
            design_amount = float(product.design_service_price)
        
        return JsonResponse({
            'success': True,
            'pricing': {
                'base_price': float(base_price),
                'unit_price': unit_price,
                'quantity': quantity,
                'subtotal_before_discount': subtotal_before_discount,
                'discount_percent': discount_percent,
                'discount_amount': discount_amount,
                'subtotal_after_discount': subtotal_after_discount,
                'rush_amount': rush_amount,
                'design_amount': design_amount,
                'total_price': float(total_price),
                'price_per_unit': float(total_price) / quantity if quantity > 0 else 0
            },
            'breakdown': {
                'size_modifier': size_modifier,
                'paper_modifier': paper_modifier,
                'finish_modifier': finish_modifier,
                'rush_percentage': product.rush_order_percentage if rush_order else 0,
                'design_service_price': float(product.design_service_price) if design_service else 0
            }
        })
        
    except StaticProduct.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
    except ValueError as e:
        return JsonResponse({'error': f'Invalid parameter: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Internal server error'}, status=500)


def product_search(request):
    """Search products across all categories"""
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category')
    
    products = StaticProduct.objects.filter(is_active=True).select_related('category')
    
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(short_description__icontains=query)
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


