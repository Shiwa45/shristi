# apps/design_tool/urls.py
from django.urls import path
from . import views

app_name = 'design_tool'

urlpatterns = [
    # Main design tool views
    path('', views.design_tool_view, name='index'),
    path('product/<slug:product_slug>/', views.design_tool_view, name='product'),

    # Static product design editor (NEW)
    path('editor/<slug:category_slug>/<slug:product_slug>/', views.static_product_design_editor, name='editor'),

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

    # NEW Static Product Design APIs
    path('api/static/save/', views.save_design_ajax, name='save_design_ajax'),
    path('api/static/load/<int:design_id>/', views.load_design_ajax, name='load_design_ajax'),
    path('api/static/template/<int:template_id>/', views.load_template_ajax, name='load_template_ajax'),

    # Template management APIs
    path('api/upload-svg-template/', views.api_upload_svg_template, name='api_upload_svg_template'),
    path('api/user-templates/', views.api_user_templates, name='api_user_templates'),

    # Pixabay integration
    path('api/pixabay/images/', views.api_pixabay_images, name='api_pixabay_images'),
    path('api/pixabay/cliparts/', views.api_pixabay_cliparts, name='api_pixabay_cliparts'),
    path('api/unsplash/images/', views.api_unsplash_images, name='api_unsplash_images'),
    path('api/pexels/images/', views.api_pexels_images, name='api_pexels_images'),
]
