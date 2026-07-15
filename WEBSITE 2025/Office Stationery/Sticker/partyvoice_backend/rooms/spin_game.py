"""
rooms/spin_game.py — the Lucky Spin wheel (gaming rooms).

Design decisions that matter:
  * PROVABLY FAIR. Before betting opens the server generates a secret seed and
    publishes only its SHA-256 hash. After the wheel lands, the seed is
    revealed. Anyone can recompute sha256(seed) and the outcome and verify the
    round wasn't rigged after the fact. Without this, a coin-betting wheel is
    just "trust us".
  * The SERVER spins, not the client. The client animation is decoration; the
    outcome comes from the seed.
  * Bets are DEBITED when placed (no betting coins you don't have) and winners
    are credited on settle. Every move is ledgered and idempotent.
  * House edge is explicit (`HOUSE_EDGE`), not hidden in the odds.
"""

import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from economy.models import Currency, Transaction
from economy.services import InsufficientFunds, credit, debit

# The wheel. Weights are tuned so EVERY symbol returns ~0.95 coins per 1 coin
# bet — a consistent, honest 5% house edge. The LOSE_WEIGHT slots are the part
# of the wheel that matches no bet; they're what make the edge work.
#
# Getting this wrong is not a cosmetic bug: with the naive weights (40/25/12/3)
# a bet on 💎 returned ~1.69 coins per coin wagered, i.e. the house pays out
# ~69% MORE than it takes in and the coin economy inflates without limit.
# EV per symbol = P(symbol) * multiplier, and P = weight / TOTAL_WEIGHT.
WHEEL = [
    {"symbol": "🍒", "multiplier": 2, "weight": 475},   # P=.475  EV=0.950
    {"symbol": "🍋", "multiplier": 5, "weight": 190},   # P=.190  EV=0.950
    {"symbol": "🔔", "multiplier": 10, "weight": 95},   # P=.095  EV=0.950
    {"symbol": "💎", "multiplier": 45, "weight": 21},   # P=.021  EV=0.945
]
LOSE_WEIGHT = 219      # slots that match no symbol; the house's margin
TOTAL_WEIGHT = sum(w["weight"] for w in WHEEL) + LOSE_WEIGHT  # 1000
HOUSE_EDGE = 0.05      # ~5%, disclosed to players (see round_state)

BET_WINDOW_SECONDS = 20


class SpinError(Exception):
    """Bet rejected (round closed, bad symbol, insufficient coins…)."""


class SpinRound(models.Model):
    class Status(models.TextChoices):
        BETTING = "betting", "Betting open"
        SPINNING = "spinning", "Spinning"
        SETTLED = "settled", "Settled"

    room = models.ForeignKey("rooms.Room", on_delete=models.CASCADE,
                             related_name="spin_rounds")
    number = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=10, choices=Status.choices,
                              default=Status.BETTING, db_index=True)

    # provably fair: hash is published up-front, seed revealed on settle
    server_seed = models.CharField(max_length=64)
    server_seed_hash = models.CharField(max_length=64)

    winning_symbol = models.CharField(max_length=8, blank=True)
    bets_close_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def seconds_left(self) -> int:
        return max(0, int((self.bets_close_at - timezone.now()).total_seconds()))

    @property
    def pool(self) -> int:
        return sum(b.amount for b in self.bets.all())


class SpinBet(models.Model):
    round = models.ForeignKey(SpinRound, on_delete=models.CASCADE, related_name="bets")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="spin_bets")
    symbol = models.CharField(max_length=8)
    amount = models.PositiveIntegerField()
    payout = models.PositiveIntegerField(default=0)  # filled on settle
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["round", "symbol"])]


# ---------------- service ----------------

def open_round(*, room_id: int) -> SpinRound:
    """Start a new round. Publishes the seed HASH only — the seed stays secret
    until the wheel lands, which is what makes the round verifiable."""
    seed = secrets.token_hex(32)
    seed_hash = hashlib.sha256(seed.encode()).hexdigest()
    last = SpinRound.objects.filter(room_id=room_id).order_by("-number").first()
    return SpinRound.objects.create(
        room_id=room_id,
        number=(last.number + 1) if last else 1,
        server_seed=seed,
        server_seed_hash=seed_hash,
        bets_close_at=timezone.now() + timedelta(seconds=BET_WINDOW_SECONDS),
    )


@transaction.atomic
def place_bet(*, round_id: int, user_id: int, symbol: str, amount: int) -> dict:
    rnd = SpinRound.objects.select_for_update().get(id=round_id)

    if rnd.status != SpinRound.Status.BETTING:
        raise SpinError("Betting is closed for this round.")
    if timezone.now() >= rnd.bets_close_at:
        raise SpinError("Betting is closed for this round.")
    if symbol not in {w["symbol"] for w in WHEEL}:
        raise SpinError("Unknown symbol.")
    if amount <= 0:
        raise SpinError("Bet must be positive.")

    try:
        debit(
            user_id, Currency.COIN, amount,
            txn_type=Transaction.Type.PURCHASE,
            idempotency_key=f"spin:bet:{rnd.id}:{user_id}:{symbol}:{amount}",
            initiator_id=user_id,
            system_sink=True,  # pooled by the house until settle
            metadata={"reason": "spin_bet", "round": rnd.id, "symbol": symbol},
        )
    except InsufficientFunds:
        raise SpinError("Not enough coins for that bet.")

    SpinBet.objects.create(round=rnd, user_id=user_id, symbol=symbol, amount=amount)

    return {
        "round_id": rnd.id,
        "symbol": symbol,
        "amount": amount,
        "pool": rnd.pool,
        "bet_counts": bet_counts(rnd),
    }


def _pick_symbol(seed: str, round_number: int) -> str:
    """Deterministic outcome from the secret seed. Anyone holding the revealed
    seed can recompute this exactly — that's the 'provably' in provably fair.

    Rolls across the FULL wheel including the LOSE slots, so the house edge is
    real. Returns "" when the wheel lands on a losing slot (no symbol wins).
    """
    digest = hashlib.sha256(f"{seed}:{round_number}".encode()).hexdigest()
    roll = int(digest[:8], 16) % TOTAL_WEIGHT
    upto = 0
    for w in WHEEL:
        upto += w["weight"]
        if roll < upto:
            return w["symbol"]
    return ""  # landed on a LOSE slot — nobody wins this round


@transaction.atomic
def settle_round(*, round_id: int) -> dict:
    """Land the wheel, pay the winners, reveal the seed.

    Payout model: winners are paid the FULL advertised multiplier, backed by the
    house — not scaled down to whatever the pool happens to hold. An earlier
    version capped payouts at the pool, which meant a lone winner could bet 1000,
    win, and receive 950. Winning must never cost you money, or the advertised
    "×5" is a lie. The house takes `HOUSE_EDGE` of the losing stakes as its
    margin and covers the variance — that's the actual business model.
    """
    rnd = SpinRound.objects.select_for_update().get(id=round_id)
    if rnd.status == SpinRound.Status.SETTLED:
        raise SpinError("Round already settled.")

    rnd.status = SpinRound.Status.SPINNING
    winning = _pick_symbol(rnd.server_seed, rnd.number)
    rnd.winning_symbol = winning

    pool = rnd.pool
    # winning == "" means the wheel landed on a LOSE slot: nobody wins.
    winners = (list(rnd.bets.select_related("user").filter(symbol=winning))
               if winning else [])
    multiplier = (next(w["multiplier"] for w in WHEEL if w["symbol"] == winning)
                  if winning else 0)

    results = []
    for b in winners:
        payout = b.amount * multiplier  # full advertised multiplier, always
        credit(
            b.user_id, Currency.COIN, payout,
            txn_type=Transaction.Type.REWARD,
            idempotency_key=f"spin:payout:{rnd.id}:{b.id}",
            initiator_id=None,
            system_source=True,
            metadata={"reason": "spin_win", "round": rnd.id, "symbol": winning},
        )
        b.payout = payout
        b.save(update_fields=["payout"])
        results.append({
            "user_id": b.user.public_id.hex,
            "name": _display_name(b.user),
            "bet": b.amount,
            "payout": payout,
        })

    rnd.status = SpinRound.Status.SETTLED
    rnd.save(update_fields=["status", "winning_symbol"])

    total_paid = sum(r["payout"] for r in results)
    return {
        "round_id": rnd.id,
        "round_number": rnd.number,
        "winning_symbol": winning,
        "multiplier": multiplier,
        "pool": pool,
        "total_paid": total_paid,
        "house_pnl": pool - total_paid,  # negative when the house pays out big
        "winners": results,
        # revealed so players can verify: sha256(server_seed) == server_seed_hash
        "server_seed": rnd.server_seed,
        "server_seed_hash": rnd.server_seed_hash,
    }


def bet_counts(rnd: SpinRound) -> dict:
    counts = {w["symbol"]: 0 for w in WHEEL}
    for b in rnd.bets.all():
        counts[b.symbol] = counts.get(b.symbol, 0) + 1
    return counts


def round_state(rnd: SpinRound) -> dict:
    return {
        "round_id": rnd.id,
        "round_number": rnd.number,
        "status": rnd.status,
        "seconds_left": rnd.seconds_left,
        "pool": rnd.pool,
        "bet_counts": bet_counts(rnd),
        "wheel": [{"symbol": w["symbol"], "multiplier": w["multiplier"]} for w in WHEEL],
        "server_seed_hash": rnd.server_seed_hash,  # commit, published up-front
        "winning_symbol": rnd.winning_symbol or None,
        "house_edge": HOUSE_EDGE,
    }


def _display_name(user) -> str:
    prof = getattr(user, "profile", None)
    return prof.display_name if prof and prof.display_name else user.username
