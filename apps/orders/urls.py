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
    path('quote/submit/', views.submit_quote_view, name='submit_quote'),
    path('quote/request/', views.quote_request_view, name='quote_request'),
    path('quote/<str:quote_number>/', views.quote_detail, name='quote_detail'),
    path('quotes/', views.quotes_list, name='quotes_list'),
    
    # API endpoints
    path('api/cart-count/', views.cart_count_api, name='api_cart_count'),

    # ENHANCED CART AJAX ENDPOINTS (Phase 3)
    path('api/static-product/add/<int:product_id>/', views.add_static_product_to_cart, name='add_static_product'),
    path('api/cart/update/<int:item_id>/', views.update_cart_item_ajax, name='update_cart_ajax'),
    path('api/cart/remove/<int:item_id>/', views.remove_cart_item_ajax, name='remove_cart_ajax'),
    path('api/cart/apply-coupon/', views.apply_coupon_ajax, name='apply_coupon_ajax'),
    path('api/cart/summary/', views.cart_summary_ajax, name='cart_summary_ajax'),

    # QUOTE GENERATION SYSTEM (Phase 3)
    path('api/quote/generate/', views.generate_quote_from_cart, name='generate_quote'),
    path('quote/<str:quote_number>/', views.quote_detail_view, name='quote_detail_new'),
    path('api/quote/<str:quote_number>/accept/', views.accept_quote, name='accept_quote'),
    path('quote/<str:quote_number>/download/', views.download_quote_pdf, name='download_quote_pdf'),
    
    # BOOK PRINTING ORDER SUBMISSION
    path('api/book-printing/submit/<int:product_id>/', views.submit_book_printing_order, name='submit_book_printing_order'),
]