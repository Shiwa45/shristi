# apps/design_tool/urls.py
from django.urls import path
from . import views

app_name = 'design_tool'

urlpatterns = [
    # Main design tool interface
    path('', views.design_tool_view, name='index'),
    path('product/<slug:product_slug>/', views.design_tool_view, name='product_designer'),
    
    # API endpoints
    path('api/database-templates/', views.api_database_templates, name='api_database_templates'),
    path('api/search/pixabay/', views.api_search_pixabay, name='api_search_pixabay'),
    path('api/save-design/', views.api_save_design, name='api_save_design'),
    path('api/load-design/<int:design_id>/', views.api_load_design, name='api_load_design'),
    path('api/user-designs/', views.api_user_designs, name='api_user_designs'),
    path('api/products/', views.api_products, name='api_products'),
    path('api/categories/', views.api_categories, name='api_categories'),
]