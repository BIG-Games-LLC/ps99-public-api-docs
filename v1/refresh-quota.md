# Freshness & the refresh quota

This page explains how player data endpoints get their data, why a response is sometimes
a few minutes old, and the **daily budget** that governs how often fresh data is pulled.
It covers both the authenticated [`/v1/account/*`](account.md) endpoints and the public
[`/v1/players/:slug`](players.md) profile reads — both draw from the same per-player
budget.

## The short version

When you call a player data endpoint, the API does **not** read the player's live game
data on every request. Instead it keeps a recent **snapshot** of their Roblox save and
serves that. Pulling a *new* snapshot from Roblox is the expensive part, so it's
rate-limited by a per-player **daily quota**, sized so a snapshot can refresh on a steady
cadence all day long:

| Player type | Fresh snapshots per day | Works out to |
| --- | --- | --- |
| Standard | 48 | one every 30 minutes |
| VIP | 96 | one every 15 minutes |

The quota is counted **per Roblox player, per UTC day**, and it is **shared** across the
official Big Games site, public profile reads, and every third-party app. It resets at
midnight UTC. Spending a slot is the exception, not the rule — most calls are served from
the snapshot and cost nothing.

Every account response tells you exactly what happened in a `refresh` object, and the same
information is mirrored in response headers. (Public `/v1/players` responses stay
anonymous — no `refresh` object, no quota headers — see
[public profiles](#how-this-affects-public-profiles) below.)

## When a fresh snapshot is pulled (and when it isn't)

An authenticated `/v1/account/*` call spends a quota slot when **both** of these are true:

1. The current snapshot is **older than 5 minutes** (or you pass
   [`?refresh=true`](#forcing-a-refresh)), and
2. The player still has quota left for the day.

A public `/v1/players/:slug` read uses a longer window: it spends a slot only when the
snapshot is older than the player's **refresh cooldown** — 30 minutes for standard
players, 15 minutes for VIP. (That cooldown is exactly what the daily limits are derived
from, so public traffic alone can never exhaust a player's quota early.)

Otherwise the cached snapshot is served for free. The `refresh.skipped` field names the
reason a fresh pull was skipped:

| `skipped` value | Meaning |
| --- | --- |
| `"fresh"` | The snapshot is under 5 minutes old. Served from cache; no slot spent. |
| `null` | A fresh pull was attempted on this call (it either spent a slot, or the quota was already exhausted — check `quotaExhausted`). |

## Forcing a refresh

Append `?refresh=true` (or `?refresh=1`) to any `/v1/account/*` read to force a fresh
Open Cloud pull immediately, bypassing the 5-minute freshness window. A forced pull still
spends a quota slot and is still bounded by the daily limit — once the quota is exhausted,
`?refresh=true` returns the most recent snapshot with `quotaExhausted: true`, exactly like
an ordinary read. Use this for an explicit, user-initiated "refresh now"; don't attach it
to routine reads, and watch `refresh.nextRefreshEligibleAt` so you don't force a pull that
would only return identical data.

## What happens when the quota runs out

Running out of quota is **not** an error. The API still returns `200 OK` with the most
recent snapshot it has, and sets `refresh.quotaExhausted` to `true` (and the
`X-RateLimit-Quota-Exhausted: true` header). You keep getting data — it just won't get any
fresher until the quota resets at the next UTC midnight (`refresh.resetsAt`).

This is different from the per-minute [rate limits](overview.md#rate-limits), which return
`429`. The refresh quota never returns `429`.

## The `refresh` object

Present on every `/v1/account/*` response (for anonymous public reads it is `null`).

| Field | Type | Description |
| --- | --- | --- |
| `consumedThisCall` | boolean | `true` if this exact call pulled a fresh snapshot and spent a quota slot. |
| `used` | number | Slots used so far today. |
| `limit` | number | The player's daily limit (`48` standard, `96` VIP). |
| `resetsAt` | string | ISO 8601 timestamp of the next quota reset (next UTC midnight). |
| `nextRefreshEligibleAt` | string | ISO 8601 timestamp when the current snapshot becomes eligible for a fresh pull (snapshot time + 5 minutes). |
| `quotaExhausted` | boolean | `true` when the daily limit is spent. The current snapshot is still served. |
| `skipped` | string \| null | Why no fresh pull happened: `"fresh"` or `null`. See the table above. |

### Examples

Served from a recent snapshot — no slot spent:

```json
{
  "consumedThisCall": false,
  "used": 3,
  "limit": 48,
  "resetsAt": "2026-05-29T00:00:00.000Z",
  "nextRefreshEligibleAt": "2026-05-28T14:32:00.000Z",
  "quotaExhausted": false,
  "skipped": "fresh"
}
```

This call pulled fresh data and spent a slot:

```json
{
  "consumedThisCall": true,
  "used": 4,
  "limit": 48,
  "resetsAt": "2026-05-29T00:00:00.000Z",
  "nextRefreshEligibleAt": "2026-05-28T14:40:00.000Z",
  "quotaExhausted": false,
  "skipped": null
}
```

Quota spent — serving the last snapshot until reset:

```json
{
  "consumedThisCall": false,
  "used": 48,
  "limit": 48,
  "resetsAt": "2026-05-29T00:00:00.000Z",
  "nextRefreshEligibleAt": "2026-05-28T13:05:00.000Z",
  "quotaExhausted": true,
  "skipped": null
}
```

## Response headers

The same state is exposed on `/v1/account/*` responses as headers, following the standard
rate-limit header conventions. The window (`w`) is 86400 seconds — one day.

| Header | Example | Description |
| --- | --- | --- |
| `X-RateLimit-Limit` | `48` | Daily limit. |
| `X-RateLimit-Remaining` | `44` | Slots left today (`limit − used`, never below 0). |
| `X-RateLimit-Reset` | `1748476800` | Unix timestamp (seconds) of the next reset. |
| `X-RateLimit-Resource` | `player-refresh` | The resource these headers describe. |
| `RateLimit-Policy` | `48;w=86400;name=player-refresh` | The policy: limit, window in seconds, resource name. |
| `X-RateLimit-Quota-Exhausted` | `true` | Present **only** when the quota is spent. |

## How this affects public profiles

Public profile reads under [`/v1/players/:slug`](players.md) keep themselves fresh:
when a request asks for at least one view the player has made public and the snapshot is
older than the player's cooldown (**30 minutes** standard / **15 minutes** VIP), the API
pulls a fresh snapshot inline before responding, spending a slot from the same shared
daily quota. Nobody has to press anything — a public profile that people actually look at
stays no more than a cooldown (plus CDN cache time) behind the live game.

Details worth knowing:

- The responses stay anonymous: no `refresh` object, no `X-RateLimit-*` headers. Use the
  per-view `fetchedAt` (and `isStale`) to see what you got.
- Spamming a profile can't drain the player's quota — inside the cooldown every read is
  served from the snapshot for free, so public traffic paces itself to at most the daily
  limit spread across the whole day.
- If the quota is exhausted or the pull fails, the read silently serves the most recent
  snapshot instead. Public reads never error because of refresh state.
- A public player whose snapshot has aged out entirely (`no_recent_data`) is
  re-bootstrapped by the next read, so that state is now temporary rather than permanent.
- Metadata-only requests (no `?include=`), and requests that hit only non-public views,
  never trigger a pull.

## Practical guidance

- **Don't poll.** Reading the same endpoint in a tight loop won't get you newer data — it
  just burns the daily quota. Watch `refresh.nextRefreshEligibleAt` to know when newer
  data is even possible.
- **Read `refresh.skipped` and `refresh.consumedThisCall`** to understand whether you're
  looking at brand-new or cached data.
- **Treat `quotaExhausted: true` as "this is as fresh as it gets today,"** not as a
  failure. The data is still valid.
- The combined [`/v1/account/*` endpoints](account.md) all share the same per-player
  quota, so calling `inventory` then `trades` for the same player within a few minutes
  spends at most one slot.
- **Reading a public profile is enough to keep it fresh.** If you just want current data
  for a player who has opted in to public views, `GET /v1/players/:slug` on your normal
  read path is all you need — no OAuth token or forced refresh required.
