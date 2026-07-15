# PartyVoice — Django Admin Guide

A full admin panel is wired so you can manage the app without touching code.

## Access
```bash
python manage.py migrate
python manage.py seed_themes          # seed the 9 room themes
python manage.py createsuperuser      # make your admin login
python manage.py runserver
```
Open http://127.0.0.1:8000/admin/ and log in.

## What you can manage (49 models across 12 sections)

**Economy**
- **Gifts** — add/edit gifts: code, name, tier, coin cost, diamond value,
  icon + SVGA animation URL, active flag, sort order. (Inline-edit price &
  active right in the list.)
- **Wallets** — view/adjust user coin & diamond balances (ledger is the source
  of truth; prefer transactions for real money moves).
- **Transactions / Ledger entries** — read-only audit trail (created by the
  service layer; not hand-editable, by design).
- **Gift events** — history of who sent what.

**Engagement (tokens & offers)**
- **VIP tiers** — levels, wealth thresholds, monthly coin price, perks.
- **User VIP** — who has which tier and when it expires.
- **Redeem codes** — promo/token codes: reward, max uses, expiry, active.
- **Tasks** — daily/weekly tasks: trigger, target, coin reward.
- **Daily login rewards** — per-day coin rewards.
- **Loot tables** — gacha offers with weighted **loot rewards** (edited inline).
- **Referrals** — invite tracking.

**Rooms**
- **Rooms** — every room: type, category, status, theme, seat count, owner.
- **Room themes** — the background-theme store: name, coin cost, default/active,
  sort order (inline-editable). This is where you add new purchasable themes.
- **Room bans**, seats, theme ownership.

**Social** — Families (with member inline), Posts (with hide/unhide bulk
actions for moderation), comments, likes, follows.

**Other sections** — Accounts/Profiles, Relationships (rings/marriages/
mentorships), Inventory (cosmetic items), Events (with milestone inlines),
Payouts (KYC/requests/policies — review here, mutate via services), Moderation
(reports/cases/actions), Games.

## Common tasks
- **Add a new gift**: Economy → Gifts → Add. Set code, name, tier, coin_cost,
  and the animation_url (the .svga for the on-screen animation).
- **Create a promo code**: Engagement → Redeem codes → Add (set reward, max
  uses, expiry).
- **Add a room theme/offer**: Rooms → Room themes → Add (key, name, coin_cost,
  assets JSON for colors/accent). Set is_active to publish.
- **Run a limited offer/event**: Events → Events → Add, with milestones inline.
- **Moderate**: Social → Posts → select → "Hide selected posts".

## Notes
- Money/ledger rows are intentionally read-only in admin — they're written by
  the tested service layer so balances can't drift. Adjust via top-ups/grants.
- Coin top-up *packages* (the IAP price tiers) live in client/config + your
  store console, not the DB; everything else above is DB-managed here.
