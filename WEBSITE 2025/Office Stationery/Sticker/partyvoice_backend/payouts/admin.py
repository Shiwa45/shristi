from django.contrib import admin

from .models import (
    KycProfile, PayoutAuditLog, PayoutMethod, PayoutPolicy, PayoutRequest,
)


@admin.register(PayoutRequest)
class PayoutRequestAdmin(admin.ModelAdmin):
    list_display = [f.name for f in PayoutRequest._meta.fields if f.name in
                    ("id", "user", "amount_diamonds", "status", "created_at")]
    list_filter = ("status",) if any(f.name == "status" for f in PayoutRequest._meta.fields) else ()
    search_fields = ("user__username",)
    # payouts are high-risk: review in admin but mutate via the service layer
    raw_id_fields = ("user",) if any(f.name == "user" for f in PayoutRequest._meta.fields) else ()


@admin.register(PayoutPolicy)
class PayoutPolicyAdmin(admin.ModelAdmin):
    list_display = [f.name for f in PayoutPolicy._meta.fields][:6]


for _m in (KycProfile, PayoutMethod, PayoutAuditLog):
    admin.site.register(_m)
