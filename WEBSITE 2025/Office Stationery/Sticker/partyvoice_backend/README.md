# PartyVoice Backend — WePlay-style Social Audio App

Complete, runnable Django backend, built fresh (no prior code reused), across
all 5 phases. Stack: Django 5 + DRF + Channels + Celery + PostgreSQL + Redis.
Real-time audio/RTC via ZEGOCLOUD (server mints tokens; client uses the kits).

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # fill in secrets (ZEGO_*, etc.)
export DJANGO_SECRET_KEY=...    # or put in .env and load it
python manage.py migrate        # boots on SQLite + in-memory channels with no extra services
python manage.py createsuperuser
python manage.py runserver      # REST API
# For WebSockets + Celery in production, run under ASGI (daphne/uvicorn) with Redis:
#   daphne partyvoice.asgi:application
#   celery -A partyvoice worker -l info
```
With no POSTGRES_* / REDIS_URL set, the project runs on SQLite and an in-memory
channel layer so it boots with zero external services for first-run testing.
Set those env vars to switch to Postgres + Redis for real deployments.

## Verified
- `manage.py check` — 0 issues
- `manage.py makemigrations` — all 15 apps, no drift
- `manage.py migrate` — full schema builds against a real DB
- Economy ledger, families/feed, weddings/mentorship/loot/inventory, and
  fraud/moderation algorithms all tested green against a real ORM.

## Project layout
- partyvoice/      settings, urls, asgi, wsgi, celery (the project package)
- manage.py        Django entry point
- accounts/        User + Profile (Phase 1)
- rtc/             ZEGOCLOUD Token04 generator, token endpoint, WS JWT auth (Phase 1)
- rooms/           Room lifecycle, seat-sync consumer, chat, bans, PK battles (P1, P3)
- economy/         Double-entry ledger, wallet, gifts, IAP, leaderboards (Phase 2)
- engagement/      VIP, daily login, tasks, referrals, redeem codes, loot boxes (P2, P4)
- payouts/         Diamond->cash with KYC, escrow, fraud gates, audit (Phase 2)
- games/           Game framework, sessions, staked referee, sync consumer (Phase 3)
- social/          Families/clans, Moments feed, follow graph (Phase 3)
- relationships/   Weddings, mentorship (Phase 4)
- inventory/       Cosmetic items, ownership, equipping (Phase 4)
- events/          Time-limited events engine (Phase 4)
- moderation/      Reports, cases, action tiers, auto-mod (Phase 5)
- fraud/           Velocity, collusion/laundering detection, device fingerprint (Phase 5)
- observability/   Audit log, analytics pipeline (Phase 5)
- admin_tools/     Moderation queue API, Celery maintenance tasks (Phase 5)

Apps with models keep them either in models.py or in topic modules
(social/families.py, social/feed.py, relationships/weddings.py,
relationships/mentorship.py) that are re-exported via the app's models.py.

## Integration points to wire (left as clearly-marked stubs by design)
- economy/gift_service._google_play_verify : Google Play Developer API (service account)
- payouts : KYC vendor (Onfido/Sumsub) + payout processor + per-region PayoutPolicy + legal review
- moderation : audio/text/image classifier services
- All ZEGO_* settings + the 32-char ServerSecret (server-side ONLY — never ship to client)

## Realtime endpoints (ASGI / Channels)
- ws/room/<room_id>/        seat sync, presence, room chat, moderation
- ws/game/<session_id>/     game state sync (WebView bridge transport)
