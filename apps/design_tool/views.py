# apps/design_tool/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.contrib import messages
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
from django.db.models import Q
import json
import base64
import io
from PIL import Image
import uuid

from apps.services.models import Product
from apps.templates_mgmt.models import DesignTemplate, TemplateCategory, UserDesign


def design_tool_view(request, product_slug=None):
    """Main design tool interface"""
    product = None
    if product_slug:
        product = get_object_or_404(Product, slug=product_slug, has_design_tool=True)
    
    # Get all products with design tool enabled for product selector
    products = Product.objects.filter(has_design_tool=True, is_active=True).select_related('category')
    
    # Get template categories for dropdown
    template_categories = TemplateCategory.objects.filter(is_active=True)
    
    # Get user's saved designs if logged in
    user_designs = []
    if request.user.is_authenticated:
        user_designs = UserDesign.objects.filter(user=request.user)[:10]
    
    context = {
        'product': product,
        'products': products,
        'template_categories': template_categories,
        'user_designs': user_designs,
    }
    
    return render(request, 'design_tool/designer.html', context)


@login_required
def my_designs_view(request):
    """User's saved designs page"""
    designs = UserDesign.objects.filter(user=request.user).select_related('product')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        designs = designs.filter(
            Q(name__icontains=search_query) |
            Q(product__name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(designs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'designs': page_obj.object_list,
        'search_query': search_query,
    }
    
    return render(request, 'design_tool/my_designs.html', context)


@login_required
def load_design_view(request, design_id):
    """Load a saved design into the editor"""
    design = get_object_or_404(UserDesign, id=design_id, user=request.user)
    
    # Redirect to design tool with the product and pass design data
    url = f"/design-tool/product/{design.product.slug}/?load_design={design.id}"
    return redirect(url)


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
                'is_premium': template.is_premium,
                'category': template.category.name,
            })
        
        return JsonResponse({
            'success': True,
            'templates': template_data,
            'pagination': {
                'current_page': page,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def api_template_categories(request):
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
                'template_count': category.templates.filter(is_active=True).count()
            })
        
        return JsonResponse({
            'success': True,
            'categories': categories_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def api_product_config(request, product_id):
    """API endpoint for product canvas configuration"""
    try:
        product = Product.objects.get(id=product_id, is_active=True, has_design_tool=True)
        
        config = {
            'id': product.id,
            'name': product.name,
            'canvas': product.get_canvas_config(),
            'specifications': {
                'width_mm': product.width_mm,
                'height_mm': product.height_mm,
                'bleed_mm': product.bleed_mm,
                'safe_zone_mm': product.safe_zone_mm,
                'dpi': product.dpi,
                'minimum_quantity': product.minimum_quantity,
            }
        }
        
        return JsonResponse({
            'success': True,
            'product': config
        })
        
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Product not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_save_design(request):
    """API endpoint for saving user designs"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['name', 'product_id', 'canvas_data', 'width_mm', 'height_mm']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)
        
        # Get product
        try:
            product = Product.objects.get(id=data['product_id'], is_active=True)
        except Product.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Product not found'
            }, status=404)
        
        # Check if updating existing design
        design_id = data.get('design_id')
        if design_id:
            try:
                design = UserDesign.objects.get(id=design_id, user=request.user)
                # Update existing design
                design.name = data['name']
                design.canvas_data = data['canvas_data']
                design.width_mm = data['width_mm']
                design.height_mm = data['height_mm']
                design.bleed_mm = data.get('bleed_mm', 3.0)
                design.safe_zone_mm = data.get('safe_zone_mm', 5.0)
                design.save()
                
                action = 'updated'
            except UserDesign.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Design not found'
                }, status=404)
        else:
            # Create new design
            design = UserDesign.objects.create(
                user=request.user,
                name=data['name'],
                product=product,
                canvas_data=data['canvas_data'],
                width_mm=data['width_mm'],
                height_mm=data['height_mm'],
                bleed_mm=data.get('bleed_mm', 3.0),
                safe_zone_mm=data.get('safe_zone_mm', 5.0),
            )
            action = 'saved'
        
        # Save preview image if provided
        if 'preview_image' in data and data['preview_image']:
            try:
                # Decode base64 image
                image_data = data['preview_image'].split(',')[1]  # Remove data:image/png;base64,
                image_bytes = base64.b64decode(image_data)
                
                # Create file
                filename = f"design_{design.id}_{uuid.uuid4().hex[:8]}.png"
                design.preview_image.save(
                    filename,
                    ContentFile(image_bytes),
                    save=True
                )
            except Exception as e:
                print(f"Failed to save preview image: {e}")
        
        return JsonResponse({
            'success': True,
            'design_id': design.id,
            'message': f'Design {action} successfully',
            'action': action
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
    """API endpoint for loading a saved design"""
    try:
        design = UserDesign.objects.select_related('product').get(
            id=design_id, 
            user=request.user
        )
        
        design_data = {
            'id': design.id,
            'name': design.name,
            'canvas_data': design.canvas_data,
            'product': {
                'id': design.product.id,
                'name': design.product.name,
                'slug': design.product.slug,
            },
            'specifications': {
                'width_mm': design.width_mm,
                'height_mm': design.height_mm,
                'bleed_mm': design.bleed_mm,
                'safe_zone_mm': design.safe_zone_mm,
            },
            'created_at': design.created_at.isoformat(),
            'updated_at': design.updated_at.isoformat(),
        }
        
        return JsonResponse({
            'success': True,
            'design': design_data
        })
        
    except UserDesign.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Design not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["DELETE"])
def api_delete_design(request, design_id):
    """API endpoint for deleting a saved design"""
    try:
        design = UserDesign.objects.get(id=design_id, user=request.user)
        
        # Delete preview image file if exists
        if design.preview_image:
            try:
                design.preview_image.delete()
            except:
                pass
        
        design.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Design deleted successfully'
        })
        
    except UserDesign.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Design not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_export_design(request):
    """API endpoint for exporting design as high-resolution image"""
    try:
        data = json.loads(request.body)
        
        # Get export parameters
        image_data = data.get('image_data')  # Base64 encoded image
        format_type = data.get('format', 'png').lower()
        dpi = int(data.get('dpi', 300))
        
        if not image_data:
            return JsonResponse({
                'success': False,
                'error': 'No image data provided'
            }, status=400)
        
        # Decode base64 image
        try:
            image_bytes = base64.b64decode(image_data.split(',')[1])
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, 'white')
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            # Save to bytes
            output = io.BytesIO()
            if format_type == 'jpg' or format_type == 'jpeg':
                image.save(output, format='JPEG', quality=95, dpi=(dpi, dpi))
                content_type = 'image/jpeg'
            else:
                image.save(output, format='PNG', dpi=(dpi, dpi))
                content_type = 'image/png'
            
            output.seek(0)
            
            # Return as downloadable file
            response = HttpResponse(output.read(), content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="design_export.{format_type}"'
            return response
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Image processing failed: {str(e)}'
            }, status=500)
        
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
def api_user_designs(request):
    """API endpoint for getting user's saved designs"""
    try:
        designs = UserDesign.objects.filter(user=request.user).select_related('product')
        
        designs_data = []
        for design in designs:
            designs_data.append({
                'id': design.id,
                'name': design.name,
                'product_name': design.product.name,
                'product_slug': design.product.slug,
                'preview_image': design.preview_image.url if design.preview_image else None,
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