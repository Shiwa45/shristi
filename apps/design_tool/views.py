# apps/design_tool/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.contrib import messages
import json
import requests
from django.conf import settings

from apps.services.models import Product
from apps.templates_mgmt.models import DesignTemplate, TemplateCategory, UserDesign


def design_tool_view(request, product_slug=None):
    """Main design tool interface"""
    product = None
    if product_slug:
        product = get_object_or_404(Product, slug=product_slug, has_design_tool=True)
    
    # Get template categories for dropdown
    template_categories = TemplateCategory.objects.filter(is_active=True)
    
    context = {
        'product': product,
        'template_categories': template_categories,
    }
    
    return render(request, 'design_tool/designer.html', context)


@require_http_methods(["GET"])
def api_database_templates(request):
    """API endpoint for loading templates from database"""
    try:
        # Get pagination parameters
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 8))
        category_slug = request.GET.get('category', '')
        
        # Filter templates
        templates = DesignTemplate.objects.filter(is_active=True)
        
        if category_slug:
            templates = templates.filter(category__slug=category_slug)
        
        # Paginate
        paginator = Paginator(templates, per_page)
        page_obj = paginator.get_page(page)
        
        # Serialize templates
        template_data = []
        for template in page_obj:
            template_data.append({
                'id': template.id,
                'name': template.name,
                'thumbnail': template.thumbnail.url if template.thumbnail else None,
                'preview_image': template.preview_image.url if template.preview_image else None,
                'svg_file': template.svg_file.url if template.svg_file else None,
                'json_data': template.json_data,
                'width_mm': template.width_mm,
                'height_mm': template.height_mm,
                'bleed_mm': template.bleed_mm,
                'safe_zone_mm': template.safe_zone_mm,
                'category': template.category.name,
                'is_premium': template.is_premium,
            })
        
        response_data = {
            'success': True,
            'data': {
                'hits': template_data,
                'totalHits': paginator.count,
                'page': page,
                'pages': paginator.num_pages,
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def api_search_pixabay(request):
    """Proxy endpoint for Pixabay image search"""
    try:
        # Pixabay API configuration
        PIXABAY_API_KEY = getattr(settings, 'PIXABAY_API_KEY', '')
        PIXABAY_API_URL = 'https://pixabay.com/api/'
        
        if not PIXABAY_API_KEY:
            return JsonResponse({
                'success': False,
                'error': 'Pixabay API key not configured'
            }, status=500)
        
        # Get search parameters
        query = request.GET.get('q', '')
        page = request.GET.get('page', '1')
        per_page = request.GET.get('per_page', '12')
        image_type = request.GET.get('image_type', 'photo')
        
        # Make request to Pixabay
        params = {
            'key': PIXABAY_API_KEY,
            'q': query,
            'page': page,
            'per_page': per_page,
            'image_type': image_type,
            'safesearch': 'true',
            'category': 'all',
        }
        
        response = requests.get(PIXABAY_API_URL, params=params)
        response.raise_for_status()
        
        return JsonResponse({
            'success': True,
            'data': response.json()
        })
        
    except requests.RequestException as e:
        return JsonResponse({
            'success': False,
            'error': f'Pixabay API error: {str(e)}'
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_save_design(request):
    """Save user design to database"""
    try:
        data = json.loads(request.body)
        
        canvas_data = data.get('canvas')
        config = data.get('config')
        design_name = data.get('name', 'Untitled Design')
        
        if not canvas_data or not config:
            return JsonResponse({
                'success': False,
                'error': 'Missing canvas data or configuration'
            }, status=400)
        
        # Get or create product
        product_id = config.get('productId')
        if product_id:
            product = get_object_or_404(Product, id=product_id)
        else:
            # Default product or create a generic one
            product = Product.objects.filter(has_design_tool=True).first()
            if not product:
                return JsonResponse({
                    'success': False,
                    'error': 'No products available for design tool'
                }, status=400)
        
        # Create or update user design
        user_design, created = UserDesign.objects.get_or_create(
            user=request.user,
            name=design_name,
            product=product,
            defaults={
                'canvas_data': canvas_data,
                'width_mm': config.get('widthMM', product.width_mm),
                'height_mm': config.get('heightMM', product.height_mm),
                'bleed_mm': config.get('bleedMM', product.bleed_mm),
                'safe_zone_mm': config.get('safeZoneMM', product.safe_zone_mm),
            }
        )
        
        if not created:
            # Update existing design
            user_design.canvas_data = canvas_data
            user_design.width_mm = config.get('widthMM', user_design.width_mm)
            user_design.height_mm = config.get('heightMM', user_design.height_mm)
            user_design.bleed_mm = config.get('bleedMM', user_design.bleed_mm)
            user_design.safe_zone_mm = config.get('safeZoneMM', user_design.safe_zone_mm)
            user_design.save()
        
        return JsonResponse({
            'success': True,
            'design_id': user_design.id,
            'message': 'Design saved successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_load_design(request, design_id):
    """Load user design from database"""
    try:
        user_design = get_object_or_404(UserDesign, id=design_id, user=request.user)
        
        return JsonResponse({
            'success': True,
            'data': {
                'name': user_design.name,
                'canvas_data': user_design.canvas_data,
                'config': {
                    'widthMM': user_design.width_mm,
                    'heightMM': user_design.height_mm,
                    'bleedMM': user_design.bleed_mm,
                    'safeZoneMM': user_design.safe_zone_mm,
                    'productId': user_design.product.id,
                },
                'product': {
                    'id': user_design.product.id,
                    'name': user_design.product.name,
                    'slug': user_design.product.slug,
                }
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_user_designs(request):
    """Get list of user's saved designs"""
    try:
        designs = UserDesign.objects.filter(user=request.user)
        
        designs_data = []
        for design in designs:
            designs_data.append({
                'id': design.id,
                'name': design.name,
                'product_name': design.product.name,
                'preview_image': design.preview_image.url if design.preview_image else None,
                'created_at': design.created_at.isoformat(),
                'updated_at': design.updated_at.isoformat(),
            })
        
        return JsonResponse({
            'success': True,
            'designs': designs_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def api_products(request):
    """API endpoint for products list"""
    try:
        products = Product.objects.filter(is_active=True)
        
        products_data = []
        for product in products:
            products_data.append({
                'id': product.id,
                'name': product.name,
                'slug': product.slug,
                'width': product.width_mm,
                'height': product.height_mm,
                'bleed_size': product.bleed_mm,
                'safe_zone': product.safe_zone_mm,
                'has_design_tool': product.has_design_tool,
                'category': product.category.name,
            })
        
        return JsonResponse({
            'success': True,
            'results': products_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def api_categories(request):
    """API endpoint for template categories"""
    try:
        categories = TemplateCategory.objects.filter(is_active=True)
        
        categories_data = []
        for category in categories:
            categories_data.append({
                'id': category.id,
                'name': category.name,
                'slug': category.slug,
                'description': category.description,
            })
        
        return JsonResponse({
            'success': True,
            'results': categories_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)