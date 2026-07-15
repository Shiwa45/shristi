"""
economy/models.py — Phase 2 virtual economy (production-grade).

Design principles:
  * Double-entry ledger: every value movement is recorded as balanced
    LedgerEntry rows (sum of deltas per transaction == 0 within a currency).
  * Balances are DENORMALIZED on Wallet for fast reads, but always derivable
    from the ledger — a reconciliation job can verify wallet == sum(ledger).
  * All mutations are atomic (select_for_update) and idempotent (idempotency_key).
  * Coins are spendable (bought via IAP / earned). Diamonds are earned by
    recipients of gifts and are the basis for host payouts.

Currencies are kept as integers (smallest indivisible unit) — never floats.
"""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Currency(models.TextChoices):
    COIN = "coin", "Coin"        # spendable
    DIAMOND = "diamond", "Diamond"  # earned, payout-eligible


class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallet")
    coin_balance = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
    diamond_balance = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])

    # lifetime aggregates that feed wealth/charm (never decrease)
    lifetime_coins_spent = models.BigIntegerField(default=0)
    lifetime_diamonds_earned = models.BigIntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    def balance(self, currency: str) -> int:
        return self.coin_balance if currency == Currency.COIN else self.diamond_balance

    def __str__(self):
        return f"Wallet<{self.user_id}> {self.coin_balance}c / {self.diamond_balance}d"


class Transaction(models.Model):
    """
    A logical money event. Groups balanced LedgerEntry rows.
    `idempotency_key` makes retries safe: the same key returns the same txn
    instead of double-charging.
    """
    class Type(models.TextChoices):
        TOPUP = "topup", "Top-up (IAP)"
        GIFT = "gift", "Gift"
        PAYOUT = "payout", "Payout (diamond->cash)"
        REWARD = "reward", "Reward grant"
        REFUND = "refund", "Refund"
        CONVERT = "convert", "Diamond->coin convert"
        PURCHASE = "purchase", "In-app item purchase"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        REVERSED = "reversed", "Reversed"

    type = models.CharField(max_length=12, choices=Type.choices, db_index=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.COMPLETED, db_index=True)
    idempotency_key = models.CharField(max_length=80, unique=True, db_index=True)

    # convenience references (the ledger is the source of truth)
    initiator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="initiated_txns")
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["type", "status", "-created_at"])]

    def __str__(self):
        return f"Txn<{self.id}> {self.type}/{self.status}"


class LedgerEntry(models.Model):
    """
    One side of a double-entry movement. `amount` is signed: debits are
    negative, credits positive. For each (transaction, currency), the sum of
    amounts across all entries must be zero (value is conserved, except for
    SYSTEM entries which represent the economy boundary — IAP mint / payout burn).
    """
    transaction = models.ForeignKey(Transaction, on_delete=models.PROTECT, related_name="entries")
    wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT, related_name="ledger_entries", null=True)
    # null wallet == SYSTEM account (mint/burn boundary for IAP and payouts)
    is_system = models.BooleanField(default=False)

    currency = models.CharField(max_length=8, choices=Currency.choices)
    amount = models.BigIntegerField()  # signed
    balance_after = models.BigIntegerField(null=True)  # snapshot for user wallets

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["wallet", "currency", "-created_at"])]

    def __str__(self):
        sign = "+" if self.amount >= 0 else ""
        who = "SYSTEM" if self.is_system else self.wallet_id
        return f"Ledger<{who}> {sign}{self.amount} {self.currency}"
