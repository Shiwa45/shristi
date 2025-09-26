# apps/design_tool/urls.py
from django.urls import path
from . import views

app_name = 'design_tool'

urlpatterns = [
    # Main design tool views
    path('', views.design_tool_view, name='index'),
    path('product/<slug:product_slug>/', views.design_tool_view, name='product'),
    path('my-designs/', views.my_designs_view, name='my_designs'),
    path('load/<int:design_id>/', views.load_design_view, name='load_design'),
    
    # API endpoints
    path('api/templates/', views.api_database_templates, name='api_templates'),
    path('api/categories/', views.api_template_categories, name='api_categories'),
    path('api/product/<int:product_id>/config/', views.api_product_config, name='api_product_config'),
    
    # Design management APIs
    path('api/save/', views.api_save_design, name='api_save_design'),
    path('api/load/<int:design_id>/', views.api_load_design, name='api_load_design'),
    path('api/delete/<int:design_id>/', views.api_delete_design, name='api_delete_design'),
    path('api/export/', views.api_export_design, name='api_export_design'),
    path('api/user-designs/', views.api_user_designs, name='api_user_designs'),

    # Template management APIs
    path('api/upload-svg-template/', views.api_upload_svg_template, name='api_upload_svg_template'),
    path('api/user-templates/', views.api_user_templates, name='api_user_templates'),

    # Pixabay integration
    path('api/pixabay/images/', views.api_pixabay_images, name='api_pixabay_images'),
]