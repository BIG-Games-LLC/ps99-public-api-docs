# Public profiles refresh themselves + bigger refresh quotas

**Released:** 2026-07-27

## Added

- **Public reads now trigger refreshes.** `GET /v1/players/:slug` no longer serves
  only whatever snapshot happens to exist. When a request asks for at least one public
  view and the snapshot is older than the player's cooldown — **30 minutes** standard,
  **15 minutes** VIP — the API pulls a fresh snapshot from Roblox inline before
  responding. Players no longer need to press Refresh on the Big Games site (or authorize
  an app) for their public profile to stay current; reading it is enough. See
  [v1/refresh-quota.md](../v1/refresh-quota.md#how-this-affects-public-profiles) and
  [v1/players.md](../v1/players.md#data-freshness).

## Changed

- **Daily refresh limits raised: 10 → 48 standard, 30 → 96 VIP.** The limits are now
  derived from the public cooldown cadence (one refresh per 30 / 15 minutes across a
  UTC day). The quota remains per-player and shared — now across the official site,
  public profile reads, and every third-party app. `refresh.limit` and the
  `X-RateLimit-*` headers on `/v1/account/*` responses report the new numbers.
- **`no_recent_data` is now temporary.** Previously a public player whose snapshot had
  aged out stayed in `no_recent_data` until they visited the site. A public read now
  re-bootstraps the snapshot, so a follow-up request shortly after usually has data.
- Public `/v1/players` responses are unchanged in shape: still no `refresh` object and
  no quota headers. Use each view's `fetchedAt` / `isStale` to judge freshness. If a
  player's quota is exhausted or the pull fails, public reads silently serve the most
  recent snapshot — they never error because of refresh state.
