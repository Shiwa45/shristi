"""
games/draw_guess.py — "Draw & Guess" (Pictionary-style).

How it plays:
  * Each round one player is the DRAWER and gets a secret word.
  * Everyone else guesses in chat. The drawer must not say/type the word.
  * Correct guessers score — earlier guesses score more. The drawer scores based
    on how many people got it (so they're incentivised to draw *clearly*, not
    to draw something impossible).
  * Everyone drawer-rotates; highest total score after N rounds wins.

Design decisions that matter:
  * The WORD IS A SECRET from everyone but the drawer. Same discipline as the
    spy game: it's never in a room-wide broadcast.
  * GUESSES ARE VALIDATED SERVER-SIDE. A client can't declare itself correct.
  * NEAR-MISS FEEDBACK: a guess that's one edit away ("close!") is told so
    privately. Without this the game feels unresponsive when you're nearly there.
  * The drawer's own messages are checked — if they type the word, it's blocked
    (accidental or not).
  * STROKES DON'T LIVE HERE. Drawing data is high-frequency and disposable; it
    is relayed through the WebSocket consumer and never written to the DB. Only
    the *game* state (scores, phase, who's drawing) is persisted. Writing every
    brush point to Postgres would melt it.
"""

import random
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import GamePlayer, GameSession

WORDS = [
    "cat", "pizza", "guitar", "rainbow", "rocket", "castle", "dragon", "coffee",
    "bicycle", "elephant", "snowman", "camera", "island", "robot", "butterfly",
    "hamburger", "lighthouse", "umbrella", "volcano", "penguin", "cactus",
    "helicopter", "mermaid", "sandwich", "telescope", "waterfall", "windmill",
    "astronaut", "campfire", "dolphin", "fireworks", "igloo", "jellyfish",
]

MIN_PLAYERS = 3
MAX_PLAYERS = 10
DRAW_SECONDS = 80
ROUNDS_PER_PLAYER = 1          # each player draws once
CORRECT_BASE = 100             # points for being first
DRAWER_PER_GUESSER = 40        # drawer's reward per person who got it


class DrawError(Exception):
    """Invalid action (not the drawer, already guessed, wrong phase…)."""


# ---------------- lifecycle ----------------

@transaction.atomic
def start_game(*, session_id: int) -> dict:
    session = GameSession.objects.select_for_update().get(id=session_id)
    if session.status != GameSession.Status.LOBBY:
        raise DrawError("Game already started.")

    players = list(session.players.order_by("seat_slot"))
    if len(players) < MIN_PLAYERS:
        raise DrawError(f"Need at least {MIN_PLAYERS} players.")

    rng = random.Random(session.rng_seed or random.randrange(1 << 62))
    order = [p.seat_slot for p in players]
    rng.shuffle(order)

    session.state = {
        "phase": "draw",
        "round": 1,
        "total_rounds": len(players) * ROUNDS_PER_PLAYER,
        "drawer_order": order,
        "drawer_index": 0,
        "word": rng.choice(WORDS),
        "used_words": [],
        "scores": {str(p.seat_slot): 0 for p in players},
        "solved_by": [],          # [{slot, points, order}] this round
        "ends_at": (timezone.now() + timedelta(seconds=DRAW_SECONDS)).isoformat(),
        "winner": None,
    }
    session.status = GameSession.Status.PLAYING
    session.started_at = timezone.now()
    session.save(update_fields=["state", "status", "started_at"])
    return public_state(session)


def public_state(session: GameSession) -> dict:
    """No word. Ever. Only a masked hint (length + revealed letters)."""
    st = session.state
    over = st.get("winner") is not None
    players = {
        p.seat_slot: {
            "slot": p.seat_slot,
            "name": _name(p),
            "user_id": p.user.public_id.hex if p.user_id else None,
        }
        for p in session.players.select_related("user", "user__profile")
    }
    order = st.get("drawer_order", [])
    drawer = order[st["drawer_index"] % len(order)] if order else None

    return {
        "session_id": session.id,
        "phase": st.get("phase"),
        "round": st.get("round"),
        "total_rounds": st.get("total_rounds"),
        "drawer_slot": drawer,
        "players": list(players.values()),
        "scores": st.get("scores", {}),
        "solved_by": st.get("solved_by", []),
        "ends_at": st.get("ends_at"),
        "hint": _hint(st.get("word", ""), st.get("solved_by", [])),
        "winner": st.get("winner"),
        "reveal_word": st.get("word") if (over or st.get("phase") == "reveal") else None,
        "draw_seconds": DRAW_SECONDS,
    }


def drawer_state(session: GameSession, seat_slot: int) -> dict:
    """The drawer alone learns the word."""
    st = session.state
    order = st["drawer_order"]
    drawer = order[st["drawer_index"] % len(order)]
    if seat_slot != drawer:
        raise DrawError("You're not the drawer.")
    return {"your_word": st["word"], "you_are_drawer": True}


def _hint(word: str, solved_by) -> str:
    """Masked word: '_ _ _ _'. Reveal one extra letter once someone solves it,
    so late guessers still have a chance instead of being locked out."""
    if not word:
        return ""
    reveal = min(len(solved_by), max(0, len(word) - 2))
    out = []
    for i, ch in enumerate(word):
        if ch == " ":
            out.append(" ")
        elif i < reveal:
            out.append(ch)
        else:
            out.append("_")
    return " ".join(out)


# ---------------- guessing ----------------

def _normalise(s: str) -> str:
    return "".join(c for c in s.lower().strip() if c.isalnum())


def _edit_distance(a: str, b: str) -> int:
    if abs(len(a) - len(b)) > 2:
        return 99
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


@transaction.atomic
def submit_guess(*, session_id: int, seat_slot: int, text: str) -> dict:
    """Validate a guess SERVER-SIDE. Returns what to tell the guesser, plus
    whether the room state changed."""
    session = GameSession.objects.select_for_update().get(id=session_id)
    st = session.state

    if st.get("phase") != "draw":
        raise DrawError("Not guessing right now.")

    order = st["drawer_order"]
    drawer = order[st["drawer_index"] % len(order)]

    guess = _normalise(text)
    word = _normalise(st["word"])

    # The drawer typing the word — accidental or not — is blocked, never relayed.
    if seat_slot == drawer:
        if guess == word or word in guess:
            return {"blocked": True, "reason": "You can't say the word!",
                    "changed": False, "relay": False}
        return {"blocked": False, "changed": False, "relay": True}

    if any(s["slot"] == seat_slot for s in st["solved_by"]):
        return {"blocked": True, "reason": "You already got it!",
                "changed": False, "relay": False}

    if guess == word:
        # earlier guessers score more
        rank = len(st["solved_by"])
        points = max(30, CORRECT_BASE - rank * 20)
        st["solved_by"].append({"slot": seat_slot, "points": points, "order": rank})
        st["scores"][str(seat_slot)] = st["scores"].get(str(seat_slot), 0) + points

        # the drawer is paid per person who understood the drawing —
        # so drawing *clearly* is the winning strategy, not drawing cryptically
        st["scores"][str(drawer)] = st["scores"].get(str(drawer), 0) + DRAWER_PER_GUESSER

        session.state = st
        session.save(update_fields=["state"])

        # everyone (except the drawer) got it -> end the round early
        total_guessers = session.players.count() - 1
        if len(st["solved_by"]) >= total_guessers:
            return {"correct": True, "points": points, "changed": True,
                    "relay": False, "round_over": True,
                    "state": end_round(session_id=session.id)}

        return {"correct": True, "points": points, "changed": True, "relay": False}

    # near miss — told ONLY to the guesser, or it becomes a free hint for the room
    if _edit_distance(guess, word) <= 1 and len(guess) > 2:
        return {"close": True, "changed": False, "relay": False}

    return {"correct": False, "changed": False, "relay": True}


@transaction.atomic
def end_round(*, session_id: int) -> dict:
    """Time's up (or everyone guessed). Advance the drawer, or finish."""
    session = GameSession.objects.select_for_update().get(id=session_id)
    st = session.state
    if st.get("winner"):
        return public_state(session)

    st["used_words"].append(st["word"])
    st["drawer_index"] += 1

    if st["round"] >= st["total_rounds"]:
        top = max(st["scores"].items(), key=lambda kv: kv[1], default=(None, 0))
        st["winner"] = int(top[0]) if top[0] is not None else None
        st["phase"] = "over"
        session.state = st
        session.status = GameSession.Status.FINISHED
        session.finished_at = timezone.now()
        session.save(update_fields=["state", "status", "finished_at"])
        _settle(session)
        return public_state(session)

    rng = random.Random()
    remaining = [w for w in WORDS if w not in st["used_words"]] or WORDS
    st["round"] += 1
    st["word"] = rng.choice(remaining)
    st["solved_by"] = []
    st["phase"] = "draw"
    st["ends_at"] = (timezone.now() + timedelta(seconds=DRAW_SECONDS)).isoformat()

    session.state = st
    session.save(update_fields=["state"])
    return public_state(session)


def _settle(session: GameSession):
    st = session.state
    winner_slot = st.get("winner")
    for p in session.players.all():
        p.score = st["scores"].get(str(p.seat_slot), 0)
        p.result = (GamePlayer.Result.WIN if p.seat_slot == winner_slot
                    else GamePlayer.Result.LOSS)
        p.save(update_fields=["score", "result"])


@transaction.atomic
def leave_game(*, session_id: int, seat_slot: int) -> dict:
    """A player quits. If the DRAWER quits mid-round the round would hang, so
    end it immediately and move on."""
    session = GameSession.objects.select_for_update().get(id=session_id)
    st = session.state
    order = st.get("drawer_order", [])
    if not order:
        return public_state(session)

    drawer = order[st["drawer_index"] % len(order)]
    session.players.filter(seat_slot=seat_slot).delete()

    st["drawer_order"] = [s for s in order if s != seat_slot]
    session.state = st
    session.save(update_fields=["state"])

    if not st["drawer_order"] or session.players.count() < 2:
        st["winner"] = None
        st["phase"] = "over"
        session.state = st
        session.status = GameSession.Status.ABANDONED
        session.save(update_fields=["state", "status"])
        return public_state(session)

    if seat_slot == drawer:
        return end_round(session_id=session.id)
    return public_state(session)


def _name(player: GamePlayer) -> str:
    if not player.user_id:
        return f"Player {player.seat_slot + 1}"
    prof = getattr(player.user, "profile", None)
    return prof.display_name if prof and prof.display_name else player.user.username
