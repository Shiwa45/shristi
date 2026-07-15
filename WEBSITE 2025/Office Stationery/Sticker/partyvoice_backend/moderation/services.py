"""
moderation/services.py — Report intake, triage, and enforcement.

file_report():       creates a Report and folds it into an open ModerationCase
                     for the subject (dedup by subject+reason), bumping priority
                     for critical categories and accumulating report_count.
take_action():       issues a ModerationAction and applies its side effects
                     (e.g. account ban sets a flag, room ban writes RoomBan).
is_user_restricted(): central check used across the app before sensitive ops.
ingest_automod():     records an automated hit and auto-actions on high-confidence
                     critical categories (minor safety, etc.).
"""

from django.db import transaction as db_txn
from django.db.models import F
from django.utils import timezone

from .models import (
    AutoModEvent, ModerationAction, ModerationCase, Report,
)


# reasons that escalate a case to CRITICAL priority and may auto-action
CRITICAL_REASONS = {
    Report.Reason.MINOR_SAFETY, Report.Reason.SELF_HARM, Report.Reason.VIOLENCE,
}


class ModerationError(Exception):
    pass


@db_txn.atomic
def file_report(*, reporter_id, target_type, target_ref, reported_user_id,
                reason, detail="", evidence_refs=None) -> Report:
    report = Report.objects.create(
        reporter_id=reporter_id, target_type=target_type, target_ref=target_ref,
        reported_user_id=reported_user_id, reason=reason, detail=detail,
        evidence_refs=evidence_refs or [])

    if reported_user_id:
        case = ModerationCase.objects.select_for_update().filter(
            subject_user_id=reported_user_id,
            status__in=[ModerationCase.Status.OPEN, ModerationCase.Status.TRIAGED],
        ).first()
        priority = (ModerationCase.Priority.CRITICAL if reason in CRITICAL_REASONS
                    else ModerationCase.Priority.NORMAL)
        if case:
            case.report_count = F("report_count") + 1
            if priority > case.priority:
                case.priority = priority
            case.save(update_fields=["report_count", "priority"])
            case.refresh_from_db()
        else:
            case = ModerationCase.objects.create(
                subject_user_id=reported_user_id, primary_reason=reason,
                priority=priority, report_count=1)
        case.reports.add(report)

    return report


@db_txn.atomic
def take_action(*, target_user_id, kind, reason, moderator_id=None,
                case_id=None, duration_minutes=None, room_id=None,
                is_automated=False) -> ModerationAction:
    expires = (timezone.now() + timezone.timedelta(minutes=duration_minutes)
               if duration_minutes else None)

    action = ModerationAction.objects.create(
        case_id=case_id, target_user_id=target_user_id, kind=kind, reason=reason,
        expires_at=expires, moderator_id=moderator_id, is_automated=is_automated)

    # side effects per action kind
    if kind == ModerationAction.Kind.BAN:
        _set_account_banned(target_user_id, True)
    elif kind == ModerationAction.Kind.SUSPEND:
        _set_account_banned(target_user_id, True)  # cleared by expiry job
    elif kind == ModerationAction.Kind.ROOM_BAN and room_id:
        from rooms.models import Room, RoomBan
        room = Room.objects.filter(room_id=room_id).first()
        if room:
            RoomBan.objects.get_or_create(
                room=room, user_id=target_user_id, defaults={"created_by_id": moderator_id})

    if case_id:
        ModerationCase.objects.filter(pk=case_id).update(
            status=ModerationCase.Status.ACTIONED, resolved_at=timezone.now())

    return action


def _set_account_banned(user_id, value: bool):
    from accounts.models import User
    User.objects.filter(id=user_id).update(is_active=not value)


def is_user_restricted(user_id) -> dict:
    """
    Central gate. Returns active restrictions so callers (room join, gifting,
    posting) can enforce them. Expired timed actions are treated as inactive.
    """
    now = timezone.now()
    actions = ModerationAction.objects.filter(
        target_user_id=user_id, active=True
    ).exclude(expires_at__lt=now)
    kinds = set(a.kind for a in actions)
    return {
        "banned": ModerationAction.Kind.BAN in kinds or ModerationAction.Kind.SUSPEND in kinds,
        "muted": ModerationAction.Kind.MUTE in kinds,
        "shadow": ModerationAction.Kind.SHADOW in kinds,
        "kinds": list(kinds),
    }


@db_txn.atomic
def ingest_automod(*, user_id, channel, category, score, context_ref="",
                   auto_action_threshold=0.9) -> AutoModEvent:
    """
    Record an automated moderation hit. On high-confidence critical categories,
    auto-action (mute) and open a CRITICAL case for human review — automation
    acts fast but a human confirms, never the reverse.
    """
    event = AutoModEvent.objects.create(
        user_id=user_id, channel=channel, category=category, score=score,
        context_ref=context_ref)

    critical = category in ("minor_safety", "sexual", "self_harm", "violence", "hate")
    if critical and score >= auto_action_threshold:
        take_action(
            target_user_id=user_id, kind=ModerationAction.Kind.MUTE,
            reason=f"Auto-mod: {category} (score {score:.2f})",
            duration_minutes=60, is_automated=True)
        case = ModerationCase.objects.create(
            subject_user_id=user_id, primary_reason="other",
            priority=ModerationCase.Priority.CRITICAL, report_count=0)
        event.auto_actioned = True
        event.save(update_fields=["auto_actioned"])
    return event
