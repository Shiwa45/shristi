# apps/services/urls.py
from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    path('', views.services_index, name='index'),
    path('category/<slug:slug>/', views.service_category, name='category'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
]

