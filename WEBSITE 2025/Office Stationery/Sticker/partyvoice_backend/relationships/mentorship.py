"""
relationships/mentorship.py — Master-disciple system.

Eligibility (reference WePlay charm thresholds):
  * Disciple: charm value BELOW the threshold (e.g. < 12,000)
  * Master:   charm value AT/ABOVE the threshold (e.g. >= 12,000)
Disciples complete growth-point missions; reaching the graduation target
"graduates" the disciple and rewards both parties.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


CHARM_THRESHOLD = 12000          # master/disciple boundary
GRADUATION_GROWTH_POINTS = 1000  # disciple must accumulate this to graduate
MAX_DISCIPLES_PER_MASTER = 5


class Mentorship(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        GRADUATED = "graduated", "Graduated"
        ENDED = "ended", "Ended"

    master = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="disciples")
    disciple = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mentor")

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    growth_points = models.PositiveIntegerField(default=0)

    started_at = models.DateTimeField(auto_now_add=True)
    graduated_at = models.DateTimeField(null=True, blank=True)

    @property
    def progress(self) -> float:
        return min(1.0, self.growth_points / GRADUATION_GROWTH_POINTS)


# relationships/mentorship_service.py logic ----------------------------------

from django.db import transaction as db_txn

from economy.models import Currency, Transaction
from economy.services import credit


class MentorshipError(Exception):
    pass


def _charm_of(user_id: int) -> int:
    from economy.models import Wallet
    w = Wallet.objects.filter(user_id=user_id).first()
    return w.lifetime_diamonds_earned if w else 0


@db_txn.atomic
def take_disciple(*, master_id: int, disciple_id: int) -> Mentorship:
    if master_id == disciple_id:
        raise MentorshipError("You cannot mentor yourself.")
    if _charm_of(master_id) < CHARM_THRESHOLD:
        raise MentorshipError(f"Masters need a charm value of at least {CHARM_THRESHOLD}.")
    if _charm_of(disciple_id) >= CHARM_THRESHOLD:
        raise MentorshipError("This user is too established to be a disciple.")
    if Mentorship.objects.filter(disciple_id=disciple_id, status=Mentorship.Status.ACTIVE).exists():
        raise MentorshipError("This user already has a master.")
    active = Mentorship.objects.filter(master_id=master_id, status=Mentorship.Status.ACTIVE).count()
    if active >= MAX_DISCIPLES_PER_MASTER:
        raise MentorshipError("You have reached your disciple limit.")

    return Mentorship.objects.create(master_id=master_id, disciple_id=disciple_id)


@db_txn.atomic
def add_growth(*, disciple_id: int, points: int) -> Mentorship:
    m = Mentorship.objects.select_for_update().filter(
        disciple_id=disciple_id, status=Mentorship.Status.ACTIVE).first()
    if not m:
        raise MentorshipError("No active mentorship.")
    m.growth_points += max(0, points)
    if m.growth_points >= GRADUATION_GROWTH_POINTS:
        _graduate(m)
    m.save()
    return m


def _graduate(m: Mentorship):
    m.status = Mentorship.Status.GRADUATED
    m.graduated_at = timezone.now()
    # reward both parties (idempotent on mentorship id)
    for uid, role in ((m.master_id, "master"), (m.disciple_id, "disciple")):
        credit(user_id=uid, currency=Currency.COIN, amount=2000,
               txn_type=Transaction.Type.REWARD,
               idempotency_key=f"graduation:{m.id}:{role}",
               initiator_id=None, system_source=True,
               metadata={"reason": "mentorship_graduation", "mentorship": m.id})

