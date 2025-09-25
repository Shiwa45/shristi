# apps/services/urls.py - Complete Updated Version

from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    # Main service pages
    path('', views.service_categories_view, name='categories'),
    path('category/<slug:slug>/', views.category_products_view, name='category'),
    path('product/<slug:slug>/', views.product_detail_view, name='product_detail'),
    
    # Search functionality
    path('search/', views.product_search, name='product_search'),
    
    # API endpoints for dynamic pricing and options
    path('api/pricing/<int:product_id>/', views.api_product_pricing, name='api_pricing'),
    path('api/options/<int:product_id>/', views.api_product_options, name='api_options'),
    path('api/paper-options/<int:product_id>/', views.get_paper_options, name='api_paper_options'),
    path('api/color-options/<int:product_id>/', views.get_color_options, name='api_color_options'),
    
    # Bulk pricing calculator
    path('api/bulk-pricing/<int:product_id>/', views.api_bulk_pricing, name='api_bulk_pricing'),
    
    # Quote request handling
    path('api/quote-request/', views.api_quote_request, name='api_quote_request'),
    
    # Shipping calculation
    path('api/shipping-cost/', views.api_shipping_cost, name='api_shipping_cost'),
]