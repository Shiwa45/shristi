# ===== URLs Configuration =====

# apps/services/urls.py - Updated for Category-Specific Pages

from django.urls import path, re_path
from . import views

app_name = 'services'

# Define allowed category slugs for validation
ALLOWED_CATEGORIES = [
    'book-printing',
    'paper-boxes', 
    'marketing-material',
    'stationery'
]

urlpatterns = [
    # Main services pages
    path('', views.services_home, name='home'),
    path('categories/', views.services_home, name='categories'),
    path('search/', views.product_search, name='search'),
    

    
    # Category pages (fallback for non-specific categories)
    path('<slug:slug>/', views.category_detail, name='category'),
    
    # Product pages
    path('<slug:category_slug>/<slug:product_slug>/', views.product_detail, name='product_detail'),
    path('<slug:category_slug>/<slug:product_slug>/static/', views.static_product_detail, name='static_product_detail'),
    
    # API endpoints
    path('api/pricing/<int:product_id>/', views.product_pricing_api, name='pricing_api'),
    path('api/category-pricing/', views.category_pricing_api, name='category_pricing_api'),
]