"""
fraud/models.py + services.py — Anti-fraud & AML.

Three detection families, matching the plan's economy-integrity requirements:

  1. Velocity      — abnormal rate of top-ups, gifts, or payouts in a window.
  2. Collusion     — tight reciprocal gifting rings (A->B->A) that exist to
                     launder purchased coins into withdrawable diamonds.
  3. Chargeback    — IAP refunds/chargebacks after the coins were already spent.

Signals feed a RiskScore used by the payout state machine (Phase 2) to send a
withdrawal to REVIEW. Nothing here auto-seizes funds; it raises flags for
review, because false positives on real money are costly.
"""

from django.conf import settings
from django.db import models


class FraudFlag(models.Model):
    class Kind(models.TextChoices):
        VELOCITY_TOPUP = "velocity_topup", "Top-up velocity"
        VELOCITY_GIFT = "velocity_gift", "Gift velocity"
        VELOCITY_PAYOUT = "velocity_payout", "Payout velocity"
        COLLUSION = "collusion", "Collusion ring"
        LAUNDERING = "laundering", "Suspected laundering"
        CHARGEBACK = "chargeback", "Chargeback after spend"
        DEVICE_SHARING = "device_sharing", "Shared device fingerprint"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="fraud_flags")
    kind = models.CharField(max_length=20, choices=Kind.choices, db_index=True)
    severity = models.FloatField(default=0.5)   # 0..1
    detail = models.JSONField(default=dict, blank=True)
    resolved = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["user", "resolved", "-created_at"])]


class DeviceFingerprint(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="devices")
    fingerprint = models.CharField(max_length=128, db_index=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "fingerprint")


# ----------------------------- services -----------------------------

from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.utils import timezone


# tunable thresholds (would live in config / be ML-driven in production)
TOPUP_VELOCITY_MAX = 20          # top-ups per hour
GIFT_VELOCITY_MAX = 500          # gift events per hour
RECIPROCAL_RING_MIN = 0.7        # share of gifts that flow back to senders
LAUNDERING_MIN_VALUE = 50000     # min diamond value in a reciprocal loop to flag


def _flag(user_id, kind, severity, detail):
    from .models import FraudFlag
    return FraudFlag.objects.create(
        user_id=user_id, kind=kind, severity=severity, detail=detail)


def check_topup_velocity(user_id) -> float:
    from economy.models import Transaction
    since = timezone.now() - timedelta(hours=1)
    n = Transaction.objects.filter(
        initiator_id=user_id, type=Transaction.Type.TOPUP, created_at__gte=since).count()
    if n > TOPUP_VELOCITY_MAX:
        sev = min(1.0, n / (TOPUP_VELOCITY_MAX * 2))
        _flag(user_id, "velocity_topup", sev, {"count_1h": n})
        return sev
    return 0.0


def check_gift_velocity(user_id) -> float:
    from economy.gifts import GiftEvent
    since = timezone.now() - timedelta(hours=1)
    n = GiftEvent.objects.filter(sender_id=user_id, created_at__gte=since).count()
    if n > GIFT_VELOCITY_MAX:
        sev = min(1.0, n / (GIFT_VELOCITY_MAX * 2))
        _flag(user_id, "velocity_gift", sev, {"count_1h": n})
        return sev
    return 0.0


def detect_collusion_ring(user_id, *, window_days=7) -> float:
    """
    Flag reciprocal gifting: if a large share of the diamonds a user receives
    comes from people they also heavily gift back to, that's a laundering
    pattern (buy coins -> gift partner -> partner gifts back -> withdraw).
    """
    from economy.gifts import GiftEvent, GiftRecipient
    since = timezone.now() - timedelta(days=window_days)

    # who this user gifted, and how much (by coin cost)
    sent = (GiftEvent.objects.filter(sender_id=user_id, created_at__gte=since)
            .values("recipients__user_id")
            .annotate(total=Sum("total_coin_cost")))
    sent_map = {r["recipients__user_id"]: (r["total"] or 0) for r in sent if r["recipients__user_id"]}

    # who gifted this user, and how much (by diamonds awarded)
    recv = (GiftRecipient.objects.filter(user_id=user_id, event__created_at__gte=since)
            .values("event__sender_id")
            .annotate(total=Sum("diamonds_awarded")))
    recv_map = {r["event__sender_id"]: (r["total"] or 0) for r in recv}

    total_received = sum(recv_map.values())
    if total_received < LAUNDERING_MIN_VALUE:
        return 0.0

    reciprocal_value = sum(v for uid, v in recv_map.items() if uid in sent_map)
    ratio = reciprocal_value / total_received if total_received else 0.0

    if ratio >= RECIPROCAL_RING_MIN:
        sev = min(1.0, ratio)
        _flag(user_id, "laundering", sev, {
            "reciprocal_ratio": round(ratio, 3),
            "received": total_received,
            "partners": list(set(sent_map) & set(recv_map)),
            "window_days": window_days,
        })
        return sev
    return 0.0


def score_payout_risk(user_id) -> tuple[float, list[str]]:
    """
    Composite risk score for a withdrawal request. Returns (score, reasons).
    The payout state machine sends >= 0.7 to REVIEW.
    """
    reasons = []
    score = 0.0

    laundering = detect_collusion_ring(user_id)
    if laundering:
        score = max(score, laundering)
        reasons.append("reciprocal gifting / laundering pattern")

    topup = check_topup_velocity(user_id)
    if topup:
        score = max(score, topup * 0.8)
        reasons.append("abnormal top-up velocity")

    # shared-device check: multiple accounts on one fingerprint
    from .models import DeviceFingerprint, FraudFlag
    fps = DeviceFingerprint.objects.filter(user_id=user_id).values_list("fingerprint", flat=True)
    shared = (DeviceFingerprint.objects.filter(fingerprint__in=list(fps))
              .exclude(user_id=user_id).values("user_id").distinct().count())
    if shared >= 3:
        score = max(score, 0.75)
        reasons.append(f"device shared with {shared} other accounts")
        _flag(user_id, "device_sharing", 0.75, {"shared_accounts": shared})

    # unresolved chargebacks are an automatic high flag
    if FraudFlag.objects.filter(user_id=user_id, kind="chargeback", resolved=False).exists():
        score = max(score, 0.9)
        reasons.append("unresolved chargeback")

    return min(1.0, score), reasons
