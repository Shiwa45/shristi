# apps/core/admin.py
from django.contrib import admin
from .models import HomepageSlider

@admin.register(HomepageSlider)
class HomepageSliderAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'subtitle')
    list_editable = ('is_active', 'order')
    ordering = ('order',)


