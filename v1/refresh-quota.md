# Freshness & the refresh quota

This page explains how `/v1/account/*` endpoints get their data, why a response is
sometimes a few minutes old, and the **daily budget** that governs how often fresh data
is pulled. If you only ever read public profiles under [`/v1/players`](players.md), you
can skip this page — the quota applies to authenticated account reads only.

## The short version

When you call an account endpoint, the API does **not** read the player's live game data
on every request. Instead it keeps a recent **snapshot** of their Roblox save and serves
that. Pulling a *new* snapshot from Roblox is the expensive part, so it's rate-limited by
a per-player **daily quota**:

| Player type | Fresh snapshots per day |
| --- | --- |
| Standard | 10 |
| VIP | 30 |

The quota is counted **per Roblox player, per UTC day**, and it is **shared** across the
official Big Games site and every third-party app. It resets at midnight UTC. Spending a
slot is the exception, not the rule — most calls are served from the snapshot and cost
nothing.

Every account response tells you exactly what happened in a `refresh` object, and the same
information is mirrored in response headers.

## When a fresh snapshot is pulled (and when it isn't)

A call only spends a quota slot when **all** of these are true:

1. The current snapshot is **older than 5 minutes**, and
2. The player has **logged into the game since** that snapshot was taken, and
3. The player still has quota left for the day.

Otherwise the cached snapshot is served for free. The `refresh.skipped` field names the
reason a fresh pull was skipped:

| `skipped` value | Meaning |
| --- | --- |
| `"fresh"` | The snapshot is under 5 minutes old. Served from cache; no slot spent. |
| `"cache-extension"` | The player hasn't logged in since the snapshot was taken, so a re-pull would return identical data. Served from cache; no slot spent. |
| `null` | A fresh pull was attempted on this call (it either spent a slot, or the quota was already exhausted — check `quotaExhausted`). |

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
| `limit` | number | The player's daily limit (`10` standard, `30` VIP). |
| `resetsAt` | string | ISO 8601 timestamp of the next quota reset (next UTC midnight). |
| `nextRefreshEligibleAt` | string | ISO 8601 timestamp when the current snapshot becomes eligible for a fresh pull (snapshot time + 5 minutes). |
| `quotaExhausted` | boolean | `true` when the daily limit is spent. The current snapshot is still served. |
| `skipped` | string \| null | Why no fresh pull happened: `"fresh"`, `"cache-extension"`, or `null`. See the table above. |

### Examples

Served from a recent snapshot — no slot spent:

```json
{
  "consumedThisCall": false,
  "used": 3,
  "limit": 10,
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
  "limit": 10,
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
  "used": 10,
  "limit": 10,
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
| `X-RateLimit-Limit` | `10` | Daily limit. |
| `X-RateLimit-Remaining` | `6` | Slots left today (`limit − used`, never below 0). |
| `X-RateLimit-Reset` | `1748476800` | Unix timestamp (seconds) of the next reset. |
| `X-RateLimit-Resource` | `player-refresh` | The resource these headers describe. |
| `RateLimit-Policy` | `10;w=86400;name=player-refresh` | The policy: limit, window in seconds, resource name. |
| `X-RateLimit-Quota-Exhausted` | `true` | Present **only** when the quota is spent. |

## How this affects public profiles

Public reads under [`/v1/players`](players.md) are anonymous: they **never** trigger a
fresh pull and **never** consume quota. They serve whatever snapshot already exists,
which is why a public profile can lag behind the live game. A snapshot becomes fresher
only when the player themselves (or an app they've authorized) reads their own account
data and a refresh slot is spent. Anonymous responses carry no `refresh` object and no
`X-RateLimit-*` headers.

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
