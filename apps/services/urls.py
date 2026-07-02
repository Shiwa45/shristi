# ===== URLs Configuration =====

# apps/services/urls.py - Updated for Category-Specific Pages

from django.urls import path, re_path
from . import views
from . import pricing_admin_views

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
    path('all-products/', views.all_products, name='all_products'),
    path('search/', views.product_search, name='search'),

    # Pricing Manager (staff-only, clean UI for updating prices)
    path('manage/pricing/', pricing_admin_views.pricing_home, name='pricing_home'),
    path('manage/pricing/products/', pricing_admin_views.pricing_products, name='pricing_products'),
    path('manage/pricing/products/<int:product_id>/', pricing_admin_views.pricing_product_edit, name='pricing_product_edit'),
    path('manage/pricing/book-printing/', pricing_admin_views.pricing_book, name='pricing_book'),

    # Category pages (fallback for non-specific categories)
    path('<slug:slug>/', views.category_detail, name='category'),
    
    # Product pages
    path('<slug:category_slug>/<slug:product_slug>/', views.product_detail, name='product_detail'),
    path('<slug:category_slug>/<slug:product_slug>/static/', views.static_product_detail, name='static_product_detail'),
    
    # API endpoints
    path('api/pricing/<int:product_id>/', views.product_pricing_api, name='pricing_api'),
    path('api/category-pricing/', views.category_pricing_api, name='category_pricing_api'),
]