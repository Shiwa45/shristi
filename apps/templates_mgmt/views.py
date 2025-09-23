# apps/templates_mgmt/views.py
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import DesignTemplate, TemplateCategory

def api_templates_list(request):
    """API endpoint for templates list"""
    try:
        # Get pagination parameters
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 12))
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
                'category': template.category.name,
                'is_premium': template.is_premium,
            })
        
        return JsonResponse({
            'success': True,
            'results': template_data,
            'count': paginator.count,
            'page': page,
            'pages': paginator.num_pages,
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def api_categories_list(request):
    """API endpoint for categories list"""
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