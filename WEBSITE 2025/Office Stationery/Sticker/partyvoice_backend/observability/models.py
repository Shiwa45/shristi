"""
observability/models.py + services.py — Audit log + analytics events.

AuditLog:       immutable record of privileged/sensitive actions (mod actions,
                payouts, role changes, config edits) for compliance + forensics.
AnalyticsEvent: lightweight product-analytics events (session, room_join,
                gift_sent, purchase...) buffered for batch export to a
                warehouse. Kept separate from AuditLog (different retention,
                different access controls).
"""

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Append-only. No update/delete in app code; partition/rotate at the DB."""
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="audit_entries")
    action = models.CharField(max_length=60, db_index=True)     # e.g. "payout.approve"
    target_type = models.CharField(max_length=40, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["action", "-created_at"]),
                   models.Index(fields=["target_type", "target_id"])]


class AnalyticsEvent(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="analytics_events")
    name = models.CharField(max_length=50, db_index=True)
    props = models.JSONField(default=dict, blank=True)
    session_id = models.CharField(max_length=64, blank=True, db_index=True)
    exported = models.BooleanField(default=False, db_index=True)  # batch export flag
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["name", "-created_at"]),
                   models.Index(fields=["exported", "created_at"])]


# ----------------------------- services -----------------------------

def audit(*, actor_id, action, target_type="", target_id="", metadata=None, ip=None):
    """Write an audit entry. Call from every privileged code path."""
    return AuditLog.objects.create(
        actor_id=actor_id, action=action, target_type=target_type,
        target_id=str(target_id), metadata=metadata or {}, ip=ip)


def track(*, user_id, name, props=None, session_id=""):
    """Record a product-analytics event (fire-and-forget; batch-exported)."""
    return AnalyticsEvent.objects.create(
        user_id=user_id, name=name, props=props or {}, session_id=session_id)


def export_batch(limit=5000):
    """
    Pull a batch of unexported events for shipping to the warehouse
    (called by a periodic Celery task). Marks them exported on success.
    Returns the list of dicts to ship.
    """
    from django.db import transaction
    with transaction.atomic():
        rows = list(AnalyticsEvent.objects.select_for_update(skip_locked=True)
                    .filter(exported=False).order_by("created_at")[:limit])
        if not rows:
            return []
        ids = [r.id for r in rows]
        AnalyticsEvent.objects.filter(id__in=ids).update(exported=True)
    return [{"id": r.id, "user_id": r.user_id, "name": r.name,
             "props": r.props, "session_id": r.session_id,
             "ts": r.created_at.isoformat()} for r in rows]
