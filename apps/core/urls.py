# apps/core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('contact/submit/', views.contact_submit_view, name='contact_submit'),
    path('page/<slug:slug>/', views.page_view, name='page'),
    path('faq/', views.faq_view, name='faq'),
]