"""
economy/services.py — The money engine.

Every balance change goes through one of these functions. None of them mutate
a Wallet directly outside a transaction. Invariants enforced here:

  1. Atomicity     — all rows commit together or not at all.
  2. Idempotency   — same idempotency_key returns the existing txn, no re-charge.
  3. Conservation  — user-to-user moves balance to zero across ledger entries.
                     Mint (IAP) and burn (payout) use a SYSTEM entry as the
                     economy boundary, so the ledger still balances.
  4. No negatives  — debits are rejected if they'd push a balance below zero.

Callers pass an idempotency_key derived from the source event (IAP order id,
client request id, etc.).
"""

from dataclasses import dataclass

from django.db import transaction
from django.db.models import F

from .models import Currency, LedgerEntry, Transaction, Wallet


class InsufficientFunds(Exception):
    pass


class EconomyError(Exception):
    pass


@dataclass
class TxnResult:
    transaction: Transaction
    created: bool  # False if returned from idempotency cache


def _get_or_create_wallet(user_id: int) -> Wallet:
    wallet, _ = Wallet.objects.get_or_create(user_id=user_id)
    return wallet


def _existing(idempotency_key: str):
    return Transaction.objects.filter(idempotency_key=idempotency_key).first()


@transaction.atomic
def credit(user_id: int, currency: str, amount: int, *, txn_type: str,
           idempotency_key: str, initiator_id: int | None = None,
           metadata: dict | None = None, system_source: bool = True) -> TxnResult:
    """
    Add value to a user's wallet. If system_source, the counter-entry is a
    SYSTEM mint (used for IAP top-ups and reward grants). Otherwise the caller
    is responsible for the matching debit (see transfer()).
    """
    if amount <= 0:
        raise EconomyError("credit amount must be positive")

    existing = _existing(idempotency_key)
    if existing:
        return TxnResult(existing, created=False)

    wallet = Wallet.objects.select_for_update().get(pk=_get_or_create_wallet(user_id).pk)

    txn = Transaction.objects.create(
        type=txn_type, idempotency_key=idempotency_key,
        initiator_id=initiator_id, metadata=metadata or {},
    )

    field = "coin_balance" if currency == Currency.COIN else "diamond_balance"
    Wallet.objects.filter(pk=wallet.pk).update(**{field: F(field) + amount})
    wallet.refresh_from_db(fields=[field])
    new_balance = getattr(wallet, field)

    if system_source:
        LedgerEntry.objects.create(
            transaction=txn, wallet=None, is_system=True,
            currency=currency, amount=-amount,
        )
    LedgerEntry.objects.create(
        transaction=txn, wallet=wallet, currency=currency,
        amount=amount, balance_after=new_balance,
    )

    if currency == Currency.DIAMOND:
        Wallet.objects.filter(pk=wallet.pk).update(
            lifetime_diamonds_earned=F("lifetime_diamonds_earned") + amount)

    return TxnResult(txn, created=True)


@transaction.atomic
def debit(user_id: int, currency: str, amount: int, *, txn_type: str,
          idempotency_key: str, initiator_id: int | None = None,
          metadata: dict | None = None, system_sink: bool = True) -> TxnResult:
    """Remove value (e.g. payout burn). Rejects if it would go negative."""
    if amount <= 0:
        raise EconomyError("debit amount must be positive")

    existing = _existing(idempotency_key)
    if existing:
        return TxnResult(existing, created=False)

    wallet = Wallet.objects.select_for_update().get(pk=_get_or_create_wallet(user_id).pk)
    current = wallet.balance(currency)
    if current < amount:
        raise InsufficientFunds(f"need {amount} {currency}, have {current}")

    txn = Transaction.objects.create(
        type=txn_type, idempotency_key=idempotency_key,
        initiator_id=initiator_id, metadata=metadata or {},
    )

    field = "coin_balance" if currency == Currency.COIN else "diamond_balance"
    Wallet.objects.filter(pk=wallet.pk).update(**{field: F(field) - amount})
    wallet.refresh_from_db(fields=[field])
    new_balance = getattr(wallet, field)

    LedgerEntry.objects.create(
        transaction=txn, wallet=wallet, currency=currency,
        amount=-amount, balance_after=new_balance,
    )
    if system_sink:
        LedgerEntry.objects.create(
            transaction=txn, wallet=None, is_system=True,
            currency=currency, amount=amount,
        )

    if currency == Currency.COIN:
        Wallet.objects.filter(pk=wallet.pk).update(
            lifetime_coins_spent=F("lifetime_coins_spent") + amount)

    return TxnResult(txn, created=True)


@transaction.atomic
def transfer(*, sender_id: int, recipient_id: int, send_currency: str,
             send_amount: int, recv_currency: str, recv_amount: int,
             txn_type: str, idempotency_key: str,
             metadata: dict | None = None) -> TxnResult:
    """
    Move value between two users with a possible currency change (gift: sender
    pays coins, recipient gets diamonds). The spread (send_amount in coins vs
    recv_amount in diamonds) is the platform take, recorded as a SYSTEM entry
    so the ledger balances per-currency.
    """
    if send_amount <= 0 or recv_amount < 0:
        raise EconomyError("invalid transfer amounts")
    if sender_id == recipient_id:
        raise EconomyError("cannot transfer to self")

    existing = _existing(idempotency_key)
    if existing:
        return TxnResult(existing, created=False)

    # lock both wallets in a stable order to avoid deadlocks
    ids = sorted([_get_or_create_wallet(sender_id).pk, _get_or_create_wallet(recipient_id).pk])
    wallets = {w.pk: w for w in Wallet.objects.select_for_update().filter(pk__in=ids)}
    sender_w = Wallet.objects.get(user_id=sender_id)
    recipient_w = Wallet.objects.get(user_id=recipient_id)
    sender_w = wallets[sender_w.pk]
    recipient_w = wallets[recipient_w.pk]

    if sender_w.balance(send_currency) < send_amount:
        raise InsufficientFunds(
            f"sender needs {send_amount} {send_currency}, has {sender_w.balance(send_currency)}")

    txn = Transaction.objects.create(
        type=txn_type, idempotency_key=idempotency_key,
        initiator_id=sender_id, metadata=metadata or {},
    )

    # debit sender
    s_field = "coin_balance" if send_currency == Currency.COIN else "diamond_balance"
    Wallet.objects.filter(pk=sender_w.pk).update(**{s_field: F(s_field) - send_amount})
    sender_w.refresh_from_db(fields=[s_field])
    LedgerEntry.objects.create(
        transaction=txn, wallet=sender_w, currency=send_currency,
        amount=-send_amount, balance_after=getattr(sender_w, s_field))
    if send_currency == Currency.COIN:
        Wallet.objects.filter(pk=sender_w.pk).update(
            lifetime_coins_spent=F("lifetime_coins_spent") + send_amount)

    # credit recipient
    if recv_amount > 0:
        r_field = "coin_balance" if recv_currency == Currency.COIN else "diamond_balance"
        Wallet.objects.filter(pk=recipient_w.pk).update(**{r_field: F(r_field) + recv_amount})
        recipient_w.refresh_from_db(fields=[r_field])
        LedgerEntry.objects.create(
            transaction=txn, wallet=recipient_w, currency=recv_currency,
            amount=recv_amount, balance_after=getattr(recipient_w, r_field))
        if recv_currency == Currency.DIAMOND:
            Wallet.objects.filter(pk=recipient_w.pk).update(
                lifetime_diamonds_earned=F("lifetime_diamonds_earned") + recv_amount)

    # SYSTEM entries close the books per currency (the spread / currency change)
    LedgerEntry.objects.create(
        transaction=txn, wallet=None, is_system=True,
        currency=send_currency, amount=send_amount)
    if recv_amount > 0:
        LedgerEntry.objects.create(
            transaction=txn, wallet=None, is_system=True,
            currency=recv_currency, amount=-recv_amount)

    return TxnResult(txn, created=True)


def verify_transaction_balances(txn: Transaction) -> bool:
    """Reconciliation helper: every currency in a txn must net to zero."""
    from collections import defaultdict
    sums = defaultdict(int)
    for e in txn.entries.all():
        sums[e.currency] += e.amount
    return all(v == 0 for v in sums.values())
