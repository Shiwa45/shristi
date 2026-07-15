from django.contrib import admin

from .models import AutoModEvent, ModerationAction, ModerationCase, Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = [f.name for f in Report._meta.fields if f.name in
                    ("id", "reporter", "target_type", "status", "created_at")]
    list_filter = ("status",) if any(f.name == "status" for f in Report._meta.fields) else ()


@admin.register(ModerationCase)
class ModerationCaseAdmin(admin.ModelAdmin):
    list_display = [f.name for f in ModerationCase._meta.fields if f.name in
                    ("id", "subject_user", "status", "severity", "created_at")]
    list_filter = ("status",) if any(f.name == "status" for f in ModerationCase._meta.fields) else ()


for _m in (ModerationAction, AutoModEvent):
    admin.site.register(_m)
