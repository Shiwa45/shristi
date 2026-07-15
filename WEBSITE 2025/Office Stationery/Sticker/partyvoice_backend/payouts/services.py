"""
payouts/services.py — Withdrawal state machine.

Flow:
  request_payout()  -> validates KYC + policy + thresholds, computes conversion,
                       creates a REQUESTED PayoutRequest and an escrow HOLD that
                       debits diamonds immediately (so they can't be re-spent).
  screen_payout()   -> runs anti-fraud/AML; -> REVIEW or APPROVED.
  approve_payout()  -> moves APPROVED -> PROCESSING (kicks the processor).
  mark_paid()/fail()-> terminal transitions; failures reverse the escrow.

Diamonds are burned through economy.debit() at request time (escrow). On
rejection/failure we credit them back. This prevents double-spend during the
days-long review window.
"""

from django.db import transaction as db_txn
from django.utils import timezone

from economy.models import Currency, Transaction
from economy.services import InsufficientFunds, credit, debit
from .models import (
    KycProfile, PayoutAuditLog, PayoutPolicy, PayoutRequest,
)


class PayoutError(Exception):
    pass


def _audit(req: PayoutRequest, frm: str, to: str, actor_id=None, note=""):
    PayoutAuditLog.objects.create(
        request=req, from_status=frm, to_status=to, actor_id=actor_id, note=note)


def _compute_conversion(diamonds: int, policy: PayoutPolicy):
    # gross cash (in cents) = diamonds / diamonds_per_unit * 100
    units = diamonds / policy.diamonds_per_unit_cash
    gross_cents = int(round(units * 100))
    fee_cents = gross_cents * policy.platform_fee_bps // 10000
    net_cents = gross_cents - fee_cents
    return gross_cents, fee_cents, net_cents


@db_txn.atomic
def request_payout(*, user_id: int, method_id: int, diamonds: int, country: str) -> PayoutRequest:
    kyc = KycProfile.objects.filter(user_id=user_id).first()
    if not kyc or not kyc.can_withdraw:
        raise PayoutError("KYC must be approved before withdrawing.")

    policy = PayoutPolicy.objects.filter(country=country, enabled=True).first()
    if not policy:
        raise PayoutError("Payouts are not available in your region.")

    if diamonds < policy.min_diamonds:
        raise PayoutError(f"Minimum withdrawal is {policy.min_diamonds} diamonds.")

    # daily cap
    since = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_total = sum(
        r.diamonds for r in PayoutRequest.objects.filter(
            user_id=user_id, created_at__gte=since
        ).exclude(status__in=[PayoutRequest.Status.REJECTED, PayoutRequest.Status.FAILED])
    )
    if today_total + diamonds > policy.max_diamonds_per_day:
        raise PayoutError("Daily withdrawal limit exceeded.")

    gross, fee, net = _compute_conversion(diamonds, policy)

    # Escrow: burn diamonds now via the ledger (idempotent on request identity).
    idem = f"payout-hold:{user_id}:{timezone.now().timestamp()}"
    try:
        result = debit(
            user_id=user_id, currency=Currency.DIAMOND, amount=diamonds,
            txn_type=Transaction.Type.PAYOUT, idempotency_key=idem,
            initiator_id=user_id, system_sink=True,
            metadata={"reason": "payout_escrow", "country": country},
        )
    except InsufficientFunds:
        raise PayoutError("Insufficient diamond balance.")

    req = PayoutRequest.objects.create(
        user_id=user_id, method_id=method_id, diamonds=diamonds,
        gross_cash_cents=gross, fee_cents=fee, net_cash_cents=net,
        currency_code=policy.currency_code, status=PayoutRequest.Status.REQUESTED,
        debit_transaction=result.transaction,
    )
    _audit(req, "", PayoutRequest.Status.REQUESTED, actor_id=user_id, note="escrow debited")
    return req


def screen_payout(req: PayoutRequest, *, risk_score: float, reasons: list[str] | None = None) -> PayoutRequest:
    """Anti-fraud/AML screening hook (called by a Celery task)."""
    if req.status != PayoutRequest.Status.REQUESTED:
        raise PayoutError("Can only screen a REQUESTED payout.")
    frm = req.status
    req.risk_score = risk_score
    if risk_score >= 0.7:
        req.status = PayoutRequest.Status.REVIEW
        req.hold_reason = "; ".join(reasons or ["high risk score"])
    else:
        req.status = PayoutRequest.Status.APPROVED
    req.save(update_fields=["risk_score", "status", "hold_reason", "updated_at"])
    _audit(req, frm, req.status, note=f"risk={risk_score}")
    return req


def approve_payout(req: PayoutRequest, *, actor_id: int) -> PayoutRequest:
    if req.status not in (PayoutRequest.Status.APPROVED, PayoutRequest.Status.REVIEW):
        raise PayoutError("Payout not in an approvable state.")
    frm = req.status
    req.status = PayoutRequest.Status.PROCESSING
    req.save(update_fields=["status", "updated_at"])
    _audit(req, frm, req.status, actor_id=actor_id, note="sent to processor")
    # processor dispatch happens in a Celery task; mark_paid on webhook
    return req


def mark_paid(req: PayoutRequest, *, processor_ref: str) -> PayoutRequest:
    if req.status != PayoutRequest.Status.PROCESSING:
        raise PayoutError("Payout not processing.")
    frm = req.status
    req.status = PayoutRequest.Status.PAID
    req.processor_ref = processor_ref
    req.save(update_fields=["status", "processor_ref", "updated_at"])
    _audit(req, frm, req.status, note=f"processor_ref={processor_ref}")
    return req


@db_txn.atomic
def fail_or_reject(req: PayoutRequest, *, actor_id: int | None, reason: str, reject: bool) -> PayoutRequest:
    """Refund the escrowed diamonds and close the request."""
    if req.status in (PayoutRequest.Status.PAID, PayoutRequest.Status.REVERSED):
        raise PayoutError("Cannot reverse a completed payout here.")
    frm = req.status

    # credit diamonds back to the user (idempotent on request id)
    credit(
        user_id=req.user_id, currency=Currency.DIAMOND, amount=req.diamonds,
        txn_type=Transaction.Type.REFUND, idempotency_key=f"payout-refund:{req.id}",
        initiator_id=actor_id, system_source=True,
        metadata={"reason": "payout_refund", "payout_id": req.id},
    )
    req.status = PayoutRequest.Status.REJECTED if reject else PayoutRequest.Status.FAILED
    req.hold_reason = reason
    req.save(update_fields=["status", "hold_reason", "updated_at"])
    _audit(req, frm, req.status, actor_id=actor_id, note=reason)
    return req
