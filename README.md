# Pet Simulator 99 Public API

HTTP API for Pet Simulator 99 game data, public player profiles, and authenticated player account access.

```
https://ps99.biggamesapi.io/
```

The v1 namespace (`/v1/*`) is the new surface covering authenticated player data, public player
profiles, clan aggregations, and league leaderboards. See [v1/overview.md](v1/overview.md) for the full reference.

The legacy namespace (`/api/*`) is the original API — fully supported, not deprecated, and still
the right choice for pet data, item data, RAP, clan listings, and exists lookups. See
[legacy/README.md](legacy/README.md) for the full reference.

## Choose your path

| I want to... | Use | Auth? |
| --- | --- | --- |
| Get game data (pets, items, RAP, clans, exists, collections) | [/api/*](legacy/README.md) | None |
| Look up a player's public profile | [/v1/players/](v1/players.md) | None |
| Browse clan and league leaderboards | [/v1/clans/](v1/clans.md), [/v1/leagues/](v1/leagues.md) | None |
| Read a player's personal data (with their permission) | [/v1/account/](v1/account.md) | OAuth (see [authentication](v1/authentication.md)) |

## Quickstart

Want to make your first call right now? Walk through the [Quickstart](quickstart.md) — about five minutes.

## Documentation

- [Quickstart](quickstart.md) — from zero to a working call in 5 minutes.
- [v1 overview](v1/overview.md) — response envelope, errors, rate limits, caching.
- [Authentication (OAuth 2.0 + PKCE)](v1/authentication.md) — how to issue and use bearer tokens.
- [Freshness & refresh quota](v1/refresh-quota.md) — how account data is cached and the daily fresh-pull budget.
- [v1 /players](v1/players.md) — public profile lookup, search, featured, list, total.
- [v1 /account](v1/account.md) — 7 authenticated endpoints (inventory, profile, extendedProfile, itemIndex, trades, booth, mail).
- [v1 /clans](v1/clans.md) — players aggregator, single-player lookup, battle detail.
- [v1 /leagues](v1/leagues.md) — leagues leaderboard, league detail, top contributors.
- [Legacy /api endpoints](legacy/README.md) — the original API.
- [Changelog](changelog/) — release notes.
- [Terms](TERMS.md)

## Response shape

Every response from both `/v1/*` and `/api/*` uses the same envelope: a `status` field of `"ok"`
or `"error"`, paired with either a `data` field or an `error` object.

```json
{ "status": "ok", "data": { ... } }
```

```json
{ "status": "error", "error": { "message": "Rate limit exceeded.", "ignore": true } }
```

Field-by-field details live in [v1/overview.md](v1/overview.md#response-envelope).

## Versioning

v1 is shape-stable within the version: fields will not be renamed or removed without a major
version bump. Additive changes — new fields or new view keys in player profiles — are not
considered breaking and may appear at any time. Removals or renames bump to v2. The legacy
`/api/*` surface remains supported indefinitely. See
[v1/overview.md](v1/overview.md#base-url-and-versioning) for detail.

## Support

Open an issue at <https://github.com/BIG-Games-LLC/ps99-public-api-docs/issues>.
