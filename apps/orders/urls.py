# apps/orders/urls.py
from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.orders_index, name='index'),
    path('<str:order_number>/', views.order_detail, name='detail'),
]
