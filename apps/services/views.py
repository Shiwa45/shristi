# apps/services/views.py - Updated for Category-Specific Pages

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator
from django.db.models import Q, Case, When, Value, IntegerField
from django.views.decorators.http import require_http_methods
from decimal import Decimal
import json
from .models import ServiceCategory, StaticProduct, CategoryFormField, CategoryPricingRule

ALLOWED_CATEGORIES = [
    'book-printing',
    'paper-boxes', 
    'marketing-material',
    'stationery'
]

# Whitelisted product names for categories that should only show a curated set
CATEGORY_PRODUCT_WHITELIST = {
    'marketing-material': [
        'Brochures',
        'Certificates',
        'Poster',
        'Posters',
        'Flyers & Leaflets',
        'Flyers',
        'Dangler',
        'Danglers',
        'Standees',
        'Button Badges',
        'Tent Card',
    ],
    'stationery': [
        'Business Card',
        'Business Cards',
        'Letter Head',
        'Letterheads',
        'Envelopes',
        'Bill Book',
        'Bill Books',
        'ID Cards',
        'Document Printing',
    ],
}


def _apply_curated_products(queryset, slug, exclude_id=None):
    """
    Limit a product queryset to the curated list for specific categories and
    ensure ordering matches the requested sequence.
    """
    preferred_names = CATEGORY_PRODUCT_WHITELIST.get(slug, [])
    if not preferred_names:
        return queryset

    name_filter = Q()
    for name in preferred_names:
        name_filter |= Q(name__iexact=name)

    if exclude_id:
        queryset = queryset.exclude(id=exclude_id)

    order_cases = [
        When(name__iexact=name, then=Value(index))
        for index, name in enumerate(preferred_names)
    ]

    return (
        queryset.filter(name_filter)
        .annotate(
            preferred_order=Case(
                *order_cases,
                default=Value(len(preferred_names)),
                output_field=IntegerField(),
            )
        )
        .order_by('preferred_order', 'order', 'name')
    )


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

    # Apply curated product list for Marketing Materials and Stationery to remove extras
    products = _apply_curated_products(products, slug)

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


def all_products(request):
    """All products page showing all products without filters"""
    products = StaticProduct.objects.filter(
        is_active=True
    ).select_related('category').order_by('category__order', 'category__name', 'order', 'name')

    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'page_obj': page_obj,
        'page_title': 'All Products - Shirsti Printing',
        'is_all_products': True
    }
    return render(request, 'services/all_products.html', context)


def static_product_detail(request, category_slug, product_slug):
    """Enhanced static product detail page with category-specific features"""
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

    # Keep related products aligned with curated lists where applicable
    if CATEGORY_PRODUCT_WHITELIST.get(category.slug):
        related_products = _apply_curated_products(
            StaticProduct.objects.filter(
                category=category,
                is_active=True,
            ),
            category.slug,
            exclude_id=product.id,
        ).select_related('category')[:4]

    # If no related products in same category, get from other categories
    if len(related_products) < 4:
        additional_products = StaticProduct.objects.filter(
            is_active=True,
            is_featured=True
        ).exclude(id=product.id).exclude(
            id__in=[p.id for p in related_products]
        ).select_related('category')[:4-len(related_products)]
        related_products = list(related_products) + list(additional_products)

    # Check if this category has category-specific features
    is_category_specific = category.slug in ALLOWED_CATEGORIES
    
    # Get category-specific form fields and pricing rules if applicable
    form_fields = []
    form_sections = {}
    pricing_rules = []
    
    if is_category_specific:
        form_fields = category.get_category_form_fields()
        form_sections = category.get_form_sections()
        pricing_rules = category.get_pricing_rules()

    # Determine template based on category
    template_name = 'services/static_products/product_detail.html'
    if is_category_specific:
        category_templates = {
            'book-printing': 'services/static_products/book_printing_detail.html',
            'paper-boxes': 'services/static_products/paper_boxes_detail.html',
            'marketing-material': 'services/static_products/marketing_material_detail.html',
            'stationery': 'services/static_products/stationery_detail.html'
        }
        template_name = category_templates.get(category.slug, template_name)

    context = {
        'category': category,
        'product': product,
        'related_products': related_products,
        'page_title': f'{product.name} - {category.name} - Shirsti Printing',
        'meta_description': product.short_description,
        'canonical_url': request.build_absolute_uri(),
        'is_category_specific': is_category_specific,
        'form_fields': form_fields,
        'form_sections': form_sections,
        'pricing_rules': pricing_rules,
        'category_slug': category.slug,
    }
    
    # Add category-specific context
    if category.slug == 'book-printing':
        context.update({
            'hero_padding': 'padding: 60px 0 35px;',
            'min_quantity': 25,
            'min_pages': 4,
            'binding_page_limit': 30,
            'design_service_price': 1500,
            'inner_page_design_price': 50,
            'isbn_delivery_days': '5-7',
            'gst_percentage': 18,
        })
    elif category.slug == 'paper-boxes':
        context.update({
            'min_quantity': 100,
            'material_types': ['Corrugated', 'Cardboard', 'Kraft'],
            'printing_options': ['No Printing', '1-Color', 'Full Color'],
            'finishing_options': ['Matte', 'Gloss', 'UV Coating'],
        })
    elif category.slug == 'marketing-material':
        context.update({
            'material_types': ['Brochures', 'Flyers', 'Posters', 'Catalogs'],
            'featured_services': ['Brochures', 'Business Cards', 'Flyers'],
            'design_service_available': True,
        })
    elif category.slug == 'stationery':
        context.update({
            'stationery_types': ['Business Cards', 'Letterheads', 'Envelopes'],
            'premium_options': ['Embossing', 'Foil Stamping', 'Spot UV'],
            'standard_sizes': True,
        })
    
    return render(request, template_name, context)

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


@require_http_methods(["POST"])
def category_pricing_api(request):
    """API endpoint for category-specific pricing calculation"""
    try:
        # Parse JSON data from request body
        data = json.loads(request.body)
        category_slug = data.get('category')
        form_data = data.get('form_data', {})
        quantity = int(data.get('quantity', 25))
        
        # Validate category
        if category_slug not in CategorySpecificView.ALLOWED_CATEGORIES:
            return JsonResponse({'error': 'Invalid category'}, status=400)
        
        # Get category and pricing rules
        try:
            category = ServiceCategory.objects.get(slug=category_slug, is_active=True)
        except ServiceCategory.DoesNotExist:
            return JsonResponse({'error': 'Category not found'}, status=404)
        
        pricing_rules = category.get_pricing_rules()
        
        # Calculate pricing based on category-specific rules
        total_price = Decimal('0.00')
        price_breakdown = {
            'base_price': Decimal('0.00'),
            'option_modifiers': {},
            'quantity_discount': Decimal('0.00'),
            'additional_services': {},
            'subtotal': Decimal('0.00'),
            'gst': Decimal('0.00'),
            'total': Decimal('0.00')
        }
        
        # Apply pricing rules
        for rule in pricing_rules:
            if rule.applies_to(form_data, quantity):
                rule_price = rule.calculate_price(form_data, quantity, total_price)
                
                if rule.rule_type == 'base_price':
                    price_breakdown['base_price'] = rule_price
                    total_price = rule_price
                elif rule.rule_type == 'option_modifier':
                    price_breakdown['option_modifiers'][rule.rule_name] = rule_price
                    total_price += rule_price
                elif rule.rule_type == 'quantity_tier':
                    price_breakdown['quantity_discount'] = rule_price
                    total_price += rule_price  # rule_price is negative for discounts
                elif rule.rule_type in ['conditional_pricing', 'page_based_pricing']:
                    price_breakdown['option_modifiers'][rule.rule_name] = rule_price
                    total_price += rule_price
        
        # Calculate subtotal
        price_breakdown['subtotal'] = total_price
        
        # Add GST (18%)
        gst_amount = total_price * Decimal('0.18')
        price_breakdown['gst'] = gst_amount
        
        # Calculate final total
        final_total = total_price + gst_amount
        price_breakdown['total'] = final_total
        
        # Convert Decimal to float for JSON serialization
        def decimal_to_float(obj):
            if isinstance(obj, dict):
                return {k: decimal_to_float(v) for k, v in obj.items()}
            elif isinstance(obj, Decimal):
                return float(obj)
            return obj
        
        price_breakdown = decimal_to_float(price_breakdown)
        
        return JsonResponse({
            'success': True,
            'category': category_slug,
            'quantity': quantity,
            'price_breakdown': price_breakdown,
            'price_per_unit': float(final_total) / quantity if quantity > 0 else 0,
            'currency': 'INR'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except ValueError as e:
        return JsonResponse({'error': f'Invalid parameter: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Internal server error'}, status=500)
