# apps/services/views.py - Enhanced version

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Min, Max
from .models import ServiceCategory, Product, ProductPricing
import json

def service_categories_view(request):
    """Display all service categories"""
    categories = ServiceCategory.objects.filter(is_active=True).order_by('order')
    context = {
        'categories': categories,
        'page_title': 'Our Services'
    }
    return render(request, 'services/list.html', context)

def category_products_view(request, slug):
    """Display products in a specific category"""
    category = get_object_or_404(ServiceCategory, slug=slug, is_active=True)
    products = Product.objects.filter(
        category=category, 
        is_active=True
    ).order_by('name')
    
    context = {
        'category': category,
        'products': products,
        'page_title': f'{category.name} Services'
    }
    return render(request, 'services/category.html', context)

def product_detail_view(request, slug):
    """Enhanced product detail view with pricing integration"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    
    # Get available pricing options for the product
    available_sizes = product.pricings.filter(is_active=True).values_list('size', flat=True).distinct()
    available_paper_types = product.pricings.filter(is_active=True).values_list('paper_type', flat=True).distinct()
    available_finishes = product.pricings.filter(is_active=True).values_list('finish', flat=True).distinct()
    
    # Get quantity ranges
    quantity_range = product.pricings.filter(is_active=True).aggregate(
        min_qty=Min('min_quantity'),
        max_qty=Max('min_quantity')
    )
    
    # Get related products
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:4]
    
    # Check if user has items in cart (if authenticated)
    in_cart = False
    if request.user.is_authenticated:
        # This would integrate with your cart system
        pass
    
    context = {
        'product': product,
        'available_sizes': list(available_sizes),
        'available_paper_types': list(available_paper_types),
        'available_finishes': list(available_finishes),
        'quantity_range': quantity_range,
        'related_products': related_products,
        'in_cart': in_cart,
    }
    
    return render(request, 'services/product_detail.html', context)

@require_http_methods(["GET"])
def api_product_pricing(request, product_id):
    """Enhanced API endpoint for dynamic pricing"""
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Get parameters from request
        size = request.GET.get('size', '')
        paper_type = request.GET.get('paper_type', '')
        finish = request.GET.get('finish', '')
        binding_type = request.GET.get('binding_type', '')
        colors = request.GET.get('colors', '4+4')  # Default full color both sides
        quantity = int(request.GET.get('quantity', 1))
        
        if quantity <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Quantity must be greater than 0'
            }, status=400)
        
        # Find the best matching ProductPricing
        pricing_qs = product.pricings.filter(
            size=size,
            paper_type=paper_type,
            finish=finish,
            min_quantity__lte=quantity,
            is_active=True
        )
        
        # Add binding type filter if provided and not empty
        if binding_type:
            pricing_qs = pricing_qs.filter(binding_type=binding_type)
        
        # Order by quantity descending to get the best volume pricing
        pricing_qs = pricing_qs.order_by('-min_quantity')
        
        if pricing_qs.exists():
            pricing = pricing_qs.first()
            base_unit_price = float(pricing.price_per_unit)
            
            # Apply volume discounts
            volume_discount = 0
            if quantity >= 5000:
                volume_discount = 0.20  # 20% discount
            elif quantity >= 2000:
                volume_discount = 0.15  # 15% discount
            elif quantity >= 1000:
                volume_discount = 0.10  # 10% discount
            elif quantity >= 500:
                volume_discount = 0.05  # 5% discount
            
            # Apply color pricing modifier
            color_multiplier = 1.0
            if colors == '4+4':  # Full color both sides
                color_multiplier = 1.2
            elif colors == '4+0':  # Full color one side
                color_multiplier = 1.0
            elif colors == '1+1':  # Black and white both sides
                color_multiplier = 0.8
            elif colors == '1+0':  # Black and white one side
                color_multiplier = 0.6
            
            # Calculate final pricing
            discounted_unit_price = base_unit_price * (1 - volume_discount) * color_multiplier
            total_price = discounted_unit_price * quantity
            base_total = base_unit_price * quantity * color_multiplier
            savings = base_total - total_price
            
            return JsonResponse({
                'success': True,
                'unit_price': round(discounted_unit_price, 2),
                'price': round(total_price, 2),
                'base_price': round(base_unit_price * color_multiplier, 2),
                'savings': round(savings, 2) if savings > 0 else 0,
                'volume_discount': volume_discount * 100,  # Return as percentage
                'color_multiplier': color_multiplier,
                'currency': 'INR',
                'quantity': quantity,
                'pricing_tier': pricing.min_quantity
            })
        else:
            # No exact pricing found - return quote required
            return JsonResponse({
                'success': False,
                'error': 'Custom quote required for these specifications',
                'requires_quote': True
            }, status=404)
            
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
        
        # Get all unique options from pricing table
        options = {
            'sizes': list(product.pricings.filter(is_active=True).values_list('size', flat=True).distinct()),
            'paper_types': list(product.pricings.filter(is_active=True).values_list('paper_type', flat=True).distinct()),
            'finishes': list(product.pricings.filter(is_active=True).values_list('finish', flat=True).distinct()),
            'binding_types': list(product.pricings.filter(is_active=True).values_list('binding_type', flat=True).distinct()),
            'quantity_tiers': list(product.pricings.filter(is_active=True).values_list('min_quantity', flat=True).distinct().order_by('min_quantity'))
        }
        
        # Remove empty values
        for key in options:
            options[key] = [opt for opt in options[key] if opt]
        
        return JsonResponse({
            'success': True,
            'options': options,
            'product_info': {
                'name': product.name,
                'category': product.category.name,
                'has_design_tool': product.has_design_tool,
                'allows_upload': product.allows_upload
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def product_search(request):
    """Search products by name or category"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    # Search in product names and descriptions
    products = Product.objects.filter(
        Q(name__icontains=query) | 
        Q(description__icontains=query) |
        Q(category__name__icontains=query),
        is_active=True
    )[:10]
    
    suggestions = []
    for product in products:
        suggestions.append({
            'id': product.id,
            'name': product.name,
            'category': product.category.name,
            'url': product.get_absolute_url(),
            'has_design_tool': product.has_design_tool,
            'image': product.image.url if product.image else None
        })
    
    return JsonResponse({'suggestions': suggestions})




def product_search(request):
    """Search products by name or category"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    # Search in product names and descriptions
    products = Product.objects.filter(
        Q(name__icontains=query) | 
        Q(description__icontains=query) |
        Q(category__name__icontains=query),
        is_active=True
    )[:10]
    
    suggestions = []
    for product in products:
        suggestions.append({
            'id': product.id,
            'name': product.name,
            'category': product.category.name,
            'url': product.get_absolute_url(),
            'has_design_tool': product.has_design_tool,
            'image': product.image.url if product.image else None
        })
    
    return JsonResponse({'suggestions': suggestions})

@require_http_methods(["GET"])
def api_bulk_pricing(request, product_id):
    """Get bulk pricing tiers for a product"""
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Get parameters
        size = request.GET.get('size', '')
        paper_type = request.GET.get('paper_type', '')
        finish = request.GET.get('finish', '')
        colors = request.GET.get('colors', '4+4')
        
        # Get all matching pricing tiers
        pricing_qs = product.pricings.filter(
            size=size,
            paper_type=paper_type,
            finish=finish,
            is_active=True
        ).order_by('min_quantity')
        
        if colors:
            # If colors specified, try to filter by it, but don't exclude if no match
            color_filtered = pricing_qs.filter(colors=colors)
            if color_filtered.exists():
                pricing_qs = color_filtered
        
        if not pricing_qs.exists():
            return JsonResponse({
                'success': False,
                'error': 'No pricing tiers found for selected specifications'
            })
        
        # Build pricing table data
        tiers = []
        for pricing in pricing_qs:
            # Calculate prices for common quantities
            quantities = [pricing.min_quantity]
            if pricing.min_quantity < 500:
                quantities.extend([500, 1000, 2000, 5000])
            elif pricing.min_quantity < 1000:
                quantities.extend([1000, 2000, 5000])
            elif pricing.min_quantity < 2000:
                quantities.extend([2000, 5000])
            else:
                quantities.extend([pricing.min_quantity * 2, pricing.min_quantity * 5])
            
            tier_data = {
                'specifications': {
                    'size': pricing.size,
                    'paper_type': pricing.paper_type,
                    'finish': pricing.finish,
                    'colors': pricing.colors or colors
                },
                'min_quantity': pricing.min_quantity,
                'max_quantity': pricing.max_quantity,
                'base_price_per_unit': float(pricing.price_per_unit),
                'setup_cost': float(pricing.setup_cost),
                'turnaround_days': pricing.turnaround_days,
                'volume_discount': float(pricing.volume_discount_percentage),
                'quantities': []
            }
            
            for qty in quantities:
                if qty >= pricing.min_quantity and (not pricing.max_quantity or qty <= pricing.max_quantity):
                    calc = pricing.calculate_total_price(qty)
                    if calc:
                        tier_data['quantities'].append({
                            'quantity': qty,
                            'unit_price': calc['unit_price'],
                            'total_price': calc['total_price'],
                            'savings': calc['savings']
                        })
            
            tiers.append(tier_data)
        
        return JsonResponse({
            'success': True,
            'product_name': product.name,
            'tiers': tiers
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def api_quote_request(request):
    """Handle quote requests"""
    try:
        data = json.loads(request.body)
        
        # Extract quote data
        product_id = data.get('product_id')
        customer_info = data.get('customer_info', {})
        specifications = data.get('specifications', {})
        quantity = data.get('quantity', 0)
        special_requirements = data.get('special_requirements', '')
        
        # Validate required fields
        if not product_id:
            return JsonResponse({
                'success': False,
                'error': 'Product ID is required'
            }, status=400)
        
        if not customer_info.get('email'):
            return JsonResponse({
                'success': False,
                'error': 'Customer email is required'
            }, status=400)
        
        if quantity <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Valid quantity is required'
            }, status=400)
        
        # Get the product
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Here you would typically:
        # 1. Save the quote request to the database
        # 2. Send email notifications to admin/sales team
        # 3. Send confirmation email to customer
        
        # For now, we'll just return success
        quote_reference = f"QT{product_id}{quantity}{hash(str(customer_info.get('email')))}"[-8:]
        
        return JsonResponse({
            'success': True,
            'message': 'Quote request submitted successfully',
            'quote_reference': quote_reference,
            'estimated_response_time': '24 hours'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while processing your quote request'
        }, status=500)# apps/services/views.py - Enhanced version

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Min, Max
from .models import ServiceCategory, Product, ProductPricing
import json

def service_categories_view(request):
    """Display all service categories"""
    categories = ServiceCategory.objects.filter(is_active=True).order_by('order')
    context = {
        'categories': categories,
        'page_title': 'Our Services'
    }
    return render(request, 'services/list.html', context)

def category_products_view(request, slug):
    """Display products in a specific category"""
    category = get_object_or_404(ServiceCategory, slug=slug, is_active=True)
    products = Product.objects.filter(
        category=category, 
        is_active=True
    ).order_by('name')
    
    context = {
        'category': category,
        'products': products,
        'page_title': f'{category.name} Services'
    }
    return render(request, 'services/category.html', context)

def product_detail_view(request, slug):
    """Enhanced product detail view with pricing integration"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    
    # Get available pricing options for the product
    available_sizes = product.pricings.filter(is_active=True).values_list('size', flat=True).distinct()
    available_paper_types = product.pricings.filter(is_active=True).values_list('paper_type', flat=True).distinct()
    available_finishes = product.pricings.filter(is_active=True).values_list('finish', flat=True).distinct()
    
    # Get quantity ranges
    quantity_range = product.pricings.filter(is_active=True).aggregate(
        min_qty=Min('min_quantity'),
        max_qty=Max('min_quantity')
    )
    
    # Get related products
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:4]
    
    # Check if user has items in cart (if authenticated)
    in_cart = False
    if request.user.is_authenticated:
        # This would integrate with your cart system
        pass
    
    context = {
        'product': product,
        'available_sizes': list(available_sizes),
        'available_paper_types': list(available_paper_types),
        'available_finishes': list(available_finishes),
        'quantity_range': quantity_range,
        'related_products': related_products,
        'in_cart': in_cart,
    }
    
    return render(request, 'services/product_detail.html', context)

@require_http_methods(["GET"])
def api_product_pricing(request, product_id):
    """Enhanced API endpoint for dynamic pricing"""
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Get parameters from request
        size = request.GET.get('size', '')
        paper_type = request.GET.get('paper_type', '')
        finish = request.GET.get('finish', '')
        binding_type = request.GET.get('binding_type', '')
        colors = request.GET.get('colors', '4+4')  # Default full color both sides
        quantity = int(request.GET.get('quantity', 1))
        
        if quantity <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Quantity must be greater than 0'
            }, status=400)
        
        # Find the best matching ProductPricing
        pricing_qs = product.pricings.filter(
            size=size,
            paper_type=paper_type,
            finish=finish,
            min_quantity__lte=quantity,
            is_active=True
        )
        
        # Add binding type filter if provided and not empty
        if binding_type:
            pricing_qs = pricing_qs.filter(binding_type=binding_type)
        
        # Order by quantity descending to get the best volume pricing
        pricing_qs = pricing_qs.order_by('-min_quantity')
        
        if pricing_qs.exists():
            pricing = pricing_qs.first()
            base_unit_price = float(pricing.price_per_unit)
            
            # Apply volume discounts
            volume_discount = 0
            if quantity >= 5000:
                volume_discount = 0.20  # 20% discount
            elif quantity >= 2000:
                volume_discount = 0.15  # 15% discount
            elif quantity >= 1000:
                volume_discount = 0.10  # 10% discount
            elif quantity >= 500:
                volume_discount = 0.05  # 5% discount
            
            # Apply color pricing modifier
            color_multiplier = 1.0
            if colors == '4+4':  # Full color both sides
                color_multiplier = 1.2
            elif colors == '4+0':  # Full color one side
                color_multiplier = 1.0
            elif colors == '1+1':  # Black and white both sides
                color_multiplier = 0.8
            elif colors == '1+0':  # Black and white one side
                color_multiplier = 0.6
            
            # Calculate final pricing
            discounted_unit_price = base_unit_price * (1 - volume_discount) * color_multiplier
            total_price = discounted_unit_price * quantity
            base_total = base_unit_price * quantity * color_multiplier
            savings = base_total - total_price
            
            return JsonResponse({
                'success': True,
                'unit_price': round(discounted_unit_price, 2),
                'price': round(total_price, 2),
                'base_price': round(base_unit_price * color_multiplier, 2),
                'savings': round(savings, 2) if savings > 0 else 0,
                'volume_discount': volume_discount * 100,  # Return as percentage
                'color_multiplier': color_multiplier,
                'currency': 'INR',
                'quantity': quantity,
                'pricing_tier': pricing.min_quantity
            })
        else:
            # No exact pricing found - return quote required
            return JsonResponse({
                'success': False,
                'error': 'Custom quote required for these specifications',
                'requires_quote': True
            }, status=404)
            
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
        
        # Get all unique options from pricing table
        options = {
            'sizes': list(product.pricings.filter(is_active=True).values_list('size', flat=True).distinct()),
            'paper_types': list(product.pricings.filter(is_active=True).values_list('paper_type', flat=True).distinct()),
            'finishes': list(product.pricings.filter(is_active=True).values_list('finish', flat=True).distinct()),
            'binding_types': list(product.pricings.filter(is_active=True).values_list('binding_type', flat=True).distinct()),
            'quantity_tiers': list(product.pricings.filter(is_active=True).values_list('min_quantity', flat=True).distinct().order_by('min_quantity'))
        }
        
        # Remove empty values
        for key in options:
            options[key] = [opt for opt in options[key] if opt]
        
        return JsonResponse({
            'success': True,
            'options': options,
            'product_info': {
                'name': product.name,
                'category': product.category.name,
                'has_design_tool': product.has_design_tool,
                'allows_upload': product.allows_upload
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def product_search(request):
    """Search products by name or category"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    # Search in product names and descriptions
    products = Product.objects.filter(
        Q(name__icontains=query) | 
        Q(description__icontains=query) |
        Q(category__name__icontains=query),
        is_active=True
    )[:10]
    
    suggestions = []
    for product in products:
        suggestions.append({
            'id': product.id,
            'name': product.name,
            'category': product.category.name,
            'url': product.get_absolute_url(),
            'has_design_tool': product.has_design_tool,
            'image': product.image.url if product.image else None
        })
    
    return JsonResponse({'suggestions': suggestions})