# apps/orders/urls.py
from django.urls import path
from . import views
from .cart_views import AddToCartView
from .checkout_views import (
    CheckoutView, CheckoutShippingView, CheckoutPaymentView, CheckoutConfirmView, CheckoutSuccessView
)

app_name = 'orders'

urlpatterns = [
    # Cart URLs
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/<int:product_id>/', AddToCartView.as_view(), name='add_to_cart'),
    path('cart/update/', views.UpdateCartView.as_view(), name='update_cart'),
    path('cart/remove/<int:item_id>/', views.RemoveFromCartView.as_view(), name='remove_from_cart'),
    path('cart/apply-coupon/', views.ApplyCouponView.as_view(), name='apply_coupon'),
    path('cart/count/', views.cart_count_api, name='cart_count_api'),
    
    # Checkout URLs (to be implemented next)
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('checkout/shipping/', CheckoutShippingView.as_view(), name='checkout_shipping'),
    path('checkout/payment/', CheckoutPaymentView.as_view(), name='checkout_payment'),
    path('checkout/confirm/', CheckoutConfirmView.as_view(), name='checkout_confirm'),
    path('checkout/success/<str:order_number>/', CheckoutSuccessView.as_view(), name='checkout_success'),
    
    # Order management URLs
    path('', views.orders_index, name='index'),
    path('history/', views.orders_index, name='history'),  # Alias for orders index
    path('order/<str:order_number>/', views.order_detail, name='detail'),
    path('order/<str:order_number>/cancel/', views.cancel_order, name='cancel_order'),
    
    # Quote URLs
    path('quote/request/', views.quote_request_view, name='quote_request'),
    path('quote/<str:quote_number>/', views.quote_detail, name='quote_detail'),
    path('quotes/', views.quotes_list, name='quotes_list'),
    
    # API endpoints
    path('api/cart-count/', views.cart_count_api, name='api_cart_count'),
]