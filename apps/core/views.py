# apps/core/views.py
from django.shortcuts import render
from django.db.models import Q
from .models import HomepageSlider
from apps.services.models import ServiceCategory, Product

def home_view(request):
    """Homepage view with slider and featured products"""
    sliders = HomepageSlider.objects.filter(is_active=True).order_by('order')
    featured_products = Product.objects.filter(is_active=True, is_featured=True)[:6]
    service_categories = ServiceCategory.objects.filter(is_active=True).order_by('order')[:4]
    
    context = {
        'sliders': sliders,
        'featured_products': featured_products,
        'service_categories': service_categories,
    }
    return render(request, 'core/home.html', context)

def about_view(request):
    """About page view"""
    return render(request, 'core/about.html')

def contact_view(request):
    """Contact page view"""
    return render(request, 'core/contact.html')






