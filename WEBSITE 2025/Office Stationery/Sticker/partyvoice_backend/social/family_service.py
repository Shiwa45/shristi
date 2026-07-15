"""
social/family_service.py — Family operations with economy integration.

create_family():   debits the creation cost, makes the founder MANAGER.
contribute():      debits coins, adds to family funds + exp, may trigger level-up.
join/approve:      capacity-checked membership flow.
promote/demote/kick: role-gated management actions.
"""

from django.db import transaction as db_txn

from economy.models import Currency, Transaction
from economy.services import InsufficientFunds, debit
from .families import FAMILY_CREATION_COST, Family, FamilyJoinRequest, FamilyMember


class FamilyError(Exception):
    pass


# exp needed to reach level N+1 (index = current level)
LEVEL_EXP = {n: n * 100000 for n in range(1, 11)}


@db_txn.atomic
def create_family(*, founder_id: int, name: str, logo_url: str = "") -> Family:
    if Family.objects.filter(name=name).exists():
        raise FamilyError("That family name is taken.")
    if FamilyMember.objects.filter(user_id=founder_id).exists():
        raise FamilyError("You are already in a family.")

    try:
        debit(user_id=founder_id, currency=Currency.COIN, amount=FAMILY_CREATION_COST,
              txn_type=Transaction.Type.PURCHASE,
              idempotency_key=f"family-create:{founder_id}:{name}",
              initiator_id=founder_id, system_sink=True,
              metadata={"reason": "family_creation", "name": name})
    except InsufficientFunds:
        raise FamilyError(f"Creating a family costs {FAMILY_CREATION_COST} coins.")

    family = Family.objects.create(name=name, logo_url=logo_url, created_by_id=founder_id)
    FamilyMember.objects.create(family=family, user_id=founder_id, role=FamilyMember.Role.MANAGER)
    return family


@db_txn.atomic
def contribute(*, user_id: int, amount: int) -> Family:
    member = FamilyMember.objects.select_for_update().filter(user_id=user_id).first()
    if not member:
        raise FamilyError("You are not in a family.")
    if amount <= 0:
        raise FamilyError("Contribution must be positive.")

    try:
        debit(user_id=user_id, currency=Currency.COIN, amount=amount,
              txn_type=Transaction.Type.PURCHASE,
              idempotency_key=f"family-contrib:{user_id}:{member.family_id}:{amount}:{_now_key()}",
              initiator_id=user_id, system_sink=True,
              metadata={"reason": "family_contribution", "family": member.family_id})
    except InsufficientFunds:
        raise FamilyError("Not enough coins.")

    family = Family.objects.select_for_update().get(pk=member.family_id)
    family.funds += amount
    family.exp += amount
    member.contribution += amount
    member.save(update_fields=["contribution"])

    _maybe_level_up(family)
    family.save()
    return family


def _maybe_level_up(family: Family):
    while family.level < 11 and family.exp >= LEVEL_EXP.get(family.level, float("inf")):
        family.exp -= LEVEL_EXP[family.level]
        family.level += 1


@db_txn.atomic
def request_join(*, user_id: int, family_id: int) -> FamilyJoinRequest:
    if FamilyMember.objects.filter(user_id=user_id).exists():
        raise FamilyError("You are already in a family.")
    req, _ = FamilyJoinRequest.objects.get_or_create(
        family_id=family_id, user_id=user_id,
        defaults={"status": FamilyJoinRequest.Status.PENDING})
    return req


@db_txn.atomic
def approve_join(*, approver_id: int, request_id: int) -> FamilyMember:
    req = FamilyJoinRequest.objects.select_for_update().get(pk=request_id)
    approver = FamilyMember.objects.get(user_id=approver_id, family_id=req.family_id)
    if not approver.can_manage:
        raise FamilyError("Only managers can approve members.")
    family = Family.objects.select_for_update().get(pk=req.family_id)
    if family.members.count() >= family.member_capacity:
        raise FamilyError("Family is at capacity.")
    if FamilyMember.objects.filter(user_id=req.user_id).exists():
        raise FamilyError("User already joined a family.")

    req.status = FamilyJoinRequest.Status.APPROVED
    req.save(update_fields=["status"])
    return FamilyMember.objects.create(family=family, user_id=req.user_id)


@db_txn.atomic
def set_role(*, actor_id: int, target_user_id: int, new_role: int) -> FamilyMember:
    target = FamilyMember.objects.select_for_update().get(user_id=target_user_id)
    actor = FamilyMember.objects.get(user_id=actor_id, family_id=target.family_id)
    # only the manager can change roles, and cannot create a second manager
    if actor.role != FamilyMember.Role.MANAGER:
        raise FamilyError("Only the manager can change roles.")
    if new_role >= FamilyMember.Role.MANAGER:
        raise FamilyError("Transfer ownership separately; cannot mint a second manager.")
    target.role = new_role
    target.save(update_fields=["role"])
    return target


@db_txn.atomic
def kick_member(*, actor_id: int, target_user_id: int):
    target = FamilyMember.objects.select_for_update().get(user_id=target_user_id)
    actor = FamilyMember.objects.get(user_id=actor_id, family_id=target.family_id)
    if not actor.can_manage or actor.role <= target.role:
        raise FamilyError("You cannot remove this member.")
    target.delete()


def _now_key() -> str:
    from django.utils import timezone
    return str(int(timezone.now().timestamp()))
