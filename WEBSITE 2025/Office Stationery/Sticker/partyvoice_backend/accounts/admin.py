from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "level", "gender")
    search_fields = ("user__username", "display_name")
    raw_id_fields = ("user",)
