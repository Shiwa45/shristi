"""
games/services.py — Game lifecycle + staked-result settlement.

The server is the referee for staked games: it collects entry stakes into a
pot (atomic coin debits via the economy ledger) and pays the winner(s) out of
that pot when a result is reported and validated. Non-staked games skip all
economy interaction.

Anti-cheat note: clients report results, but for staked games the server
should validate the reported result against the authoritative `state` it has
been tracking over the sync channel before settling. The validation hook is
`validate_result()` — game-specific validators plug in per definition code.
"""

import random

from django.db import transaction as db_txn
from django.utils import timezone

from economy.models import Currency, Transaction
from economy.services import InsufficientFunds, credit, debit
from .models import GameDefinition, GamePlayer, GameSession


class GameError(Exception):
    pass


@db_txn.atomic
def create_session(*, definition_code: str, room_id: str, host_id: int,
                   stake_coins: int = 0) -> GameSession:
    definition = GameDefinition.objects.get(code=definition_code, is_active=True)
    if stake_coins and not definition.is_staked:
        raise GameError("This game does not support stakes.")
    session = GameSession.objects.create(
        definition=definition, room_id=room_id, host_id=host_id,
        stake_coins=stake_coins, rng_seed=random.getrandbits(48),
        status=GameSession.Status.LOBBY,
    )
    return session


@db_txn.atomic
def join_session(*, session_id: int, user_id: int, seat_slot: int,
                 team: int | None = None) -> GamePlayer:
    session = GameSession.objects.select_for_update().get(pk=session_id)
    if session.status != GameSession.Status.LOBBY:
        raise GameError("Game already started.")
    if session.players.count() >= session.definition.max_players:
        raise GameError("Game is full.")

    # staked game: debit the entry stake into the pot at join time
    if session.stake_coins:
        idem = f"game-stake:{session_id}:{user_id}"
        try:
            debit(user_id=user_id, currency=Currency.COIN, amount=session.stake_coins,
                  txn_type=Transaction.Type.PURCHASE, idempotency_key=idem,
                  initiator_id=user_id, system_sink=False,
                  metadata={"reason": "game_stake", "session": session_id})
        except InsufficientFunds:
            raise GameError("Not enough coins for the entry stake.")

    return GamePlayer.objects.create(
        session=session, user_id=user_id, seat_slot=seat_slot, team=team)


@db_txn.atomic
def add_bot(*, session_id: int, seat_slot: int, team: int | None = None) -> GamePlayer:
    session = GameSession.objects.select_for_update().get(pk=session_id)
    if not session.definition.supports_bots:
        raise GameError("This game does not support bots.")
    return GamePlayer.objects.create(
        session=session, user=None, is_bot=True, seat_slot=seat_slot, team=team)


@db_txn.atomic
def start_session(*, session_id: int) -> GameSession:
    session = GameSession.objects.select_for_update().get(pk=session_id)
    n = session.players.count()
    if n < session.definition.min_players:
        raise GameError("Not enough players.")
    session.status = GameSession.Status.PLAYING
    session.started_at = timezone.now()
    session.save(update_fields=["status", "started_at"])
    return session


def validate_result(session: GameSession, reported: dict) -> bool:
    """
    Per-game referee validation. Default trusts the report for non-staked games;
    staked games should register a stricter validator. Game-specific validators
    can be registered in VALIDATORS by definition code.
    """
    if not session.stake_coins:
        return True
    validator = VALIDATORS.get(session.definition.code)
    if validator is None:
        # staked game with no validator: refuse to settle automatically
        return False
    return validator(session, reported)


VALIDATORS: dict[str, callable] = {}


def register_validator(code: str):
    def deco(fn):
        VALIDATORS[code] = fn
        return fn
    return deco


@db_txn.atomic
def settle_session(*, session_id: int, winner_slots: list[int], scores: dict | None = None) -> GameSession:
    """
    Finalize a game. For staked games, the pot (sum of all stakes) is split
    among winners. Idempotent on session id — re-settling returns the finished
    session without paying twice.
    """
    session = GameSession.objects.select_for_update().get(pk=session_id)
    if session.status == GameSession.Status.FINISHED:
        return session
    if session.status != GameSession.Status.PLAYING:
        raise GameError("Game is not in progress.")

    players = list(session.players.all())
    scores = scores or {}
    for p in players:
        p.score = scores.get(str(p.seat_slot), p.score)
        if p.seat_slot in winner_slots:
            p.result = GamePlayer.Result.WIN
        elif len(winner_slots) == len(players):
            p.result = GamePlayer.Result.DRAW
        else:
            p.result = GamePlayer.Result.LOSS
        p.save(update_fields=["score", "result"])

    if session.stake_coins:
        pot = session.stake_coins * len(players)
        human_winners = [p for p in players if p.seat_slot in winner_slots and p.user_id]
        if human_winners:
            share = pot // len(human_winners)
            for p in human_winners:
                credit(user_id=p.user_id, currency=Currency.COIN, amount=share,
                       txn_type=Transaction.Type.REWARD,
                       idempotency_key=f"game-payout:{session_id}:{p.user_id}",
                       initiator_id=None, system_source=True,
                       metadata={"reason": "game_win", "session": session_id})

    session.status = GameSession.Status.FINISHED
    session.finished_at = timezone.now()
    session.save(update_fields=["status", "finished_at"])
    return session
