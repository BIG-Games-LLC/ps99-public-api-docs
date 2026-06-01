# v1 API overview

This page documents the conventions shared across every v1 endpoint. Read it once before diving into individual endpoint pages.

## Base URL and versioning

```
https://ps99.biggamesapi.io/v1/...
```

All v1 endpoints are served under this prefix. Within v1, we follow an additive-only compatibility policy: new fields and new view keys can appear in responses at any time without a version bump. Changes that remove or rename fields, or that alter the meaning of an existing field, require a new major version (v2). Safe to assume that anything you don't recognize in a response can be ignored.

## Response envelope

Every v1 response is one of two shapes. Success:

```json
{
  "status": "ok",
  "data": {}
}
```

Error (minimal — many responses look like this):

```json
{
  "status": "error",
  "error": {
    "message": "Human-readable description."
  }
}
```

Error (all fields — present on richer error responses):

```json
{
  "status": "error",
  "error": {
    "code": "player_not_found",
    "message": "Optional human-readable text.",
    "ignore": true
  }
}
```

Error field reference:

- `code` — Machine-readable error identifier. Present on select error responses (e.g. `/v1/players/:slug` 404s and `/v1/players/search` 500s). Not guaranteed on every error; check before using.
- `message` — Human-readable description of the error. Always a string when present.
- `ignore` — Boolean flag set by the legacy middleware (`replyError`) indicating the client may safely treat the error as non-critical — for example, show a friendly empty state instead of a hard failure. Set to `true` on the majority of error responses. Not present on every error (e.g. 401/429 responses from the auth layer omit it or set it differently).

## HTTP status codes

| Code | Meaning |
| --- | --- |
| 200 | OK — request succeeded. |
| 400 | Bad request — a required or malformed query/path parameter. Returned by `/v1/players` (missing/invalid `page`/`pageSize`/`sort`/`sortOrder`), `/v1/leagues/:name`, and the `:userId`/`:battleId` lookups under `/v1/clans` and `/v1/leagues`. |
| 401 | Missing, invalid, expired, or rotated bearer token. Only returned by `/v1/account/*` endpoints. |
| 403 | Token does not have the required scope for the requested resource. Only returned by `/v1/account/*` endpoints. |
| 404 | Resource not found. Returned by `/v1/players/:slug`, `/v1/clans/players/:userId`, `/v1/clans/battles/:battleId`, and `/v1/leagues/{:name,players/:userId}`. |
| 429 | Rate-limited (per-minute limits). The response includes a `Retry-After` header (value in seconds). The daily refresh quota does **not** use 429 — see [Refresh quota](#refresh-quota-v1account) below. |
| 500 | Internal server error. |

Note: 200 also covers some "soft" cases. A `/v1/account/*` call for a player with no save returns `200` with `data: null`; an exhausted daily refresh quota still returns `200` with the last snapshot. See [Freshness & the refresh quota](refresh-quota.md).

## Per-view envelope

`GET /v1/players/:slug` returns a `views` map where each key is a view name and each value is one of the following shapes. The full list of view keys and what each one returns lives in [v1/players.md](players.md#public-views).

Data is available:

```json
{
  "available": true,
  "data": {},
  "isStale": false,
  "fetchedAt": "2026-05-13T12:00:00.000Z"
}
```

`available: true, isStale: true` is also valid — the snapshot is served but is older than 7 days.

Player has not opted in for this view:

```json
{
  "available": false,
  "reason": "not_public"
}
```

Player opted in but no save snapshot exists yet:

```json
{
  "available": false,
  "reason": "no_recent_data",
  "fetchedAt": null
}
```

View name is recognized but not yet implemented (defensive; not expected under normal use):

```json
{
  "available": false,
  "reason": "not_implemented"
}
```

Note: `isStale === true` means the snapshot (the cached save data) is older than 7 days. The data is still served — staleness is advisory.

## Rate limits

### Authenticated endpoints (`/v1/account/*`)

Rate limits are enforced per API key, per linked player, and per app:

| Dimension | Limit |
| --- | --- |
| Per API key per minute | 60 requests |
| Per player per minute | 120 requests |
| Per app per minute | 600 requests |

When any limit is exceeded the server responds with HTTP 429:

```json
{
  "status": "error",
  "error": {
    "message": "Rate limit exceeded."
  }
}
```

The response also includes a `Retry-After` header whose value is the number of seconds to wait before retrying:

```
Retry-After: 42
```

### Refresh quota (`/v1/account/*`)

Separate from the per-minute limits above, account endpoints enforce a **daily quota on
how often fresh data is pulled from Roblox** — 10/day for standard players and 30/day for
VIP, counted per player and shared across all apps. Most calls are served from a cached
snapshot and cost nothing; only an actual fresh pull spends a slot. Running out does
**not** return 429 — you keep getting the last snapshot with `quotaExhausted: true`.

Every account response carries a `refresh` object and these headers:

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 6
X-RateLimit-Reset: 1748476800
X-RateLimit-Resource: player-refresh
RateLimit-Policy: 10;w=86400;name=player-refresh
```

The full behavior — when a refresh happens, the `refresh` object fields, and how to handle
exhaustion — lives in [Freshness & the refresh quota](refresh-quota.md).

### Public endpoints (`/v1/players/*`, `/v1/clans/*`, `/v1/leagues/*`, legacy `/api/*`)

These endpoints are unauthenticated. Stay under 100 requests per minute per IP and cache responses locally whenever possible. Bursting over this threshold will result in a 429.

## Caching

The server sets explicit `Cache-Control` headers on every response. Respect them — CDN edge nodes and browser caches use these values to avoid hammering the origin.

| Endpoint | `Cache-Control` |
| --- | --- |
| `/v1/players/:slug` | `public, max-age=300, s-maxage=900, stale-while-revalidate=1800` |
| `/v1/players/search` | `public, max-age=30, s-maxage=60, stale-while-revalidate=120` |
| `/v1/players/featured` | `public, max-age=60, s-maxage=300, stale-while-revalidate=600` |
| `/v1/clans/*` | `public, max-age=60, s-maxage=180, stale-while-revalidate=600` |
| `/v1/leagues/*` | `public, max-age=60, s-maxage=180, stale-while-revalidate=600` |
| `/v1/account/*` | `private, no-cache` |

The `private, no-cache` value on account endpoints means **never share responses across users**. Do not store them in a shared cache layer.

## Item enrichment

Items returned by inventory, trades, booth, and mail endpoints are enriched server-side before delivery. Each item object includes display name, icon, rarity, category, recent average price (RAP), exists count, and variant flags (golden, rainbow, shiny). See [v1/account.md](account.md#enriched-item-shape) for the field-by-field reference.

## Roblox user resolution

In trades, booth, and mail responses you will see `otherParty: { uid, displayName }` blocks. The `displayName` field is resolved by calling Roblox's user API at response time. If Roblox returns no display name for a given user ID, `displayName` falls back to the stringified `uid`.
