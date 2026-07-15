from django.contrib import admin

from .mentorship import Mentorship
from .weddings import Marriage, Ring


@admin.register(Ring)
class RingAdmin(admin.ModelAdmin):
    list_display = [f.name for f in Ring._meta.fields][:6]


admin.site.register(Marriage)
admin.site.register(Mentorship)
