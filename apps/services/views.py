# apps/services/views.py
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import ServiceCategory, Product

def services_index(request):
    """Services listing page"""
    categories = ServiceCategory.objects.filter(is_active=True).prefetch_related('products')
    
    # Search functionality
    search_query = request.GET.get('q', '')
    if search_query:
        products = Product.objects.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query),
            is_active=True
        )
    else:
        products = Product.objects.filter(is_active=True)
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'categories': categories,
        'products': page_obj,
        'search_query': search_query,
    }
    return render(request, 'services/index.html', context)

def service_category(request, slug):
    """Category detail page"""
    category = get_object_or_404(ServiceCategory, slug=slug, is_active=True)
    products = category.products.filter(is_active=True)
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'products': page_obj,
    }
    return render(request, 'services/category.html', context)

def product_detail(request, slug):
    """Product detail page"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related_products = Product.objects.filter(
        category=product.category, 
        is_active=True
    ).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'services/product_detail.html', context)






