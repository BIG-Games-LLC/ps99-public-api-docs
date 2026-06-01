# /v1/leagues

The `/v1/leagues` endpoints expose Pet Simulator 99 **leagues** — small competitive teams (up to four players) that compete on a single continuous points leaderboard. Leagues are similar to [clans](clans.md) but simpler: there are no battles, medals, diamonds, or descriptions. A league has a name, an icon, an owner, a roster, and a running `Points` total built from each member's contributions.

Unlike `/v1/clans` — whose plain clan list still lives in the legacy [`/api/clans`](../legacy/README.md) routes — leagues have no legacy endpoints, so `/v1/leagues` carries the leaderboard itself. All four endpoints are read-only, require no authentication, and return the standard envelope (see [overview.md](overview.md) for envelope and caching details).

The leaderboard is an exact, indexed query over every league. The contributor endpoints (`/v1/leagues/players`, `/v1/leagues/players/:userId`) are drawn from a rolling sample of the top 500 point contributions and are rebuilt at most once every 3 minutes server-side.

> **Field casing.** League and player **entity** fields are returned in **PascalCase** (`UserID`, `DisplayName`, `League.Name`), matching the `/v1/clans/players` aggregate endpoints. The pagination/container keys (`leagues`, `players`, `total`, `page`, `pageSize`) are lowercase.

---

## GET /v1/leagues

Returns a page of leagues ranked by the chosen metric. This is the full leaderboard — every league is reachable through pagination.

**Query parameters**

| Parameter | Type | Description |
|---|---|---|
| `page` | integer | 1-based page number. Defaults to `1`; capped at `10000`. |
| `pageSize` | integer | Results per page. Defaults to `25`; capped at `100`. |
| `sort` | string | Sort metric: `Points` (default), `Members`, `Created`, or `Name`. Any other value falls back to `Points`. |
| `sortOrder` | string | `desc` (default) or `asc`. |
| `search` | string | _(Optional)_ Case-insensitive **prefix** match on the league name (matches from the start, so `"RN"` matches `"RNG"` but `"NG"` does not). Trimmed and truncated to 64 characters. |

### Example request

```bash
curl 'https://ps99.biggamesapi.io/v1/leagues?page=1&pageSize=25&sort=Points'
```

```python
import requests
r = requests.get('https://ps99.biggamesapi.io/v1/leagues', params={
    'page': 1, 'pageSize': 25, 'sort': 'Points',
})
print(r.json())
```

### Example response (200)

```json
{
  "status": "ok",
  "data": {
    "leagues": [
      {
        "Name": "RNG",
        "NameLower": "rng",
        "ID": "a11060b75492443da3f8889318037509",
        "Icon": "rbxassetid://138181621351068",
        "Level": 1,
        "Points": 47781156,
        "Members": 4,
        "MemberCapacity": 4,
        "ContributorCount": 4,
        "Owner": 20532808,
        "Created": 1778947248
      }
      // ...
    ],
    "total": 92578,
    "page": 1,
    "pageSize": 25
  }
}
```

**Response fields**

| Field | Type | Description |
|---|---|---|
| `leagues` | array | One entry per league on the requested page. |
| `leagues[].Name` | string | League name. |
| `leagues[].NameLower` | string | Lowercased name, used for lookups and search. |
| `leagues[].ID` | string | Stable unique league identifier (hex string). |
| `leagues[].Icon` | string \| null | Asset ID string for the league icon (`rbxassetid://…`). |
| `leagues[].Level` | number | League level. |
| `leagues[].Points` | number | Total league points. |
| `leagues[].Members` | number | Roster size, counting the owner (owner + member entries). |
| `leagues[].MemberCapacity` | number | Maximum roster size. |
| `leagues[].ContributorCount` | number | Number of distinct point-contribution records. |
| `leagues[].Owner` | number \| null | Roblox user ID of the league owner. |
| `leagues[].Created` | number \| null | Unix timestamp (seconds) when the league was created. |
| `total` | number | Total number of leagues matching the query (ignores pagination). |
| `page` | number | The page number echoed back. |
| `pageSize` | number | The effective page size echoed back. |

### Other responses

- `500 (unhandled error)` — The leaderboard query threw an unexpected error. Envelope: `{ "status": "error", "error": { "message": "Could not load league leaderboard.", "ignore": true } }`.

### Notes

- Cache: `public, max-age=60, s-maxage=180, stale-while-revalidate=600`
- Each unique combination of query parameters is cached server-side for up to 60 seconds (a bounded LRU of 1000 entries; high query variety can evict entries sooner).
- `sort=Members` orders by roster size and is computed with an aggregation; the other sorts use indexed fields directly.

---

## GET /v1/leagues/:name

Returns full detail for a single league: its roster and its point contributions, with Roblox display names resolved.

**Path parameters**

| Parameter | Type | Description |
|---|---|---|
| `name` | string | League name (case-insensitive). Maximum 64 characters. |

If more than one league shares a name, the one with the highest `Points` is returned.

### Example request

```bash
curl 'https://ps99.biggamesapi.io/v1/leagues/RNG'
```

```python
import requests
r = requests.get('https://ps99.biggamesapi.io/v1/leagues/RNG')
print(r.json())
```

### Example response (200)

```json
{
  "status": "ok",
  "data": {
    "Name": "RNG",
    "NameLower": "rng",
    "ID": "a11060b75492443da3f8889318037509",
    "Icon": "rbxassetid://138181621351068",
    "Level": 1,
    "Points": 47781156,
    "MemberCapacity": 4,
    "Created": 1778947248,
    "Owner": {
      "UserID": 20532808,
      "DisplayName": "GamesReborn"
    },
    "Members": [
      {
        "UserID": 8008645,
        "DisplayName": "Camille",
        "PermissionLevel": 50,
        "JoinTime": 1778947279
      }
      // ...
    ],
    "PointContributions": [
      {
        "UserID": 904244953,
        "DisplayName": "Metaverse",
        "Points": 14045416,
        "Timestamp": 1779404439
      }
      // ...
    ]
  }
}
```

**Response fields**

| Field | Type | Description |
|---|---|---|
| `Name` | string | League name. |
| `NameLower` | string | Lowercased name. |
| `ID` | string | Stable unique league identifier. |
| `Icon` | string \| null | Asset ID string for the league icon. |
| `Level` | number | League level. |
| `Points` | number | Total league points. |
| `MemberCapacity` | number | Maximum roster size. |
| `Created` | number \| null | Unix timestamp (seconds) of league creation. |
| `Owner` | object | The league owner. |
| `Owner.UserID` | number \| null | Roblox user ID of the owner. `null` for an owner-less league. |
| `Owner.DisplayName` | string | Owner's Roblox display name. |
| `Members` | array | Roster entries, **excluding** the owner (the owner is the separate `Owner` field). |
| `Members[].UserID` | number | Roblox user ID. |
| `Members[].DisplayName` | string | Roblox display name. |
| `Members[].PermissionLevel` | number | In-game permission level. |
| `Members[].JoinTime` | number \| null | Unix timestamp (seconds) when the member joined. |
| `PointContributions` | array | Per-player point contributions, sorted by `Points` descending. |
| `PointContributions[].UserID` | number | Roblox user ID. |
| `PointContributions[].DisplayName` | string | Roblox display name. |
| `PointContributions[].Points` | number | Points this player has contributed. |
| `PointContributions[].Timestamp` | number \| null | Unix timestamp (seconds) of the most recent contribution. |

### Other responses

- `400 Invalid league name.` — The `name` parameter is empty or longer than 64 characters. Envelope: `{ "status": "error", "error": { "message": "Invalid league name.", "ignore": true } }`.
- `404 League not found.` — No league matches the given name. Envelope: `{ "status": "error", "error": { "message": "League not found.", "ignore": true } }`.
- `500 (unhandled error)` — Envelope: `{ "status": "error", "error": { "message": "Could not load league detail.", "ignore": true } }`.

### Notes

- Cache: `public, max-age=60, s-maxage=180, stale-while-revalidate=600`
- The 404 response uses `Cache-Control: no-store` so negative results are not cached downstream.
- Display names are resolved in bulk; if the Roblox API is unavailable, a name falls back to the string form of its `UserID`.

---

## GET /v1/leagues/players

Returns the top point contributors across all leagues — a flat, ranked list drawn from a rolling sample of the top 500 contributions.

**No path or query parameters.**

### Example request

```bash
curl 'https://ps99.biggamesapi.io/v1/leagues/players'
```

```python
import requests
r = requests.get('https://ps99.biggamesapi.io/v1/leagues/players')
print(r.json())
```

### Example response (200)

```json
{
  "status": "ok",
  "data": {
    "players": [
      {
        "UserID": 904244953,
        "DisplayName": "Metaverse",
        "Points": 14045416,
        "Timestamp": 1779404439,
        "League": {
          "Name": "RNG",
          "ID": "a11060b75492443da3f8889318037509",
          "Icon": "rbxassetid://138181621351068",
          "Points": 47781156
        }
      }
      // ...
    ]
  }
}
```

**Response fields**

| Field | Type | Description |
|---|---|---|
| `players` | array | Contributors ranked by `Points` descending. Up to 500 entries. |
| `players[].UserID` | number | Roblox user ID. |
| `players[].DisplayName` | string | Roblox display name; falls back to the string form of `UserID` if resolution fails. |
| `players[].Points` | number | Points this player has contributed to their league. |
| `players[].Timestamp` | number \| null | Unix timestamp (seconds) of the contribution. |
| `players[].League` | object | The league this contribution belongs to. |
| `players[].League.Name` | string | League name. |
| `players[].League.ID` | string | Stable league identifier. |
| `players[].League.Icon` | string \| null | Asset ID string for the league icon. |
| `players[].League.Points` | number | The league's total points. |

### Other responses

- `500 (unhandled error)` — Envelope: `{ "status": "error", "error": { "message": "Could not load contributor aggregate.", "ignore": true } }`.

### Notes

- Cache: `public, max-age=60, s-maxage=180, stale-while-revalidate=600`
- The aggregate is rebuilt at most once every 3 minutes server-side.
- A player who contributes to a league outside the top 500 contributions will not appear here. This is a sample, not an exhaustive list.

---

## GET /v1/leagues/players/:userId

Looks up a single contributor within the same aggregate used by `/v1/leagues/players`. Returns that player's entry, or a 404 if they are not in the sample.

**Path parameters**

| Parameter | Type | Description |
|---|---|---|
| `userId` | integer | Roblox user ID. Must be a finite positive integer. |

### Example request

```bash
curl 'https://ps99.biggamesapi.io/v1/leagues/players/904244953'
```

```python
import requests
r = requests.get('https://ps99.biggamesapi.io/v1/leagues/players/904244953')
print(r.json())
```

### Example response (200)

```json
{
  "status": "ok",
  "data": {
    "UserID": 904244953,
    "DisplayName": "Metaverse",
    "Points": 14045416,
    "Timestamp": 1779404439,
    "League": {
      "Name": "RNG",
      "ID": "a11060b75492443da3f8889318037509",
      "Icon": "rbxassetid://138181621351068",
      "Points": 47781156
    }
  }
}
```

**Response fields**

The `data` object is a single contributor entry — identical in shape to one element of the `players` array from `GET /v1/leagues/players`.

### Other responses

- `400 Invalid userId.` — `userId` is not a finite positive integer. Envelope: `{ "status": "error", "error": { "message": "Invalid userId.", "ignore": true } }`.
- `404 Player not found in sampled leagues.` — The aggregate loaded successfully but the requested user ID was not among the sampled contributions. Envelope: `{ "status": "error", "error": { "message": "Player not found in sampled leagues.", "ignore": true } }`.
- `500 (unhandled error)` — Envelope: `{ "status": "error", "error": { "message": "Could not load contributor lookup.", "ignore": true } }`.

### Notes

- Cache: `public, max-age=60, s-maxage=180, stale-while-revalidate=600`
- The 404 response uses `Cache-Control: no-store`.
- A 404 does not mean the player has no league — only that their contribution was not in the top-500 sample.

---

## Caveats

- **Leaderboard is exact; contributors are sampled.** `GET /v1/leagues` paginates over every league. `GET /v1/leagues/players` and `/players/:userId` are drawn from the top 500 contributions only.
- **Server cache:** The contributor aggregate is held in memory for 3 minutes; leaderboard pages for 60 seconds. The first request after a cache miss may take slightly longer.
- **Display names:** Roblox display names are resolved in bulk. If the Roblox API is unavailable, names fall back to the numeric user ID as a string.
- **Duplicate names:** League names are not guaranteed unique. `GET /v1/leagues/:name` returns the highest-`Points` match.
