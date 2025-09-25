# shirsti_printing/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('accounts/', include('apps.accounts.urls')),
    # path('auth/', include('allauth.urls')),
    path('services/', include('apps.services.urls')),
    path('design-tool/', include('apps.design_tool.urls')),
    path('orders/', include('apps.orders.urls')),
    path('api/', include('apps.templates_mgmt.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])