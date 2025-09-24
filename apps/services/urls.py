# apps/services/urls.py
from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    # Main services pages
    path('', views.services_list_view, name='list'),
    path('search/', views.products_search_view, name='search'),
    path('category/<slug:slug>/', views.category_view, name='category'),
    path('product/<slug:slug>/', views.product_detail_view, name='product_detail'),
    
    # API endpoints
    path('api/suggestions/', views.api_product_suggestions, name='api_suggestions'),
    path('api/pricing/<int:product_id>/', views.api_product_pricing, name='api_pricing'),
]