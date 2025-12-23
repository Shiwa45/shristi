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

from apps.services.models import StaticProduct
from apps.templates_mgmt.models import DesignTemplate, TemplateCategory, UserDesign
from .models import DesignAsset
import requests
from django.utils import timezone


def design_tool_view(request, product_slug=None):
    """Main design tool interface"""
    product = None
    if product_slug:
        product = get_object_or_404(StaticProduct, slug=product_slug, design_tool_enabled=True)
    
    # Get all products with design tool enabled for product selector
    products = StaticProduct.objects.filter(design_tool_enabled=True, is_active=True).select_related('category')
    
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


def static_product_design_editor(request, category_slug, product_slug):
    """Design editor for static products"""
    # Get the static product
    static_product = get_object_or_404(
        StaticProduct,
        slug=product_slug,
        category__slug=category_slug,
        design_tool_enabled=True,
        is_active=True
    )

    # Get design templates for this product
    from apps.templates_mgmt.models import StaticProductTemplate
    design_templates = StaticProductTemplate.objects.filter(
        static_product=static_product,
        is_active=True
    ).order_by('order', 'name')

    # Get user's saved designs for this product
    user_designs = []
    if request.user.is_authenticated:
        user_designs = UserDesign.objects.filter(
            user=request.user,
            static_product=static_product
        ).order_by('-updated_at')[:10]

    # Calculate canvas dimensions (convert mm to pixels at 300 DPI)
    canvas_width = int(static_product.width_mm * 11.811)  # mm to px at 300 DPI
    canvas_height = int(static_product.height_mm * 11.811)

    context = {
        'static_product': static_product,
        'design_templates': design_templates,
        'user_designs': user_designs,
        'canvas_width': canvas_width,
        'canvas_height': canvas_height,
        'product_options': {
            'base_price': str(static_product.base_price),
            'minimum_quantity': static_product.minimum_quantity,
        }
    }

    return render(request, 'design_tool/static_product_editor.html', context)


@login_required
@require_http_methods(["POST"])
def save_design_ajax(request):
    """Save user design via AJAX"""
    try:
        data = json.loads(request.body)

        static_product = get_object_or_404(StaticProduct, id=data.get('product_id'))

        # Create or update design
        design_id = data.get('design_id')
        if design_id:
            design = get_object_or_404(UserDesign, id=design_id, user=request.user)
        else:
            design = UserDesign(user=request.user, static_product=static_product)

        design.name = data.get('name', f'Design {timezone.now().strftime("%Y%m%d_%H%M%S")}')
        design.canvas_data = data.get('canvas_data', {})
        design.width_mm = static_product.width_mm
        design.height_mm = static_product.height_mm
        design.save()

        # Generate thumbnail if canvas data is provided
        if data.get('thumbnail_data'):
            import base64
            from django.core.files.base import ContentFile

            # Remove data URL prefix
            format, imgstr = data['thumbnail_data'].split(';base64,')
            ext = format.split('/')[-1]

            thumbnail_data = ContentFile(
                base64.b64decode(imgstr),
                name=f'design_{design.id}_thumb.{ext}'
            )
            design.preview_image.save(
                f'design_{design.id}_thumb.{ext}',
                thumbnail_data,
                save=True
            )

        return JsonResponse({
            'success': True,
            'design_id': design.id,
            'message': 'Design saved successfully',
            'thumbnail_url': design.preview_image.url if design.preview_image else None
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def load_design_ajax(request, design_id):
    """Load user design via AJAX"""
    try:
        design = get_object_or_404(UserDesign, id=design_id, user=request.user)

        return JsonResponse({
            'success': True,
            'design_data': design.canvas_data,
            'name': design.name,
            'product_id': design.static_product.id,
            'product_name': design.static_product.name
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["GET"])
def load_template_ajax(request, template_id):
    """Load design template via AJAX"""
    try:
        from apps.templates_mgmt.models import StaticProductTemplate
        template = get_object_or_404(StaticProductTemplate, id=template_id, is_active=True)

        # Increment usage count
        template.increment_usage()

        return JsonResponse({
            'success': True,
            'template_data': template.template_data,
            'name': template.name,
            'product_id': template.static_product.id
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


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
def api_unsplash_images(request):
    """API endpoint for Unsplash image search"""
    try:
        unsplash_access_key = getattr(settings, 'UNSPLASH_ACCESS_KEY', None)
        if not unsplash_access_key:
            return JsonResponse({
                'success': False,
                'error': 'Unsplash access key not configured'
            }, status=500)

        query = request.GET.get('q', 'business')
        page = max(int(request.GET.get('page', 1)), 1)
        per_page = min(int(request.GET.get('per_page', 12)), 30)  # Unsplash max is 30
        orientation = request.GET.get('orientation', '')

        params = {
            'query': query,
            'page': page,
            'per_page': per_page,
            'order_by': 'relevant'
        }
        if orientation:
            params['orientation'] = orientation

        headers = {'Authorization': f'Client-ID {unsplash_access_key}'}
        response = requests.get('https://api.unsplash.com/search/photos', headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        images = []
        for photo in data.get('results', []):
            urls = photo.get('urls', {}) or {}
            user = photo.get('user', {}) or {}
            links = photo.get('links', {}) or {}
            images.append({
                'id': photo.get('id'),
                'preview_url': urls.get('small') or urls.get('thumb'),
                'thumbnail_url': urls.get('thumb') or urls.get('small'),
                'large_url': urls.get('regular') or urls.get('full') or urls.get('raw'),
                'tags': photo.get('alt_description') or photo.get('description') or '',
                'user': user.get('name'),
                'user_url': (user.get('links') or {}).get('html') if user else None,
                'source_page': links.get('html'),
                'downloads': photo.get('downloads'),
                'likes': photo.get('likes'),
                'width': photo.get('width'),
                'height': photo.get('height'),
            })

        return JsonResponse({
            'success': True,
            'images': images,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_hits': data.get('total', 0),
                'total_pages': (data.get('total', 0) + per_page - 1) // per_page
            }
        })

    except requests.RequestException as e:
        return JsonResponse({
            'success': False,
            'error': f'Unsplash API error: {str(e)}'
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def api_pexels_images(request):
    """API endpoint for Pexels image search"""
    try:
        pexels_api_key = getattr(settings, 'PEXELS_API_KEY', None)
        if not pexels_api_key:
            return JsonResponse({
                'success': False,
                'error': 'Pexels API key not configured'
            }, status=500)

        query = request.GET.get('q', 'business')
        page = max(int(request.GET.get('page', 1)), 1)
        per_page = min(int(request.GET.get('per_page', 12)), 80)  # Pexels max is 80
        orientation = request.GET.get('orientation', '')

        params = {
            'query': query,
            'page': page,
            'per_page': per_page
        }
        if orientation:
            params['orientation'] = orientation

        headers = {'Authorization': pexels_api_key}
        response = requests.get('https://api.pexels.com/v1/search', headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        images = []
        for photo in data.get('photos', []):
            src = photo.get('src', {}) or {}
            images.append({
                'id': photo.get('id'),
                'preview_url': src.get('medium') or src.get('small'),
                'thumbnail_url': src.get('small') or src.get('tiny'),
                'large_url': src.get('large') or src.get('large2x') or src.get('original'),
                'tags': photo.get('alt') or '',
                'user': photo.get('photographer'),
                'user_url': photo.get('photographer_url'),
                'source_page': photo.get('url'),
                'width': photo.get('width'),
                'height': photo.get('height'),
            })

        return JsonResponse({
            'success': True,
            'images': images,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_hits': data.get('total_results', len(images)),
                'total_pages': (data.get('total_results', len(images)) + per_page - 1) // per_page
            }
        })

    except requests.RequestException as e:
        return JsonResponse({
            'success': False,
            'error': f'Pexels API error: {str(e)}'
        }, status=500)
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


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_upload_svg_template(request):
    """API endpoint for uploading SVG templates"""
    try:
        if 'svg_file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No SVG file provided'
            }, status=400)

        svg_file = request.FILES['svg_file']
        name = request.POST.get('name', svg_file.name)
        category_id = request.POST.get('category_id')
        width_mm = float(request.POST.get('width_mm', 90))
        height_mm = float(request.POST.get('height_mm', 54))

        # Validate file type
        if not svg_file.name.lower().endswith('.svg'):
            return JsonResponse({
                'success': False,
                'error': 'Only SVG files are allowed'
            }, status=400)

        # Get or create default category
        if category_id:
            try:
                category = TemplateCategory.objects.get(id=category_id)
            except TemplateCategory.DoesNotExist:
                category, created = TemplateCategory.objects.get_or_create(
                    slug='user-uploads',
                    defaults={'name': 'User Uploads', 'description': 'User uploaded templates'}
                )
        else:
            category, created = TemplateCategory.objects.get_or_create(
                slug='user-uploads',
                defaults={'name': 'User Uploads', 'description': 'User uploaded templates'}
            )

        # Create design template
        template = DesignTemplate.objects.create(
            name=name,
            category=category,
            width_mm=width_mm,
            height_mm=height_mm,
            bleed_mm=3.0,
            safe_zone_mm=5.0,
        )

        # Save SVG file
        template.svg_file.save(
            f"template_{template.id}_{svg_file.name}",
            svg_file,
            save=True
        )

        # Create asset record for user
        asset = DesignAsset.objects.create(
            user=request.user,
            name=name,
            asset_type='template',
            file=template.svg_file,
            file_size=svg_file.size,
            mime_type='image/svg+xml',
            metadata={
                'width_mm': width_mm,
                'height_mm': height_mm,
                'template_id': template.id
            }
        )

        return JsonResponse({
            'success': True,
            'template_id': template.id,
            'asset_id': asset.id,
            'message': 'SVG template uploaded successfully',
            'template': {
                'id': template.id,
                'name': template.name,
                'svg_url': template.svg_file.url,
                'category': template.category.name,
                'width_mm': template.width_mm,
                'height_mm': template.height_mm,
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def api_pixabay_images(request):
    """API endpoint for Pixabay image search"""
    try:
        # Get Pixabay API key from settings
        pixabay_api_key = getattr(settings, 'PIXABAY_API_KEY', None)
        if not pixabay_api_key or pixabay_api_key == 'your-pixabay-api-key':
            return JsonResponse({
                'success': False,
                'error': 'Pixabay API key not configured'
            }, status=500)

        # Get search parameters
        query = request.GET.get('q', 'business')
        page = int(request.GET.get('page', 1))
        per_page = min(int(request.GET.get('per_page', 12)), 50)  # Pixabay max is 50
        category = request.GET.get('category', '')
        image_type = request.GET.get('image_type', 'photo')
        orientation = request.GET.get('orientation', 'all')

        # Build Pixabay API URL
        pixabay_url = "https://pixabay.com/api/"
        params = {
            'key': pixabay_api_key,
            'q': query,
            'image_type': image_type,
            'orientation': orientation,
            'category': category,
            'page': page,
            'per_page': per_page,
            'safesearch': 'true',
            'order': 'popular'
        }

        # Remove empty parameters
        params = {k: v for k, v in params.items() if v}

        # Make request to Pixabay
        response = requests.get(pixabay_url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Format images for frontend
        images = []
        for img in data.get('hits', []):
            images.append({
                'id': img['id'],
                'preview_url': img['webformatURL'],
                'thumbnail_url': img['previewURL'],
                'large_url': img['largeImageURL'],
                'tags': img['tags'],
                'user': img['user'],
                'downloads': img['downloads'],
                'likes': img['likes'],
                'views': img['views'],
                'width': img['imageWidth'],
                'height': img['imageHeight'],
                'size': img['imageSize']
            })

        return JsonResponse({
            'success': True,
            'images': images,
            'pagination': {
                'current_page': page,
                'total_hits': data.get('totalHits', 0),
                'per_page': per_page,
                'total_pages': (data.get('totalHits', 0) + per_page - 1) // per_page
            }
        })

    except requests.RequestException as e:
        return JsonResponse({
            'success': False,
            'error': f'Pixabay API error: {str(e)}',
            'cliparts': [],
            'pagination': {'current_page': 1, 'per_page': per_page, 'total_hits': 0, 'total_pages': 0}
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'cliparts': [],
            'pagination': {'current_page': 1, 'per_page': per_page, 'total_hits': 0, 'total_pages': 0}
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_user_templates(request):
    """API endpoint for user's uploaded templates"""
    try:
        # Get user's uploaded templates through DesignAsset
        assets = DesignAsset.objects.filter(
            user=request.user,
            asset_type='template'
        ).order_by('-created_at')

        templates_data = []
        for asset in assets:
            template_id = asset.metadata.get('template_id')
            if template_id:
                try:
                    template = DesignTemplate.objects.get(id=template_id)
                    templates_data.append({
                        'id': template.id,
                        'name': template.name,
                        'thumbnail': template.thumbnail.url if template.thumbnail else None,
                        'svg_file': template.svg_file.url if template.svg_file else None,
                        'json_data': template.json_data,
                        'preview_image': template.preview_image.url if template.preview_image else None,
                        'width_mm': template.width_mm,
                        'height_mm': template.height_mm,
                        'bleed_mm': template.bleed_mm,
                        'safe_zone_mm': template.safe_zone_mm,
                        'category': template.category.name,
                        'created_at': asset.created_at.isoformat(),
                        'usage_count': asset.usage_count,
                    })
                except DesignTemplate.DoesNotExist:
                    continue

        return JsonResponse({
            'success': True,
            'templates': templates_data
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def api_pixabay_cliparts(request):
    """API endpoint for Pixabay vector/illustration search for cliparts"""
    try:
        pixabay_api_key = getattr(settings, 'PIXABAY_API_KEY', None)
        if not pixabay_api_key:
            return JsonResponse({
                'success': False,
                'error': 'Pixabay API key not configured'
            }, status=500)

        query = request.GET.get('q', 'icon')
        page = max(int(request.GET.get('page', 1)), 1)
        per_page = min(int(request.GET.get('per_page', 12)), 50)
        orientation = request.GET.get('orientation', 'all')

        params = {
            'key': pixabay_api_key,
            'q': query,
            'page': page,
            'per_page': per_page,
            'image_type': 'vector',
            'orientation': orientation,
            'safesearch': 'true',
            'order': 'popular'
        }

        response = requests.get('https://pixabay.com/api/', params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        cliparts = []
        for img in data.get('hits', []):
            cliparts.append({
                'id': img.get('id'),
                'preview_url': img.get('previewURL'),
                'thumbnail_url': img.get('previewURL'),
                'large_url': img.get('vectorURL') or img.get('largeImageURL') or img.get('imageURL'),
                'tags': img.get('tags'),
                'user': img.get('user'),
                'views': img.get('views'),
                'downloads': img.get('downloads'),
                'likes': img.get('likes'),
                'width': img.get('imageWidth'),
                'height': img.get('imageHeight')
            })

        return JsonResponse({
            'success': True,
            'cliparts': cliparts,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_hits': data.get('totalHits', 0),
                'total_pages': (data.get('totalHits', 0) + per_page - 1) // per_page
            }
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
