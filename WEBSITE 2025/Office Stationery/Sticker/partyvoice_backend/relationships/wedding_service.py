"""
relationships/wedding_service.py — Marriage lifecycle.

propose():  buy a ring (coin debit), create an ENGAGED marriage.
accept():   partner_b confirms -> MARRIED, rings appear on both profiles.
add_value(): guest gifts during ceremony fill affection/blessing.
divorce():  consensual (free, both agree) or forced (unilateral, coin cost).
reunite():  within the grace window, restore the prior affection/blessing.

One active (engaged/married) marriage per user is enforced.
"""

from django.db import transaction as db_txn
from django.db.models import Q
from django.utils import timezone

from economy.models import Currency, Transaction
from economy.services import InsufficientFunds, debit
from .weddings import FORCED_DIVORCE_COST, Marriage, Ring


class WeddingError(Exception):
    pass


def _has_active_marriage(user_id: int) -> bool:
    return Marriage.objects.filter(
        Q(partner_a_id=user_id) | Q(partner_b_id=user_id),
        status__in=[Marriage.Status.ENGAGED, Marriage.Status.MARRIED],
    ).exists()


@db_txn.atomic
def propose(*, proposer_id: int, partner_id: int, ring_code: str, room_id: str = "") -> Marriage:
    if proposer_id == partner_id:
        raise WeddingError("You cannot marry yourself.")
    if _has_active_marriage(proposer_id) or _has_active_marriage(partner_id):
        raise WeddingError("One of you is already engaged or married.")

    ring = Ring.objects.get(code=ring_code)
    try:
        debit(user_id=proposer_id, currency=Currency.COIN, amount=ring.coin_cost,
              txn_type=Transaction.Type.PURCHASE,
              idempotency_key=f"ring:{proposer_id}:{partner_id}:{ring_code}:{_now()}",
              initiator_id=proposer_id, system_sink=True,
              metadata={"reason": "ring_purchase", "ring": ring_code})
    except InsufficientFunds:
        raise WeddingError(f"That ring costs {ring.coin_cost} coins.")

    return Marriage.objects.create(
        partner_a_id=proposer_id, partner_b_id=partner_id, ring=ring, room_id=room_id)


@db_txn.atomic
def accept(*, marriage_id: int, partner_id: int) -> Marriage:
    m = Marriage.objects.select_for_update().get(pk=marriage_id)
    if m.partner_b_id != partner_id:
        raise WeddingError("Only the proposed partner can accept.")
    if m.status != Marriage.Status.ENGAGED:
        raise WeddingError("This proposal is no longer pending.")
    m.status = Marriage.Status.MARRIED
    m.married_at = timezone.now()
    m.save(update_fields=["status", "married_at"])
    return m


@db_txn.atomic
def add_value(*, marriage_id: int, affection: int = 0, blessing: int = 0) -> Marriage:
    m = Marriage.objects.select_for_update().get(pk=marriage_id)
    if m.status == Marriage.Status.DIVORCED:
        raise WeddingError("This marriage has ended.")
    m.affection += max(0, affection)
    m.blessing += max(0, blessing)
    m.save(update_fields=["affection", "blessing"])
    return m


@db_txn.atomic
def divorce(*, marriage_id: int, actor_id: int, forced: bool) -> Marriage:
    m = Marriage.objects.select_for_update().get(pk=marriage_id)
    if not m.involves(actor_id):
        raise WeddingError("You are not part of this marriage.")
    if m.status == Marriage.Status.DIVORCED:
        raise WeddingError("Already divorced.")

    if forced:
        # unilateral: costs coins
        try:
            debit(user_id=actor_id, currency=Currency.COIN, amount=FORCED_DIVORCE_COST,
                  txn_type=Transaction.Type.PURCHASE,
                  idempotency_key=f"divorce:{marriage_id}:{actor_id}:{_now()}",
                  initiator_id=actor_id, system_sink=True,
                  metadata={"reason": "forced_divorce", "marriage": marriage_id})
        except InsufficientFunds:
            raise WeddingError(f"A forced divorce costs {FORCED_DIVORCE_COST} coins.")
    # consensual divorce is modelled at the API layer (both must call);
    # here we just finalize. Affection/blessing retained for the grace window.
    m.status = Marriage.Status.DIVORCED
    m.divorced_at = timezone.now()
    m.save(update_fields=["status", "divorced_at"])
    return m


@db_txn.atomic
def reunite(*, marriage_id: int, actor_id: int) -> Marriage:
    m = Marriage.objects.select_for_update().get(pk=marriage_id)
    if not m.involves(actor_id):
        raise WeddingError("You are not part of this marriage.")
    if m.status != Marriage.Status.DIVORCED:
        raise WeddingError("This marriage is not divorced.")
    if not m.within_reunion_window:
        raise WeddingError("The reunion window has closed.")
    if _has_active_marriage(m.partner_a_id) or _has_active_marriage(m.partner_b_id):
        raise WeddingError("One partner has since remarried.")
    # affection/blessing were retained, so reunion restores everything
    m.status = Marriage.Status.MARRIED
    m.divorced_at = None
    m.save(update_fields=["status", "divorced_at"])
    return m


def _now() -> str:
    return str(int(timezone.now().timestamp()))
