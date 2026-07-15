"""
games/models.py — Game framework (server side of the WebView game bridge).

Per the plan, games render as HTML/JS in a WebView and sync over the room
WebSocket. The server is the authoritative referee for anything that affects
the economy or rankings (stakes, results), while moment-to-moment rendering
state can stay client-side and gossip over the sync channel.

GameDefinition is config-driven so new games ship without backend changes.
GameSession tracks one play instance bound to a room.
"""

from django.conf import settings
from django.db import models


class GameDefinition(models.Model):
    """Catalog of playable games. `bundle_url` is the WebView entry point."""
    class Mode(models.TextChoices):
        TURN = "turn", "Turn-based"
        REALTIME = "realtime", "Real-time"
        ROUND = "round", "Round-based"

    code = models.SlugField(max_length=40, unique=True)   # ludo, whos_spy, draw_guess...
    name = models.CharField(max_length=60)
    mode = models.CharField(max_length=10, choices=Mode.choices, default=Mode.TURN)
    bundle_url = models.URLField()                         # WebView HTML/JS entry
    min_players = models.PositiveSmallIntegerField(default=2)
    max_players = models.PositiveSmallIntegerField(default=4)
    supports_bots = models.BooleanField(default=False)
    # whether a result affects economy/rankings (referee-validated)
    is_staked = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class GameSession(models.Model):
    class Status(models.TextChoices):
        LOBBY = "lobby", "Lobby (waiting)"
        PLAYING = "playing", "Playing"
        FINISHED = "finished", "Finished"
        ABANDONED = "abandoned", "Abandoned"

    definition = models.ForeignKey(GameDefinition, on_delete=models.PROTECT, related_name="sessions")
    room_id = models.CharField(max_length=32, db_index=True)
    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="hosted_games")

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.LOBBY, db_index=True)
    # authoritative state the server cares about (turn, scores, seed for RNG).
    # full render state lives client-side; this is the referee's view.
    state = models.JSONField(default=dict, blank=True)
    rng_seed = models.BigIntegerField(default=0)  # server-set, so bots/clients agree

    stake_coins = models.PositiveIntegerField(default=0)  # per-player entry, if staked
    pot_transaction = models.ForeignKey(
        "economy.Transaction", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")

    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["room_id", "status"])]

    def __str__(self):
        return f"GameSession<{self.id}> {self.definition.code}/{self.status}"


class GamePlayer(models.Model):
    class Result(models.TextChoices):
        NONE = "none", "None"
        WIN = "win", "Win"
        LOSS = "loss", "Loss"
        DRAW = "draw", "Draw"

    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name="players")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True,
                             related_name="game_plays")
    seat_slot = models.PositiveSmallIntegerField()      # player slot in the game (0..n)
    is_bot = models.BooleanField(default=False)
    team = models.PositiveSmallIntegerField(null=True, blank=True)  # for team modes
    result = models.CharField(max_length=5, choices=Result.choices, default=Result.NONE)
    score = models.IntegerField(default=0)

    class Meta:
        unique_together = ("session", "seat_slot")
        ordering = ["seat_slot"]
