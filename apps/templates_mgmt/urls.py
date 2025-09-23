# apps/templates_mgmt/urls.py
from django.urls import path
from . import views

app_name = 'templates_mgmt'

urlpatterns = [
    # API endpoints
    path('templates/', views.api_templates_list, name='api_templates_list'),
    path('categories/', views.api_categories_list, name='api_categories_list'),
]

