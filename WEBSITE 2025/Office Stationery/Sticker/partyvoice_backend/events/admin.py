from django.contrib import admin

from .models import Event, EventMilestone, EventProgress


class MilestoneInline(admin.TabularInline):
    model = EventMilestone
    extra = 1


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [f.name for f in Event._meta.fields if f.name in
                    ("id", "code", "name", "kind", "starts_at", "ends_at", "is_active")]
    list_filter = ("is_active",) if any(f.name == "is_active" for f in Event._meta.fields) else ()
    search_fields = ("name",)
    inlines = [MilestoneInline]


admin.site.register(EventProgress)
