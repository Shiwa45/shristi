"""
moderation/models.py — Trust & Safety core.

Covers the reporting -> review -> action pipeline plus the moderation-action
ledger. A live-voice product with minors and real money present makes this a
first-class, legally-required workstream.

Report:           user-submitted flags against users/rooms/posts/messages.
ModerationCase:   a triaged unit of work for human/automated review.
ModerationAction: an enforcement act (warn/mute/kick/ban tiers) with audit.
AutoModEvent:     records of automated moderation hits (audio/text/image).
"""

from django.conf import settings
from django.db import models


class Report(models.Model):
    class Target(models.TextChoices):
        USER = "user", "User"
        ROOM = "room", "Room"
        POST = "post", "Post"
        MESSAGE = "message", "Message"

    class Reason(models.TextChoices):
        HARASSMENT = "harassment", "Harassment / bullying"
        HATE = "hate", "Hate speech"
        SEXUAL = "sexual", "Sexual content"
        MINOR_SAFETY = "minor_safety", "Minor safety"
        SCAM = "scam", "Scam / fraud"
        SELF_HARM = "self_harm", "Self-harm"
        VIOLENCE = "violence", "Violence / threats"
        SPAM = "spam", "Spam"
        OTHER = "other", "Other"

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="reports_made")
    target_type = models.CharField(max_length=10, choices=Target.choices, db_index=True)
    target_ref = models.CharField(max_length=64, db_index=True)  # public_id / room_id / post id
    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="reports_against")

    reason = models.CharField(max_length=15, choices=Reason.choices, db_index=True)
    detail = models.CharField(max_length=500, blank=True)
    # evidence references (clip ids, screenshots in object storage) — never inline PII
    evidence_refs = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["reason", "-created_at"]),
                   models.Index(fields=["reported_user", "-created_at"])]


class ModerationCase(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        TRIAGED = "triaged", "Triaged"
        ACTIONED = "actioned", "Actioned"
        DISMISSED = "dismissed", "Dismissed"

    class Priority(models.IntegerChoices):
        LOW = 0, "Low"
        NORMAL = 1, "Normal"
        HIGH = 2, "High"
        CRITICAL = 3, "Critical"  # minor safety / self-harm / imminent harm

    subject_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="moderation_cases")
    reports = models.ManyToManyField(Report, blank=True, related_name="cases")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN, db_index=True)
    priority = models.IntegerField(choices=Priority.choices, default=Priority.NORMAL, db_index=True)

    primary_reason = models.CharField(max_length=15, choices=Report.Reason.choices)
    report_count = models.PositiveIntegerField(default=1)  # signal strength

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_cases")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["status", "-priority", "-report_count"])]


class ModerationAction(models.Model):
    class Kind(models.TextChoices):
        WARN = "warn", "Warning"
        MUTE = "mute", "Mute (timed)"
        ROOM_BAN = "room_ban", "Room ban"
        SUSPEND = "suspend", "Account suspension (timed)"
        BAN = "ban", "Account ban (permanent)"
        SHADOW = "shadow", "Shadow restrict"
        CONTENT_REMOVE = "content_remove", "Content removal"

    case = models.ForeignKey(ModerationCase, on_delete=models.CASCADE, null=True, blank=True, related_name="actions")
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="moderation_actions")
    kind = models.CharField(max_length=15, choices=Kind.choices, db_index=True)

    reason = models.CharField(max_length=300)
    expires_at = models.DateTimeField(null=True, blank=True)   # null = permanent
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="actions_issued")
    is_automated = models.BooleanField(default=False)
    active = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["target_user", "active", "kind"])]


class AutoModEvent(models.Model):
    """Record of an automated moderation hit (audio/text/image classifiers)."""
    class Channel(models.TextChoices):
        AUDIO = "audio", "Audio"
        TEXT = "text", "Text"
        IMAGE = "image", "Image"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="automod_events")
    channel = models.CharField(max_length=6, choices=Channel.choices)
    category = models.CharField(max_length=30)   # e.g. hate, sexual, minor_safety
    score = models.FloatField()                  # classifier confidence 0..1
    context_ref = models.CharField(max_length=120, blank=True)  # room_id / clip id
    auto_actioned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["user", "-created_at"]),
                   models.Index(fields=["category", "-score"])]
