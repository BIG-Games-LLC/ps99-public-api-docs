# /v1/clans

The `/v1/clans` endpoints expose aggregated data drawn from a rolling sample of the top clans in Pet Simulator 99, ranked by all-time battle points. They replace the older [`/api/clan*`](../legacy/README.md) family of routes, offering structured player and battle-level breakdowns in a consistent envelope format (see [overview.md](overview.md) for envelope and caching details). No authentication is required for any of these endpoints.

Data is sampled rather than exhaustive. By default the player aggregate samples the top 25 clans; the battle detail endpoint samples the top 100. A player or clan that does not appear in a response is not guaranteed to be absent from the game — it simply means none of their affiliated clans fell within the current sample. The server maintains a 3-minute internal cache for each aggregate; the HTTP response carries a `public, max-age=60, s-maxage=180, stale-while-revalidate=600` cache header, so browsers hold results for 60 seconds and shared/edge caches for 180 seconds (and may serve stale content for up to a further 600 seconds while they revalidate).

These endpoints are read-only and safe to call from a browser, a server, or a public CDN edge function. Rate limits follow the same global policy as the rest of the v1 API.

> **Heads-up on field casing.** The aggregate endpoints (`/v1/clans/players`, `/v1/clans/players/:userId`) return fields in **PascalCase** (`UserID`, `DisplayName`, `Clan.Name`). The battle detail endpoint (`/v1/clans/battles/:battleId`) returns fields in **camelCase** (`userId`, `displayName`, `clan.name`). A single typed model won't fit both — define them separately.

---

## GET /v1/clans/players

Returns a snapshot of every player seen across the sampled top clans, along with their battle statistics aggregated across all battles stored for those clans. This is the broadest view: one array covering every contributor found in the sample.

**No path or query parameters.**

### Example request

```bash
curl 'https://ps99.biggamesapi.io/v1/clans/players'
```

```python
import requests
r = requests.get('https://ps99.biggamesapi.io/v1/clans/players')
print(r.json())
```

### Example response (200)

```json
{
  "status": "ok",
  "data": {
    "players": [
      {
        "UserID": 123456789,
        "DisplayName": "CoolPlayer",
        "ActiveBattlePoints": 48200,
        "AllTimeDiamonds": 9100000,
        "TotalBattles": 14,
        "EarnedMedals": 9,
        "AvgPlace": 3.2,
        "Clan": {
          "Name": "EliteSquad",
          "Icon": "rbxassetid://12345678",
          "CountryCode": "US",
          "Place": 2
        }
      },
      {
        "UserID": 987654321,
        "DisplayName": "AnotherUser",
        "ActiveBattlePoints": 0,
        "AllTimeDiamonds": 3400000,
        "TotalBattles": 7,
        "EarnedMedals": 3,
        "AvgPlace": null,
        "Clan": {
          "Name": "TopGuild",
          "Icon": "rbxassetid://87654321",
          "CountryCode": "BR"
        }
      }
      // ...
    ],
    "activeBattleConfigName": "GuildBattle_Spring2025",
    "sampledClans": 25,
    "loadError": null
  }
}
```

**Response fields**

| Field | Type | Description |
|---|---|---|
| `players` | array | One entry per unique player found across all sampled clans. |
| `players[].UserID` | number | Roblox user ID. |
| `players[].DisplayName` | string | Roblox display name resolved at aggregate time; falls back to the string form of `UserID` if resolution fails. |
| `players[].ActiveBattlePoints` | number | Points contributed in the currently-live battle, or `0` if none is active. |
| `players[].AllTimeDiamonds` | number | Cumulative diamond contributions recorded in the clan's `DiamondContributions.AllTime` data. |
| `players[].TotalBattles` | number | Number of battles in the sample where this player has a contribution entry. |
| `players[].EarnedMedals` | number | Count of those battles where the clan earned a medal. |
| `players[].AvgPlace` | number \| null | Mean reported clan placement across battles where a numeric place was recorded; `null` if no placement data is available. |
| `players[].Clan` | object | The clan the player was first seen in during aggregation. |
| `players[].Clan.Name` | string | Clan name. |
| `players[].Clan.Icon` | string | Asset ID string for the clan icon. |
| `players[].Clan.CountryCode` | string | Two-letter country code. |
| `players[].Clan.Place` | number | _(Optional)_ Clan's current place in the active battle; omitted when no active battle exists. |
| `activeBattleConfigName` | string \| null | The `configName` of the currently-live clan battle, or `null` when none is active. |
| `sampledClans` | number | How many clans were included in this aggregate (default 25). |
| `loadError` | null \| string | `null` on success; an error message string if the underlying clan collection could not be loaded (players array will be empty). |

### Other responses

- `500 (unhandled error in the aggregator/loader)` — Aggregator threw an unexpected error. Envelope: `{ "status": "error", "error": { "message": "Could not load player aggregate.", "ignore": true } }`.

### Notes

- Cache: `public, max-age=60, s-maxage=180, stale-while-revalidate=600`
- The aggregate is rebuilt at most once every 3 minutes server-side. Subsequent requests within that window return the cached result instantly.
- A player may appear in the array even when `loadError` is non-null only if partial data was returned; in practice `loadError` correlates with an empty `players` array.

---

## GET /v1/clans/players/:userId

Looks up a single player within the same player aggregate used by `/v1/clans/players`. This is a filtered view — it returns the same data for one player plus metadata about the current battle state, or a 404 if the player is not present in the sample.

**Path parameters**

| Parameter | Type | Description |
|---|---|---|
| `userId` | integer | Roblox user ID. Must be a finite positive integer. |

### Example request

```bash
curl 'https://ps99.biggamesapi.io/v1/clans/players/123456789'
```

```python
import requests
r = requests.get('https://ps99.biggamesapi.io/v1/clans/players/123456789')
print(r.json())
```

### Example response (200)

```json
{
  "status": "ok",
  "data": {
    "player": {
      "UserID": 123456789,
      "DisplayName": "CoolPlayer",
      "ActiveBattlePoints": 48200,
      "AllTimeDiamonds": 9100000,
      "TotalBattles": 14,
      "EarnedMedals": 9,
      "AvgPlace": 3.2,
      "Clan": {
        "Name": "EliteSquad",
        "Icon": "rbxassetid://12345678",
        "CountryCode": "US",
        "Place": 2
      }
    },
    "activeBattleId": "GuildBattle_Spring2025",
    "hasActiveBattle": true,
    "sampledClans": 25
  }
}
```

**Response fields**

| Field | Type | Description |
|---|---|---|
| `player` | object | The player snapshot. Fields are identical to entries in `GET /v1/clans/players`. |
| `activeBattleId` | string \| null | Same value as `activeBattleConfigName` from the aggregate; the `configName` of the live battle or `null`. |
| `hasActiveBattle` | boolean | `true` when `activeBattleId` is a non-empty string. |
| `sampledClans` | number | Number of clans included in the underlying aggregate. |

### Other responses

- `400 Invalid userId.` — `userId` is not a finite positive integer (e.g. `0`, a negative number, or a non-numeric string). Envelope: `{ "status": "error", "error": { "message": "Invalid userId.", "ignore": true } }`.
- `404 Player not found in sampled clans.` — The aggregate loaded successfully but the requested user ID was not found in any of the sampled clans. Envelope: `{ "status": "error", "error": { "message": "Player not found in sampled clans.", "ignore": true } }`.
- `500 (unhandled error in the aggregator/loader)` — Aggregator threw an unexpected error. Envelope: `{ "status": "error", "error": { "message": "Could not load player lookup.", "ignore": true } }`.

### Notes

- Cache: `public, max-age=60, s-maxage=180, stale-while-revalidate=600`
- A 404 does not mean the player does not exist in the game. It means their clan was not among the top 25 sampled. Check `sampledClans` in a successful response to understand coverage.
- The 404 response uses `Cache-Control: no-store` so negative results are not cached downstream.

---

## GET /v1/clans/battles/:battleId

Returns detailed information about a specific clan battle: metadata, aggregate stats, and ranked leaderboards for both clans and individual players. The leaderboard is built from the top 100 clans by all-time points and capped at the top 200 individual contributors.

**Path parameters**

| Parameter | Type | Description |
|---|---|---|
| `battleId` | string | The battle's `configName` (e.g. `GuildBattle_Spring2025`). Must contain only `A-Z`, `a-z`, `0-9`, and `_`. |

### Example request

```bash
curl 'https://ps99.biggamesapi.io/v1/clans/battles/GuildBattle_Spring2025'
```

```python
import requests
r = requests.get('https://ps99.biggamesapi.io/v1/clans/battles/GuildBattle_Spring2025')
print(r.json())
```

### Example response (200)

```json
{
  "status": "ok",
  "data": {
    "meta": {
      "id": "GuildBattle_Spring2025",
      "title": "Spring 2025 Clan Battle",
      "startTime": 1746057600,
      "finishTime": 1746144000,
      "durationSeconds": 86400,
      "hasGoals": true,
      "state": "past",
      "headlineReward": null,
      "placementRewards": []
    },
    "stats": {
      "participatingClans": 48,
      "sampledClans": 100,
      "totalClanPoints": 18340000,
      "totalContributors": 512,
      "bestMedal": "gold"
    },
    "topClans": [
      {
        "rank": 1,
        "name": "EliteSquad",
        "icon": "rbxassetid://12345678",
        "countryCode": "US",
        "members": 30,
        "memberCapacity": 50,
        "points": 4200000,
        "reportedPlace": 1,
        "medal": "gold",
        "contributorCount": 28
      }
      // ...
    ],
    "topPlayers": [
      {
        "rank": 1,
        "userId": 123456789,
        "displayName": "CoolPlayer",
        "points": 980000,
        "share": 0.0534,
        "clan": {
          "name": "EliteSquad",
          "icon": "rbxassetid://12345678",
          "countryCode": "US",
          "place": 1
        }
      }
      // ...
    ]
  }
}
```

**`meta` fields**

| Field | Type | Description |
|---|---|---|
| `id` | string | The battle `configName`, echoed back. |
| `title` | string | Human-readable battle title; falls back to `id` if not set. |
| `startTime` | number \| null | Unix timestamp (seconds) of battle start. `null` if not configured. |
| `finishTime` | number \| null | Unix timestamp (seconds) of battle end. `null` if not configured. |
| `durationSeconds` | number \| null | `finishTime - startTime`; `null` when either timestamp is absent. |
| `hasGoals` | boolean | Whether this battle has goal-based milestones. |
| `state` | string | `"upcoming"`, `"live"`, or `"past"` — derived from current time vs. `startTime`/`finishTime`. |
| `headlineReward` | any \| null | Top reward object from the battle config, or `null` if not set. |
| `placementRewards` | array | Ordered placement reward entries from the battle config; empty array if none. |
| `tieredRewards` | object | Tiered reward buckets keyed by `good`, `bronze`, `silver`, `gold`, each an array of reward item objects. Omitted entirely when the battle config has no tiered rewards. |

**`stats` fields**

| Field | Type | Description |
|---|---|---|
| `participatingClans` | number | How many sampled clans have a non-zero points entry for this battle. |
| `sampledClans` | number | Total clans checked (default 100). |
| `totalClanPoints` | number | Sum of all clan points across participating clans. |
| `totalContributors` | number | Total individual contribution records counted (not deduplicated across clans). |
| `bestMedal` | string \| null | Highest medal earned by any sampled clan. Values: `"gold"`, `"silver"`, `"bronze"`, `"good"`, or `null`. |

**`topClans[]` fields**

| Field | Type | Description |
|---|---|---|
| `rank` | number | 1-based rank within this response. |
| `name` | string | Clan name. |
| `icon` | string | Asset ID string for the clan icon. |
| `countryCode` | string | Two-letter country code. |
| `members` | number | _(Optional)_ Current member count; omitted when the clan's member list is unavailable. |
| `memberCapacity` | number | Maximum member slots. |
| `points` | number | Clan's total points in this battle. |
| `reportedPlace` | number \| null | Official placement from the clan's stored battle data; `null` if not recorded. |
| `medal` | string \| null | Medal earned: `"gold"`, `"silver"`, `"bronze"`, `"good"`, or `null`. |
| `contributorCount` | number | Number of individual contribution records for this clan in this battle. |

**`topPlayers[]` fields**

| Field | Type | Description |
|---|---|---|
| `rank` | number | 1-based rank within this response (up to 200 entries). |
| `userId` | number | Roblox user ID. |
| `displayName` | string | Roblox display name; falls back to string form of `userId` if resolution fails. |
| `points` | number | Points contributed by this player. When a player appears in multiple sampled clans, only the highest contribution is kept. |
| `share` | number | This player's points divided by `stats.totalClanPoints`; `0` when total is zero. |
| `clan` | object | The clan associated with this player's highest contribution. |
| `clan.name` | string | Clan name. |
| `clan.icon` | string | Asset ID string. |
| `clan.countryCode` | string | Two-letter country code. |
| `clan.place` | number \| null | Clan's reported place in this battle, or `null`. |

### Other responses

- `400 Invalid battleId.` — `battleId` contains characters outside `[A-Za-z0-9_]` or is empty. Envelope: `{ "status": "error", "error": { "message": "Invalid battleId.", "ignore": true } }`.
- `404 Battle not found.` — No matching battle config exists in the database. Envelope: `{ "status": "error", "error": { "message": "Battle not found.", "ignore": true } }`.
- `500 (unhandled error in the aggregator/loader)` — Loader threw an unexpected error. Envelope: `{ "status": "error", "error": { "message": "Could not load battle detail.", "ignore": true } }`.

### Notes

- Cache: `public, max-age=60, s-maxage=180, stale-while-revalidate=600`
- The 404 response uses `Cache-Control: no-store`.
- `topPlayers` is capped at 200 entries, sorted by points descending.
- `topClans` is sorted by `reportedPlace` ascending (nulls last), then by `points` descending as a tiebreaker.
- The response also includes `podium` (the top 3 players, same shape as `topPlayers` entries) and `isActive` (a boolean, currently always `false` at the route layer) at the top level of `data`. These are supplemental fields and may change in a future version.

---

## Caveats

- **Sample coverage:** Player and clan data is drawn from a fixed-size sample of top clans. Missing data means not covered by the sample, not absent from the game.
- **Server cache:** Each aggregate (player list or battle detail) is held in memory for 3 minutes. The very first request after a cache miss may take slightly longer while the aggregate is rebuilt.
- **Display names:** Roblox display names are resolved in bulk at aggregate time. If the Roblox API is unavailable, names fall back to the numeric user ID as a string.
