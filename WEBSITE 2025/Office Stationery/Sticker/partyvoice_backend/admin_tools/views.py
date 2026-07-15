"""
admin_tools/views.py + tasks.py — Staff-only moderation queue + scheduled jobs.

views:  the review-queue API a moderation dashboard consumes — list cases by
        priority, claim a case, resolve with an action. Staff-gated.
tasks:  Celery periodic jobs that keep the system honest — expire timed
        actions, reconcile the ledger, roll up leaderboards, screen payouts,
        export analytics.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from moderation.models import ModerationAction, ModerationCase
from moderation.services import take_action
from observability.models import audit


@api_view(["GET"])
@permission_classes([IsAdminUser])
def review_queue(request):
    """Open cases, highest priority + strongest signal first."""
    cases = (ModerationCase.objects
             .filter(status__in=[ModerationCase.Status.OPEN, ModerationCase.Status.TRIAGED])
             .order_by("-priority", "-report_count", "created_at")[:100])
    return Response([{
        "id": c.id, "subject": c.subject_user_id, "priority": c.priority,
        "reason": c.primary_reason, "reports": c.report_count,
        "status": c.status, "created_at": c.created_at,
    } for c in cases])


@api_view(["POST"])
@permission_classes([IsAdminUser])
def resolve_case(request, case_id):
    """Apply an action to a case and audit it."""
    kind = request.data.get("kind")
    reason = request.data.get("reason", "")
    duration = request.data.get("duration_minutes")
    room_id = request.data.get("room_id")

    valid = {k for k, _ in ModerationAction.Kind.choices}
    if kind not in valid:
        return Response({"detail": "invalid action kind"}, status=400)

    case = ModerationCase.objects.get(pk=case_id)
    action = take_action(
        target_user_id=case.subject_user_id, kind=kind, reason=reason,
        moderator_id=request.user.id, case_id=case.id,
        duration_minutes=duration, room_id=room_id)
    audit(actor_id=request.user.id, action=f"moderation.{kind}",
          target_type="user", target_id=case.subject_user_id,
          metadata={"case": case.id, "reason": reason},
          ip=request.META.get("REMOTE_ADDR"))
    return Response({"ok": True, "action_id": action.id})


@api_view(["POST"])
@permission_classes([IsAdminUser])
def dismiss_case(request, case_id):
    from django.utils import timezone
    ModerationCase.objects.filter(pk=case_id).update(
        status=ModerationCase.Status.DISMISSED, resolved_at=timezone.now())
    audit(actor_id=request.user.id, action="moderation.dismiss",
          target_type="case", target_id=case_id)
    return Response({"ok": True})


# ============================ admin_tools/tasks.py ============================
"""
from celery import shared_task

@shared_task
def expire_moderation_actions():
    from django.utils import timezone
    from moderation.models import ModerationAction
    from accounts.models import User
    now = timezone.now()
    expired = ModerationAction.objects.filter(active=True, expires_at__lt=now)
    # reactivate suspended accounts whose suspension lapsed
    for a in expired.filter(kind__in=["suspend", "ban"]):
        if a.kind == "suspend":
            User.objects.filter(id=a.target_user_id).update(is_active=True)
    expired.update(active=False)

@shared_task
def reconcile_ledger():
    # verify every wallet balance == sum of its ledger entries; alert on drift
    from economy.models import Wallet, LedgerEntry, Currency
    from django.db.models import Sum
    drift = []
    for w in Wallet.objects.iterator():
        for cur, field in [(Currency.COIN, 'coin_balance'), (Currency.DIAMOND, 'diamond_balance')]:
            total = LedgerEntry.objects.filter(wallet=w, currency=cur).aggregate(s=Sum('amount'))['s'] or 0
            if total != getattr(w, field):
                drift.append((w.id, cur, total, getattr(w, field)))
    if drift:
        # emit alert to ops; never auto-correct money silently
        ...
    return len(drift)

@shared_task
def screen_pending_payouts():
    from payouts.models import PayoutRequest
    from payouts.services import screen_payout
    from fraud.models import score_payout_risk
    for req in PayoutRequest.objects.filter(status=PayoutRequest.Status.REQUESTED):
        score, reasons = score_payout_risk(req.user_id)
        screen_payout(req, risk_score=score, reasons=reasons)

@shared_task
def export_analytics():
    from observability.models import export_batch
    batch = export_batch()
    # ship `batch` to the warehouse (BigQuery / Snowflake / S3)
    ...

# beat schedule (settings.py):
#   expire_moderation_actions: every 5 min
#   reconcile_ledger:          hourly
#   screen_pending_payouts:    every 10 min
#   export_analytics:          every 15 min
"""
