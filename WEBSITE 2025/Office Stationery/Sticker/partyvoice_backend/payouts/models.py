"""
payouts/models.py — Diamond -> cash withdrawal with KYC/AML gates.

This is the highest-regulatory-risk surface in the app. Design intent:
  * Withdrawals are REQUESTS that move through a state machine, never instant.
  * A user cannot request a payout until KYC is APPROVED.
  * Diamonds are debited (burned via economy.debit) only when a payout is
    APPROVED for processing — held in escrow meanwhile via a pending hold.
  * Anti-fraud holds, minimum thresholds, and regional legality are enforced.
  * Every state change is audited.

Regional legality note: in some markets diamond->cash is regulated or
prohibited. `PayoutPolicy` gates by region; legal review required per market
before enabling.
"""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class KycProfile(models.Model):
    class Status(models.TextChoices):
        UNVERIFIED = "unverified", "Unverified"
        PENDING = "pending", "Pending review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="kyc")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.UNVERIFIED, db_index=True)

    legal_name = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=2, blank=True)  # ISO 3166-1 alpha-2
    document_type = models.CharField(max_length=20, blank=True)  # passport, national_id...
    # Documents are stored by reference (encrypted object storage), never inline.
    document_ref = models.CharField(max_length=200, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    # provider integration (e.g. Onfido/Sumsub) — id from the KYC vendor
    provider = models.CharField(max_length=30, blank=True)
    provider_ref = models.CharField(max_length=120, blank=True)

    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.CharField(max_length=200, blank=True)

    @property
    def can_withdraw(self) -> bool:
        return self.status == self.Status.APPROVED

    def __str__(self):
        return f"KYC<{self.user_id}> {self.status}"


class PayoutPolicy(models.Model):
    """Per-region payout config. Absence of a row == payouts disabled there."""
    country = models.CharField(max_length=2, unique=True)
    enabled = models.BooleanField(default=False)
    # economics
    diamonds_per_unit_cash = models.PositiveIntegerField(default=100)  # diamonds per 1.00
    currency_code = models.CharField(max_length=3, default="USD")
    min_diamonds = models.PositiveIntegerField(default=10000)
    max_diamonds_per_day = models.PositiveIntegerField(default=500000)
    platform_fee_bps = models.PositiveIntegerField(default=2000)  # 20.00%


class PayoutMethod(models.Model):
    class Kind(models.TextChoices):
        BANK = "bank", "Bank transfer"
        PAYPAL = "paypal", "PayPal"
        UPI = "upi", "UPI"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payout_methods")
    kind = models.CharField(max_length=10, choices=Kind.choices)
    # tokenized/last-4 only; full details live with the payment processor
    display = models.CharField(max_length=60)        # e.g. "HDFC ****1234"
    processor_token = models.CharField(max_length=200, blank=True)
    is_default = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class PayoutRequest(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        REVIEW = "review", "Under review (fraud/AML)"
        APPROVED = "approved", "Approved"
        PROCESSING = "processing", "Processing"
        PAID = "paid", "Paid"
        REJECTED = "rejected", "Rejected"
        FAILED = "failed", "Failed"
        REVERSED = "reversed", "Reversed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="payout_requests")
    method = models.ForeignKey(PayoutMethod, on_delete=models.PROTECT, related_name="requests")

    diamonds = models.PositiveBigIntegerField(validators=[MinValueValidator(1)])
    # snapshot of conversion at request time (rates can change)
    gross_cash_cents = models.PositiveBigIntegerField()
    fee_cents = models.PositiveBigIntegerField()
    net_cash_cents = models.PositiveBigIntegerField()
    currency_code = models.CharField(max_length=3)

    status = models.CharField(max_length=12, choices=Status.choices, default=Status.REQUESTED, db_index=True)

    # links to the economy ledger debit (set when diamonds are burned)
    debit_transaction = models.ForeignKey(
        "economy.Transaction", on_delete=models.SET_NULL, null=True, blank=True, related_name="payout_debits")

    # fraud/AML
    risk_score = models.FloatField(default=0.0)
    hold_reason = models.CharField(max_length=200, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    processor_ref = models.CharField(max_length=120, blank=True)

    class Meta:
        indexes = [models.Index(fields=["status", "-created_at"])]


class PayoutAuditLog(models.Model):
    request = models.ForeignKey(PayoutRequest, on_delete=models.CASCADE, related_name="audit")
    from_status = models.CharField(max_length=12)
    to_status = models.CharField(max_length=12)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    note = models.CharField(max_length=300, blank=True)
    at = models.DateTimeField(auto_now_add=True)
