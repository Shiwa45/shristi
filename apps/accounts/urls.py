# apps/accounts/urls.py
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
    path('profile/', views.profile_view, name='profile'),
    path('ajax-login/', views.ajax_login_view, name='ajax_login'),
    path('ajax-register/', views.ajax_register_view, name='ajax_register'),
    path('ajax-verify-otp/', views.ajax_verify_otp_view, name='ajax_verify_otp'),
    path('ajax-resend-otp/', views.ajax_resend_otp_view, name='ajax_resend_otp'),
]
