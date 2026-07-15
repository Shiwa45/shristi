"""
economy/leaderboards.py — Wealth/charm rankings.

Hot path uses Redis sorted sets (ZADD/ZINCRBY/ZREVRANGE) for O(log n) updates
and instant top-N reads. Periodic Celery rollups snapshot to Postgres for
historical periods (daily/weekly/monthly) and durability.

  wealth = lifetime coins spent (gifter side)
  charm  = lifetime diamonds earned (recipient side)

Keys are namespaced by metric + scope + period so global/regional/room and
daily/weekly/monthly all coexist.
"""

import time

import redis
from django.conf import settings

_client = None


def _redis():
    """Lazily create the Redis client so import never blocks on a connection."""
    global _client
    if _client is None:
        _client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client


def _key(metric: str, scope: str, period: str) -> str:
    # e.g. lb:wealth:global:all  | lb:charm:room_ab12:daily:2026-06-18
    if period == "all":
        return f"lb:{metric}:{scope}:all"
    bucket = _period_bucket(period)
    return f"lb:{metric}:{scope}:{period}:{bucket}"


def _period_bucket(period: str) -> str:
    t = time.gmtime()
    if period == "daily":
        return time.strftime("%Y-%m-%d", t)
    if period == "weekly":
        return time.strftime("%Y-W%U", t)
    if period == "monthly":
        return time.strftime("%Y-%m", t)
    return "all"


def add_score(metric: str, user_public_id: str, delta: int, *,
              scope: str = "global", periods=("all", "daily", "weekly", "monthly")):
    """Increment a user's score across all tracked periods atomically.

    NEVER raises. The leaderboard is a nice-to-have cache: if Redis is down, a
    gift must still succeed. Letting a cache write take down the gift endpoint
    would mean the user is charged and then shown an error — the worst possible
    failure for the feature the whole business runs on. The DB (wallet
    lifetime_* columns) remains the source of truth, and the leaderboard view
    falls back to it.
    """
    try:
        pipe = _redis().pipeline()
        for period in periods:
            key = _key(metric, scope, period)
            pipe.zincrby(key, delta, user_public_id)
            if period != "all":
                pipe.expire(key, _ttl_for(period))
        pipe.execute()
    except Exception:  # noqa: BLE001 — deliberately swallow: cache is optional
        pass


def _ttl_for(period: str) -> int:
    return {"daily": 60 * 60 * 36, "weekly": 60 * 60 * 24 * 10,
            "monthly": 60 * 60 * 24 * 40}.get(period, 60 * 60 * 24)


def top_n(metric: str, *, scope: str = "global", period: str = "all", n: int = 50):
    """Return [(user_public_id, score, rank), ...] highest first."""
    key = _key(metric, scope, period)
    rows = _redis().zrevrange(key, 0, n - 1, withscores=True)
    return [(uid, int(score), idx + 1) for idx, (uid, score) in enumerate(rows)]


def rank_of(metric: str, user_public_id: str, *, scope: str = "global", period: str = "all"):
    key = _key(metric, scope, period)
    rank = _redis().zrevrank(key, user_public_id)
    score = _redis().zscore(key, user_public_id)
    if rank is None:
        return None
    return {"rank": rank + 1, "score": int(score or 0)}
