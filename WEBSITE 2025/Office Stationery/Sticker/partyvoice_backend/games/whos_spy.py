"""
games/whos_spy.py — "Who's the Spy" (aka Undercover / Spyfall-style).

How it plays:
  * Everyone gets a secret word. The civilians all get the SAME word; the spy
    (or spies) get a DIFFERENT but related word — or, on hard mode, nothing at
    all (a "blank").
  * Each round, players take turns describing their word out loud (this is why
    it's voice-native — the room's mic IS the game).
  * Then everyone votes. The most-voted player is eliminated and their role is
    revealed.
  * Civilians win when every spy is eliminated. Spies win when they survive
    down to parity (spies >= civilians).

Design decisions that matter:
  * SERVER-AUTHORITATIVE. The word pair, who the spy is, turn order, and the
    vote tally all live here. The client only renders. A client that knows the
    spy is a client that can cheat.
  * SECRETS STAY SECRET. Each player is only ever told THEIR OWN word. The
    consumer sends a per-player payload — the shared broadcast never contains
    the word or the spy's identity until reveal.
  * Ties are resolved by re-vote, not coin-flip: eliminating the wrong person
    on a coin-flip feels terrible and players blame the game.
  * Staked games escrow the entry fee up-front and pay the winning side from
    the pot, ledgered like everything else.
"""

import random

from django.db import transaction
from django.utils import timezone

from economy.models import Currency, Transaction
from economy.services import InsufficientFunds, credit, debit

from .models import GamePlayer, GameSession

# ---- word pairs: (civilian_word, spy_word) ----
# Related but distinct: the spy must bluff plausibly, not flail obviously.
WORD_PAIRS = [
    ("Coffee", "Tea"),
    ("Cat", "Dog"),
    ("Pizza", "Burger"),
    ("Beach", "Desert"),
    ("Guitar", "Piano"),
    ("Winter", "Autumn"),
    ("Doctor", "Nurse"),
    ("Football", "Basketball"),
    ("Train", "Bus"),
    ("Moon", "Sun"),
    ("Chocolate", "Vanilla"),
    ("Rain", "Snow"),
    ("Mountain", "Hill"),
    ("River", "Lake"),
    ("Bread", "Rice"),
    ("Phone", "Laptop"),
    ("Sugar", "Salt"),
    ("Lion", "Tiger"),
    ("Wedding", "Birthday"),
    ("Teacher", "Student"),
]

MIN_PLAYERS = 4
MAX_PLAYERS = 12
DESCRIBE_SECONDS = 45
VOTE_SECONDS = 30
HOUSE_RAKE = 0.05  # on staked games only; disclosed


class SpyError(Exception):
    """Invalid action (not your turn, already voted, wrong phase…)."""


def _spy_count(n_players: int) -> int:
    """1 spy up to 7 players, 2 spies from 8. Keeps the odds sane."""
    return 2 if n_players >= 8 else 1


# ---------------- lifecycle ----------------

@transaction.atomic
def start_game(*, session_id: int) -> dict:
    """Deal roles + words. Returns the PUBLIC state (no secrets)."""
    session = GameSession.objects.select_for_update().get(id=session_id)
    if session.status != GameSession.Status.LOBBY:
        raise SpyError("Game already started.")

    players = list(session.players.select_related("user").order_by("seat_slot"))
    if len(players) < MIN_PLAYERS:
        raise SpyError(f"Need at least {MIN_PLAYERS} players.")
    if len(players) > MAX_PLAYERS:
        raise SpyError(f"At most {MAX_PLAYERS} players.")

    # escrow the stake before dealing — nobody plays for free in a staked game
    if session.stake_coins > 0:
        for p in players:
            if p.is_bot or not p.user_id:
                continue
            try:
                debit(
                    p.user_id, Currency.COIN, session.stake_coins,
                    txn_type=Transaction.Type.PURCHASE,
                    idempotency_key=f"spy:stake:{session.id}:{p.user_id}",
                    initiator_id=p.user_id,
                    system_sink=True,
                    metadata={"reason": "spy_stake", "session": session.id},
                )
            except InsufficientFunds:
                raise SpyError(f"{_name(p)} doesn't have enough coins to stake.")

    rng = random.Random(session.rng_seed or random.randrange(1 << 62))
    civ_word, spy_word = rng.choice(WORD_PAIRS)

    n_spies = _spy_count(len(players))
    spy_slots = rng.sample([p.seat_slot for p in players], n_spies)

    # turn order is shuffled so the spy isn't always forced to speak first
    order = [p.seat_slot for p in players]
    rng.shuffle(order)

    session.state = {
        "phase": "describe",
        "round": 1,
        "civ_word": civ_word,
        "spy_word": spy_word,
        "spy_slots": spy_slots,
        "turn_order": order,
        "turn_index": 0,
        "alive": [p.seat_slot for p in players],
        "eliminated": [],       # [{slot, was_spy, round}]
        "votes": {},            # {voter_slot: target_slot}
        "descriptions": {},     # {slot: text} — optional typed hint
        "winner": None,         # "civilians" | "spies"
        "revote": False,
    }
    session.status = GameSession.Status.PLAYING
    session.started_at = timezone.now()
    session.save(update_fields=["state", "status", "started_at"])

    return public_state(session)


def private_state(session: GameSession, seat_slot: int) -> dict:
    """What ONE player is allowed to know: their own word and role only."""
    st = session.state
    is_spy = seat_slot in st.get("spy_slots", [])
    return {
        "your_slot": seat_slot,
        "your_word": st["spy_word"] if is_spy else st["civ_word"],
        "you_are_spy": is_spy,
        # the spy is told how many spies there are (so 2 spies can find each
        # other by inference) but NOT who the other spy is.
        "spy_count": len(st.get("spy_slots", [])),
    }


def public_state(session: GameSession) -> dict:
    """What EVERYONE sees. Deliberately contains no words and no spy identity
    until the game is over."""
    st = session.state
    over = st.get("winner") is not None
    players = {
        p.seat_slot: {
            "slot": p.seat_slot,
            "name": _name(p),
            "user_id": p.user.public_id.hex if p.user_id else None,
            "is_bot": p.is_bot,
        }
        for p in session.players.select_related("user", "user__profile")
    }
    turn_slot = None
    if st.get("phase") == "describe":
        order = [s for s in st["turn_order"] if s in st["alive"]]
        if order:
            turn_slot = order[st["turn_index"] % len(order)]

    return {
        "session_id": session.id,
        "phase": st.get("phase"),
        "round": st.get("round"),
        "players": list(players.values()),
        "alive": st.get("alive", []),
        "eliminated": st.get("eliminated", []),
        "turn_slot": turn_slot,
        "votes_cast": len(st.get("votes", {})),
        "alive_count": len(st.get("alive", [])),
        "descriptions": st.get("descriptions", {}),
        "winner": st.get("winner"),
        "revote": st.get("revote", False),
        "describe_seconds": DESCRIBE_SECONDS,
        "vote_seconds": VOTE_SECONDS,
        # revealed ONLY when the game is over
        "reveal": {
            "civ_word": st["civ_word"],
            "spy_word": st["spy_word"],
            "spy_slots": st["spy_slots"],
        } if over else None,
    }


# ---------------- actions ----------------

@transaction.atomic
def submit_description(*, session_id: int, seat_slot: int, text: str) -> dict:
    """Optional typed hint alongside the voice description, then pass the turn."""
    session = GameSession.objects.select_for_update().get(id=session_id)
    st = session.state
    if st.get("phase") != "describe":
        raise SpyError("Not the describe phase.")
    if seat_slot not in st["alive"]:
        raise SpyError("You're eliminated.")

    order = [s for s in st["turn_order"] if s in st["alive"]]
    current = order[st["turn_index"] % len(order)]
    if seat_slot != current:
        raise SpyError("It's not your turn.")

    st["descriptions"][str(seat_slot)] = text[:80]
    st["turn_index"] += 1

    # everyone alive has spoken -> move to voting
    if st["turn_index"] >= len(order):
        st["phase"] = "vote"
        st["turn_index"] = 0
        st["votes"] = {}

    session.state = st
    session.save(update_fields=["state"])
    return public_state(session)


@transaction.atomic
def cast_vote(*, session_id: int, voter_slot: int, target_slot: int) -> dict:
    session = GameSession.objects.select_for_update().get(id=session_id)
    st = session.state
    if st.get("phase") != "vote":
        raise SpyError("Not the voting phase.")
    if voter_slot not in st["alive"]:
        raise SpyError("You're eliminated.")
    if target_slot not in st["alive"]:
        raise SpyError("That player is already out.")
    if voter_slot == target_slot:
        raise SpyError("You can't vote for yourself.")
    if str(voter_slot) in st["votes"]:
        raise SpyError("You already voted.")

    st["votes"][str(voter_slot)] = target_slot
    session.state = st
    session.save(update_fields=["state"])

    # everyone alive has voted -> tally
    if len(st["votes"]) >= len(st["alive"]):
        return _tally(session)
    return public_state(session)


def _tally(session: GameSession) -> dict:
    st = session.state
    counts = {}
    for target in st["votes"].values():
        counts[target] = counts.get(target, 0) + 1

    top = max(counts.values())
    tied = [slot for slot, n in counts.items() if n == top]

    if len(tied) > 1:
        # A tie eliminates nobody. Re-vote instead of coin-flipping someone out
        # — being knocked out by a coin toss is the fastest way to make players
        # feel cheated.
        st["votes"] = {}
        st["revote"] = True
        session.state = st
        session.save(update_fields=["state"])
        return public_state(session)

    st["revote"] = False
    out = tied[0]
    was_spy = out in st["spy_slots"]
    st["alive"] = [s for s in st["alive"] if s != out]
    st["eliminated"].append({"slot": out, "was_spy": was_spy, "round": st["round"]})

    spies_left = [s for s in st["spy_slots"] if s in st["alive"]]
    civs_left = [s for s in st["alive"] if s not in st["spy_slots"]]

    if not spies_left:
        st["winner"] = "civilians"
    elif len(spies_left) >= len(civs_left):
        # spies reach parity -> they can always force a tie vote from here
        st["winner"] = "spies"
    else:
        st["round"] += 1
        st["phase"] = "describe"
        st["turn_index"] = 0
        st["votes"] = {}
        st["descriptions"] = {}

    session.state = st

    if st["winner"]:
        session.status = GameSession.Status.FINISHED
        session.finished_at = timezone.now()
        session.save(update_fields=["state", "status", "finished_at"])
        _settle(session)
    else:
        session.save(update_fields=["state"])

    return public_state(session)


@transaction.atomic
def _settle(session: GameSession):
    """Mark results and pay the winning side from the escrowed pot."""
    st = session.state
    winner = st["winner"]
    players = list(session.players.all())

    winners, losers = [], []
    for p in players:
        is_spy = p.seat_slot in st["spy_slots"]
        won = (winner == "spies") == is_spy
        p.result = GamePlayer.Result.WIN if won else GamePlayer.Result.LOSS
        p.save(update_fields=["result"])
        (winners if won else losers).append(p)

    if session.stake_coins <= 0:
        return

    # pot = every human's stake; rake the house cut; split among human winners
    human_players = [p for p in players if p.user_id and not p.is_bot]
    pot = session.stake_coins * len(human_players)
    human_winners = [p for p in winners if p.user_id and not p.is_bot]
    if not human_winners:
        return  # only bots won; house keeps the pot

    payout_pool = int(pot * (1 - HOUSE_RAKE))
    share = payout_pool // len(human_winners)
    for p in human_winners:
        credit(
            p.user_id, Currency.COIN, share,
            txn_type=Transaction.Type.REWARD,
            idempotency_key=f"spy:payout:{session.id}:{p.user_id}",
            initiator_id=None,
            system_source=True,
            metadata={"reason": "spy_win", "session": session.id, "side": winner},
        )


@transaction.atomic
def leave_game(*, session_id: int, seat_slot: int) -> dict:
    """A player quits mid-game: treat as eliminated, then re-check the win
    condition so the game doesn't hang."""
    session = GameSession.objects.select_for_update().get(id=session_id)
    st = session.state
    if seat_slot not in st.get("alive", []):
        return public_state(session)

    was_spy = seat_slot in st["spy_slots"]
    st["alive"] = [s for s in st["alive"] if s != seat_slot]
    st["eliminated"].append(
        {"slot": seat_slot, "was_spy": was_spy, "round": st["round"], "quit": True})
    st["votes"].pop(str(seat_slot), None)

    spies_left = [s for s in st["spy_slots"] if s in st["alive"]]
    civs_left = [s for s in st["alive"] if s not in st["spy_slots"]]
    if not spies_left:
        st["winner"] = "civilians"
    elif len(spies_left) >= len(civs_left):
        st["winner"] = "spies"

    session.state = st
    if st["winner"]:
        session.status = GameSession.Status.FINISHED
        session.finished_at = timezone.now()
        session.save(update_fields=["state", "status", "finished_at"])
        _settle(session)
    else:
        session.save(update_fields=["state"])
    return public_state(session)


def _name(player: GamePlayer) -> str:
    if player.is_bot or not player.user_id:
        return f"Bot {player.seat_slot + 1}"
    prof = getattr(player.user, "profile", None)
    return prof.display_name if prof and prof.display_name else player.user.username
