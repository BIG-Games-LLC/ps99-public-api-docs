# /v1/leagues

The `/v1/leagues` endpoints expose Pet Simulator 99 **leagues**: small competitive teams (up to four players) that compete for placement rewards on a points leaderboard. A league has a name, an icon, an owner, a roster, and a `Points` total built from each member's contributions.

Leagues run in **seasons**, the way [clan battles](clans.md#get-v1clansbattlesbattleid) do. Each season has its own window, its own rewards and its own set of leagues. The `/v1/leagues/seasons` endpoints list every season and give a season detail shaped like a clan battle detail. The leaderboard, league detail and contributor endpoints serve the active season by default and take `?season=<seasonId>` to read any other.

Unlike `/v1/clans`, whose plain clan list still lives in the legacy [`/api/clans`](../legacy/README.md) routes, leagues have no legacy endpoints, so `/v1/leagues` carries the leaderboard itself. Every endpoint is read-only, requires no authentication, and returns the standard envelope (see [overview.md](overview.md) for envelope and caching details).

> **Field casing.** The leaderboard, league detail and contributor endpoints return entity fields in **PascalCase** (`UserID`, `DisplayName`, `League.Name`), matching the `/v1/clans/players` aggregate endpoints. The season endpoints return **camelCase** (`userId`, `displayName`, `league.name`), matching `/v1/clans/battles/:battleId`. Container keys (`season`, `leagues`, `players`, `total`, `page`, `pageSize`) are lowercase everywhere.

---

## How leagues are scored and ranked

The API ranks leagues the way the in-game board does, so `Rank`, `Place` and `Points` match what players see in game.

- **`Points` is the effective score.** A league's score is the sum of the **first** contribution entry of each player **currently on the roster** (the owner included). Two things make this differ from a plain sum of every contribution:
  - The game backend can store a second contribution entry for the same player. Only the first one counts, so a player's points are never counted twice.
  - A player who leaves a league keeps their contribution entry, but the board no longer counts it. League detail marks those entries `Counted: false`.
- **The board order.** For a season that has not been finalized, the API takes the top 1,000 leagues by their stored points and re-ranks them by effective points (ties broken by league ID), as the game's own leaderboard does. A league with no effective points has no rank. Below those 1,000, the order is the stored points order.
- **Finalized seasons.** Once the game backend has paid a season, it keeps a frozen copy of the final standings it paid from. A finalized season is ranked from those standings, so ranks and points are exactly what was paid, even if a league's points changed afterwards. The frozen standings go a little deeper than the last rewarded rank (see `finalized.rewardedThroughRank`), not through every league. Below that depth the order is the stored points order.

---

## Season states

| `state` | Meaning |
|---|---|
| `upcoming` | `startTime` is in the future. |
| `live` | Between `startTime` and `finishTime`. |
| `past` | After `finishTime`, or when the season has no start or finish time configured. |

A `past` season is not necessarily paid yet. `finalized` is set once the game backend has recorded the payout or captured the final standings; until then it is `null`.

**The active season** is the one `/v1/leagues` serves when no `?season=` is given: the newest season that has started, or the newest one configured when none has started. Between seasons, the active season is the one that just finished, so its `state` is `past`. In the short window after a new season starts and before it has any league data, the default endpoints fall back to the legacy league store and return `season: null` (league detail: `Season: null`), while `/v1/leagues/seasons/active` already names the new season.

---

## GET /v1/leagues/seasons

Lists every league season, newest first (by `startTime`), and names the active one.

**No path or query parameters.**

### Example request

```bash
curl 'https://ps99.biggamesapi.io/v1/leagues/seasons'
```

```python
import requests
r = requests.get('https://ps99.biggamesapi.io/v1/leagues/seasons')
print(r.json())
```

### Example response (200)

```json
{
  "status": "ok",
  "data": {
    "active": "BloodMoonLeague2026",
    "seasons": [
      {
        "id": "BloodMoonLeague2026",
        "title": "Blood Moon League",
        "startTime": 1791648000,
        "finishTime": 1792166400,
        "durationSeconds": 518400,
        "state": "past",
        "run": "BloodMoonLeague2026",
        "headlineReward": {
          "id": "Titanic Grinning Goat",
          "variant": "shinyRainbow",
          "particleTier": 2,
          "shiny": true,
          "amount": 1,
          "icon": "rbxassetid://75842588243785",
          "collection": "Pets"
        },
        "placementRewards": [
          {
            "placement": "1st",
            "best": 1,
            "worst": 1,
            "items": [
              {
                "id": "Gargantuan Mothman",
                "variant": "regular",
                "particleTier": 0,
                "shiny": false,
                "amount": 1,
                "icon": "rbxassetid://90053988446409",
                "collection": "Pets"
              }
            ]
          },
          {
            "placement": "3–4",
            "best": 3,
            "worst": 4,
            "items": [
              {
                "id": "Titanic Grinning Goat",
                "variant": "shinyGold",
                "particleTier": 1,
                "shiny": true,
                "amount": 1,
                "icon": "rbxassetid://75842588243785",
                "collection": "Pets"
              }
            ]
          }
          // ...
        ],
        "finalized": {
          "completedAt": 1792254271,
          "paid": true,
          "winnerCount": 24589,
          "rankedTeams": 42260,
          "rewardedThroughRank": 9751,
          "standingsCapturedAt": 1792166429
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
| `active` | string \| null | `id` of the active season (the one `/v1/leagues` serves by default). `null` when no season is configured. |
| `seasons` | array | Every season, newest first. Each entry is a season meta object (below). |

**Season meta object**

The same object is returned by `/v1/leagues/seasons/active` and as `meta` in `/v1/leagues/seasons/:seasonId`.

| Field | Type | Description |
|---|---|---|
| `id` | string | Season id (the season's config name, e.g. `FiestaLeague2026`). Pass it as `?season=` or `:seasonId`. |
| `title` | string | Display title; falls back to `id` when the season has none. |
| `startTime` | number \| null | Unix timestamp (seconds) when the season starts. |
| `finishTime` | number \| null | Unix timestamp (seconds) when the season ends. |
| `durationSeconds` | number \| null | `finishTime - startTime`; `null` when either is absent. |
| `state` | string | `"upcoming"`, `"live"` or `"past"` (see [Season states](#season-states)). |
| `run` | string \| null | Which data set holds this season's leagues. Usually equal to `id`; a season that was reset carries a suffix (e.g. `DeepBackroomsLeague2026B`). `null` when the season has no league data. |
| `headlineReward` | object \| null | The most notable reward item across the season's rewards (Titanic and Huge pets first, then the rarest variant). A [reward item](#reward-items). `null` when the season has no rewards. |
| `placementRewards` | array | Reward bands by placement, ordered by `best`. Empty when none. See [Placement rewards](#placement-rewards). |
| `finalized` | object \| null | Payout record for a finished season; `null` until the game backend has paid it or captured its final standings. |
| `finalized.completedAt` | number \| null | Unix timestamp (seconds) when the payout completed. |
| `finalized.paid` | boolean \| null | `true` when rewards were actually handed out; `false` for a run the backend processed without paying. `null` when no payout record exists (standings only). |
| `finalized.winnerCount` | number \| null | How many players received rewards. |
| `finalized.rankedTeams` | number \| null | How many leagues were ranked at the end (leagues with effective points). |
| `finalized.rewardedThroughRank` | number \| null | The last rank that earned a reward. |
| `finalized.standingsCapturedAt` | number \| null | Unix timestamp (seconds) when the final standings were captured. `null` when no standings were captured. |

### Placement rewards

| Field | Type | Description |
|---|---|---|
| `placement` | string | Readable label for the band: `"1st"`, `"2–10"`, `"5001+"` and so on. |
| `best` | number \| null | Best (lowest) rank in the band. |
| `worst` | number \| null | Worst (highest) rank in the band. |
| `items` | array | The [reward items](#reward-items) for the band (currently always one). |

### Reward items

Reward items appear in `headlineReward`, `placementRewards[].items`, `Reward.items` on league detail and `reward.items` in season detail. They have the same shape as clan battle [reward items](clans.md#reward-items).

| Field | Type | Description |
|---|---|---|
| `id` | string | Item id (for a pet, its name, e.g. `"Titanic Grinning Goat"`). |
| `variant` | string | `"regular"`, `"golden"`, `"rainbow"`, `"shiny"`, `"shinyGold"` or `"shinyRainbow"`. `"unknown"` for a variant the API does not recognise. |
| `particleTier` | number | The raw tier: `0` regular, `1` Golden, `2` Rainbow. |
| `shiny` | boolean | `true` for a Shiny item. Independent of `particleTier`: a Shiny Rainbow pet is `particleTier: 2` with `shiny: true`. |
| `amount` | number | How many of the item. |
| `icon` | string | _(Optional)_ Asset ID string for the item icon. Omitted when the item is not found in the item catalog. |
| `collection` | string | _(Optional)_ Item collection, e.g. `"Pets"`, `"Hoverboards"`, `"Booths"`, `"Lootboxes"`. Omitted when the item is not found. |
| `rarity` | string | _(Optional)_ Item rarity, when the catalog has one. |

### Other responses

- `500 (unhandled error)`: Envelope: `{ "status": "error", "error": { "message": "Could not load league seasons.", "ignore": true } }`.

### Notes

- Cache: `public, max-age=60, s-maxage=180, stale-while-revalidate=600`
- The season list is rebuilt at most once a minute server-side.
- The list can include internal test seasons. They have no league data (`run: null`).

---

## GET /v1/leagues/seasons/active

Returns the meta of the active season: the one `/v1/leagues`, `/v1/leagues/:name` and `/v1/leagues/players` serve when no `?season=` is given.

**No path or query parameters.**

### Example request

```bash
curl 'https://ps99.biggamesapi.io/v1/leagues/seasons/active'
```

```python
import requests
r = requests.get('https://ps99.biggamesapi.io/v1/leagues/seasons/active')
print(r.json())
```

### Example response (200)

```json
{
  "status": "ok",
  "data": {
    "id": "BloodMoonLeague2026",
    "title": "Blood Moon League",
    "startTime": 1791648000,
    "finishTime": 1792166400,
    "durationSeconds": 518400,
    "state": "past",
    "run": "BloodMoonLeague2026",
    "headlineReward": { "id": "Titanic Grinning Goat", "variant": "shinyRainbow", "particleTier": 2, "shiny": true, "amount": 1, "icon": "rbxassetid://75842588243785", "collection": "Pets" },
    "placementRewards": [ /* ... */ ],
    "finalized": { "completedAt": 1792254271, "paid": true, "winnerCount": 24589, "rankedTeams": 42260, "rewardedThroughRank": 9751, "standingsCapturedAt": 1792166429 }
  }
}
```

**Response fields**

The `data` object is a [season meta object](#get-v1leaguesseasons).

### Other responses

- `404 No league season is configured.`: There are no seasons at all. Envelope: `{ "status": "error", "error": { "message": "No league season is configured.", "ignore": true } }`.
- `500 (unhandled error)`: Envelope: `{ "status": "error", "error": { "message": "Could not load the active league season.", "ignore": true } }`.

### Notes

- Cache: `public, max-age=60, s-maxage=180, stale-while-revalidate=600`
- The 404 response uses `Cache-Control: no-store`.
- Between seasons the active season is the one that just ended, so check `state` before treating it as running.

---

## GET /v1/leagues/seasons/:seasonId

Returns detail for one season: its meta, aggregate stats, the top leagues with the reward each one's place earns, and the top individual contributors. Shaped like [`/v1/clans/battles/:battleId`](clans.md#get-v1clansbattlesbattleid).

**Path parameters**

| Parameter | Type | Description |
|---|---|---|
| `seasonId` | string | Season id (case-insensitive). Only `A-Z`, `a-z`, `0-9` and `_`, up to 64 characters. |

### Example request

```bash
curl 'https://ps99.biggamesapi.io/v1/leagues/seasons/FiestaLeague2026'
```

```python
import requests
r = requests.get('https://ps99.biggamesapi.io/v1/leagues/seasons/FiestaLeague2026')
print(r.json())
```

### Example response (200)

```json
{
  "status": "ok",
  "data": {
    "meta": {
      "id": "FiestaLeague2026",
      "title": "Fiesta League",
      "startTime": 1786208340,
      "finishTime": 1787328000,
      "durationSeconds": 1119660,
      "state": "past",
      "run": "FiestaLeague2026",
      "headlineReward": { /* reward item */ },
      "placementRewards": [ /* ... */ ],
      "finalized": { /* ... */ }
    },
    "stats": {
      "totalLeagues": 57440,
      "rankedLeagues": 43232,
      "sampledLeagues": 100,
      "totalPoints": 8779682093,
      "totalContributors": 400
    },
    "topLeagues": [
      {
        "rank": 1,
        "name": "I4GOT",
        "id": "98639e7486ea44688051fb4c178c3c5e",
        "icon": "rbxassetid://17450302814",
        "members": 4,
        "memberCapacity": 4,
        "points": 136279965,
        "contributorCount": 4,
        "reward": {
          "placement": "1st",
          "best": 1,
          "worst": 1,
          "items": [
            {
              "id": "Titanic Desert Scorpion",
              "variant": "shinyRainbow",
              "particleTier": 2,
              "shiny": true,
              "amount": 1,
              "icon": "rbxassetid://110282269693652",
              "collection": "Pets"
            }
          ]
        }
      }
      // ...
    ],
    "topPlayers": [
      {
        "rank": 1,
        "userId": 10315681945,
        "displayName": "CosmicLionLucky",
        "points": 36554351,
        "share": 0.004163516470504623,
        "league": {
          "name": "5H4N",
          "id": "818d56c7781148e79fac553f0bfebe86",
          "icon": "rbxassetid://14976604955",
          "place": 6
        }
      }
      // ...
    ],
    "podium": [ /* the first three topPlayers entries */ ]
  }
}
```

**`meta` fields**

A [season meta object](#get-v1leaguesseasons).

**`stats` fields**

| Field | Type | Description |
|---|---|---|
| `totalLeagues` | number | Every league in the season, scored or not. |
| `rankedLeagues` | number \| null | Leagues ranked at the end, from `meta.finalized.rankedTeams`. `null` until the season is finalized. |
| `sampledLeagues` | number | How many leagues are in `topLeagues` (up to 100). |
| `totalPoints` | number | Sum of `points` across `topLeagues`. |
| `totalContributors` | number | Counted contributions across `topLeagues` (contributions with points from players on the roster). |

**`topLeagues[]` fields**

| Field | Type | Description |
|---|---|---|
| `rank` | number | Board rank (see [How leagues are scored and ranked](#how-leagues-are-scored-and-ranked)). For a finalized season, the rank that was paid. |
| `name` | string | League name. |
| `id` | string | Stable league identifier. |
| `icon` | string \| null | Asset ID string for the league icon. |
| `members` | number | Roster size, counting the owner. |
| `memberCapacity` | number | Maximum roster size. |
| `points` | number | Effective points. For a finalized season, the points the rank was paid on. |
| `contributorCount` | number | Distinct players with a contribution entry, including players who have since left. |
| `reward` | object \| null | The [placement reward](#placement-rewards) band `rank` falls in, or `null` when it earns none. |

**`topPlayers[]` fields**

| Field | Type | Description |
|---|---|---|
| `rank` | number | 1-based rank within this response (up to 200 entries). |
| `userId` | number | Roblox user ID. |
| `displayName` | string | Roblox display name; falls back to the string form of `userId`. |
| `points` | number | The player's counted points. When a player has counted points in more than one of the top leagues, the highest is kept. |
| `share` | number | `points` divided by `stats.totalPoints`; `0` when the total is zero. |
| `league` | object | The league those points were scored for. |
| `league.name` | string | League name. |
| `league.id` | string | League identifier. |
| `league.icon` | string \| null | Asset ID string. |
| `league.place` | number | That league's board rank. |

`podium` is the first three `topPlayers` entries.

### Other responses

- `400 Invalid seasonId.`: `seasonId` is empty, longer than 64 characters, or has characters outside `[A-Za-z0-9_]`. Envelope: `{ "status": "error", "error": { "message": "Invalid seasonId.", "ignore": true } }`.
- `404 Season not found.`: No season has that id. Envelope: `{ "status": "error", "error": { "message": "Season not found.", "ignore": true } }`.
- `500 (unhandled error)`: Envelope: `{ "status": "error", "error": { "message": "Could not load season detail.", "ignore": true } }`.

### Notes

- Cache: `public, max-age=60, s-maxage=180, stale-while-revalidate=600`
- The 404 response uses `Cache-Control: no-store`.
- Season detail is rebuilt at most every 3 minutes server-side, and once a day for a `past` season.
- `topLeagues`, `topPlayers` and the totals cover the top 100 leagues only. They are not the whole season.
- `topPlayers` only counts contributions the board counts: a player who left a league is not listed for it.
- A season with no league data (`meta.run` is `null`) returns zero stats and empty lists, with `rankedLeagues: 0`.

---

## GET /v1/leagues

Returns a page of leagues for one season, ranked by the chosen metric. This is the full leaderboard: every league in the season is reachable through pagination.

**Query parameters**

| Parameter | Type | Description |
|---|---|---|
| `season` | string | _(Optional)_ Season id (case-insensitive). Defaults to the [active season](#season-states). |
| `page` | integer | 1-based page number. Defaults to `1`; capped at `10000`. |
| `pageSize` | integer | Results per page. Defaults to `25`; capped at `100`. |
| `sort` | string | Sort metric: `Points` (default), `Members`, `Created`, or `Name`. Any other value falls back to `Points`. |
| `sortOrder` | string | `desc` (default) or `asc`. |
| `search` | string | _(Optional)_ Case-insensitive **prefix** match on the league name (matches from the start, so `"RN"` matches `"RNG"` but `"NG"` does not). Trimmed and truncated to 64 characters. |

The default (`sort=Points`, `sortOrder=desc`, no `search`) is the in-game board order described in [How leagues are scored and ranked](#how-leagues-are-scored-and-ranked).

### Example request

```bash
curl 'https://ps99.biggamesapi.io/v1/leagues?season=BloodMoonLeague2026&page=1&pageSize=25'
```

```python
import requests
r = requests.get('https://ps99.biggamesapi.io/v1/leagues', params={
    'season': 'BloodMoonLeague2026', 'page': 1, 'pageSize': 25,
})
print(r.json())
```

### Example response (200)

```json
{
  "status": "ok",
  "data": {
    "season": "BloodMoonLeague2026",
    "leagues": [
      {
        "Name": "Top_4",
        "NameLower": "top_4",
        "ID": "b698a767d5c74002adc8b0b8e4e3308c",
        "Icon": "rbxassetid://111055741189811",
        "Level": 1,
        "Rank": 1,
        "Points": 10441,
        "Members": 4,
        "MemberCapacity": 4,
        "ContributorCount": 4,
        "Owner": 3753977683,
        "Created": 1791648017
      }
      // ...
    ],
    "total": 62687,
    "page": 1,
    "pageSize": 25
  }
}
```

**Response fields**

| Field | Type | Description |
|---|---|---|
| `season` | string \| null | The season served. `null` only when no season could be resolved and the API fell back to its legacy league store. |
| `leagues` | array | One entry per league on the requested page. |
| `leagues[].Name` | string | League name. |
| `leagues[].NameLower` | string | Lowercased name, used for lookups and search. |
| `leagues[].ID` | string | Stable unique league identifier (hex string). |
| `leagues[].Icon` | string \| null | Asset ID string for the league icon (`rbxassetid://…`). |
| `leagues[].Level` | number | League level. |
| `leagues[].Rank` | number \| null | Board rank. In the default order every row has one, except leagues with no points (`null`, listed after the ranked ones). With another `sort` or a `search`, a league in the ranked top 1,000 (or the finalized standings) keeps its board rank and the rest are `null`. |
| `leagues[].Points` | number | Effective points: what the board ranks by. For a finalized season, the points the rank was paid on. |
| `leagues[].Members` | number | Roster size, counting the owner (owner + member entries). |
| `leagues[].MemberCapacity` | number | Maximum roster size. |
| `leagues[].ContributorCount` | number | Distinct players with a contribution entry (a duplicated entry counts once), including players who have since left. |
| `leagues[].Owner` | number \| null | Roblox user ID of the league owner. |
| `leagues[].Created` | number \| null | Unix timestamp (seconds) when the league was created. |
| `total` | number | Total number of leagues matching the query (ignores pagination). |
| `page` | number | The page number echoed back. |
| `pageSize` | number | The effective page size echoed back. |

### Other responses

- `404 Season not found.`: `season` is not a known season id, or the season has no league data yet. Envelope: `{ "status": "error", "error": { "message": "Season not found.", "ignore": true } }`.
- `500 (unhandled error)`: The leaderboard query threw an unexpected error. Envelope: `{ "status": "error", "error": { "message": "Could not load league leaderboard.", "ignore": true } }`.

### Notes

- Cache: `public, max-age=60, s-maxage=180, stale-while-revalidate=600`
- The 404 response uses `Cache-Control: no-store`.
- Each unique combination of query parameters is cached server-side for up to 60 seconds (a bounded LRU of 1000 entries; high query variety can evict entries sooner). A finished season's ranking is kept for a day.
- Below the ranked depth (the top 1,000 for a season that is not finalized, the captured standings for one that is), pages follow the stored points order and `Rank` is the row's position in that order.
- `sort=Members` orders by roster size and is computed with an aggregation; the other sorts use indexed fields directly. `sort=Members` returns an empty page past the first 5,000 leagues.

---

## GET /v1/leagues/:name

Returns full detail for a single league: its place on the board, the reward that place earns, its roster and its point contributions, with Roblox display names resolved.

**Path parameters**

| Parameter | Type | Description |
|---|---|---|
| `name` | string | League name (case-insensitive). Maximum 64 characters. |

**Query parameters**

| Parameter | Type | Description |
|---|---|---|
| `season` | string | _(Optional)_ Season id (case-insensitive). Defaults to the [active season](#season-states). |

If more than one league in the season shares a name, the one with the highest stored points is returned.

A league literally named `seasons` or `players` cannot be read here: those paths are the [season](#get-v1leaguesseasons) and [contributor](#get-v1leaguesplayers) endpoints. Find it through `GET /v1/leagues?search=` instead.

### Example request

```bash
curl 'https://ps99.biggamesapi.io/v1/leagues/Top_4?season=BloodMoonLeague2026'
```

```python
import requests
r = requests.get('https://ps99.biggamesapi.io/v1/leagues/Top_4', params={
    'season': 'BloodMoonLeague2026',
})
print(r.json())
```

### Example response (200)

```json
{
  "status": "ok",
  "data": {
    "Name": "Top_4",
    "NameLower": "top_4",
    "ID": "b698a767d5c74002adc8b0b8e4e3308c",
    "Icon": "rbxassetid://111055741189811",
    "Level": 1,
    "Season": {
      "ID": "BloodMoonLeague2026",
      "State": "past",
      "Finalized": true
    },
    "Place": 1,
    "Points": 10441,
    "Reward": {
      "placement": "1st",
      "best": 1,
      "worst": 1,
      "items": [
        {
          "id": "Gargantuan Mothman",
          "variant": "regular",
          "particleTier": 0,
          "shiny": false,
          "amount": 1,
          "icon": "rbxassetid://90053988446409",
          "collection": "Pets"
        }
      ]
    },
    "MemberCapacity": 4,
    "Created": 1791648017,
    "Owner": {
      "UserID": 3753977683,
      "DisplayName": "3753977683"
    },
    "Members": [
      {
        "UserID": 102718819,
        "DisplayName": "6qym",
        "PermissionLevel": 50,
        "JoinTime": 1791648065
      }
      // ...
    ],
    "PointContributions": [
      {
        "UserID": 3753977683,
        "DisplayName": "3753977683",
        "Points": 2827,
        "Timestamp": 1792165996,
        "Counted": true
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
| `Season` | object \| null | The season this league belongs to. `null` only for the legacy league store. |
| `Season.ID` | string | Season id. |
| `Season.State` | string | `"upcoming"`, `"live"` or `"past"`. |
| `Season.Finalized` | boolean | `true` once the season has been paid or its final standings captured. |
| `Place` | number \| null | Place on the in-game board. For a finalized season, the rank that was paid. `null` when the league has no effective points. |
| `Points` | number | Effective points (see [How leagues are scored and ranked](#how-leagues-are-scored-and-ranked)). For a finalized season, the points the rank was paid on. |
| `Reward` | object \| null | The [placement reward](#placement-rewards) band `Place` falls in. `null` when the place earns no reward or there is no place. |
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
| `PointContributions` | array | One entry per player who has contributed, sorted by `Points` descending. A player the backend stored twice appears once, with the entry the game scores. |
| `PointContributions[].UserID` | number | Roblox user ID. |
| `PointContributions[].DisplayName` | string | Roblox display name. |
| `PointContributions[].Points` | number | Points this player has contributed. |
| `PointContributions[].Timestamp` | number \| null | Unix timestamp (seconds) of the most recent contribution. |
| `PointContributions[].Counted` | boolean | `true` when the player is on the roster now (owner or member), so the board counts these points. `false` for a player who has left: the entry stays, but it is not part of `Points`. |

### Other responses

- `400 Invalid league name.`: The `name` parameter is empty or longer than 64 characters. Envelope: `{ "status": "error", "error": { "message": "Invalid league name.", "ignore": true } }`.
- `404 Season not found.`: `season` is not a known season id, or the season has no league data yet. Envelope: `{ "status": "error", "error": { "message": "Season not found.", "ignore": true } }`.
- `404 League not found.`: No league in the season matches the given name. Envelope: `{ "status": "error", "error": { "message": "League not found.", "ignore": true } }`.
- `500 (unhandled error)`: Envelope: `{ "status": "error", "error": { "message": "Could not load league detail.", "ignore": true } }`.

### Notes

- Cache: `public, max-age=60, s-maxage=180, stale-while-revalidate=600`
- The 404 responses use `Cache-Control: no-store` so negative results are not cached downstream.
- Below the ranked depth, `Place` is one plus the number of leagues with more stored points. For a finalized season it is never placed inside the captured standings.
- Display names are resolved in bulk; if the Roblox API is unavailable, a name falls back to the string form of its `UserID`.

---

## GET /v1/leagues/players

Returns the top point contributors across all leagues in a season: a flat, ranked list drawn from the top 500 contributions.

**Query parameters**

| Parameter | Type | Description |
|---|---|---|
| `season` | string | _(Optional)_ Season id (case-insensitive). Defaults to the [active season](#season-states). |

### Example request

```bash
curl 'https://ps99.biggamesapi.io/v1/leagues/players?season=BloodMoonLeague2026'
```

```python
import requests
r = requests.get('https://ps99.biggamesapi.io/v1/leagues/players', params={
    'season': 'BloodMoonLeague2026',
})
print(r.json())
```

### Example response (200)

```json
{
  "status": "ok",
  "data": {
    "season": "BloodMoonLeague2026",
    "players": [
      {
        "UserID": 3753977683,
        "DisplayName": "3753977683",
        "Points": 2827,
        "Timestamp": 1792165996,
        "League": {
          "Name": "Top_4",
          "ID": "b698a767d5c74002adc8b0b8e4e3308c",
          "Icon": "rbxassetid://111055741189811",
          "Points": 10441
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
| `season` | string \| null | The season served. `null` only for the legacy league store. |
| `players` | array | Contributions ranked by `Points` descending. Up to 500 entries. |
| `players[].UserID` | number | Roblox user ID. |
| `players[].DisplayName` | string | Roblox display name; falls back to the string form of `UserID` if resolution fails. |
| `players[].Points` | number | Points this player has contributed to the league. |
| `players[].Timestamp` | number \| null | Unix timestamp (seconds) of the contribution. |
| `players[].League` | object | The league this contribution belongs to. |
| `players[].League.Name` | string | League name. |
| `players[].League.ID` | string | Stable league identifier. |
| `players[].League.Icon` | string \| null | Asset ID string for the league icon. |
| `players[].League.Points` | number | The league's effective points. |

### Other responses

- `404 Season not found.`: `season` is not a known season id, or the season has no league data yet. Envelope: `{ "status": "error", "error": { "message": "Season not found.", "ignore": true } }`.
- `500 (unhandled error)`: Envelope: `{ "status": "error", "error": { "message": "Could not load contributor aggregate.", "ignore": true } }`.

### Notes

- Cache: `public, max-age=60, s-maxage=180, stale-while-revalidate=600`
- The 404 response uses `Cache-Control: no-store`.
- The aggregate is rebuilt at most once every 3 minutes server-side, per season.
- Each entry is one contribution, not one player. A duplicated entry for the same player in the same league counts once, but the list includes entries from players who have since left their league (the ones league detail marks `Counted: false`), so a player who moved leagues can appear once per league.
- A player whose contribution is outside the top 500 will not appear here. This is a sample, not an exhaustive list. For a ranking of counted contributors in the top leagues, use `topPlayers` in [season detail](#get-v1leaguesseasonsseasonid).

---

## GET /v1/leagues/players/:userId

Looks up a single contributor within the same aggregate used by `/v1/leagues/players`. Returns that player's entry, or a 404 if they are not in the sample.

**Path parameters**

| Parameter | Type | Description |
|---|---|---|
| `userId` | integer | Roblox user ID. Must be a finite positive integer. |

**Query parameters**

| Parameter | Type | Description |
|---|---|---|
| `season` | string | _(Optional)_ Season id (case-insensitive). Defaults to the [active season](#season-states). |

### Example request

```bash
curl 'https://ps99.biggamesapi.io/v1/leagues/players/3753977683?season=BloodMoonLeague2026'
```

```python
import requests
r = requests.get('https://ps99.biggamesapi.io/v1/leagues/players/3753977683', params={
    'season': 'BloodMoonLeague2026',
})
print(r.json())
```

### Example response (200)

```json
{
  "status": "ok",
  "data": {
    "UserID": 3753977683,
    "DisplayName": "3753977683",
    "Points": 2827,
    "Timestamp": 1792165996,
    "League": {
      "Name": "Top_4",
      "ID": "b698a767d5c74002adc8b0b8e4e3308c",
      "Icon": "rbxassetid://111055741189811",
      "Points": 10441
    }
  }
}
```

**Response fields**

The `data` object is a single contributor entry, identical in shape to one element of the `players` array from `GET /v1/leagues/players`. If the player has more than one entry in the sample, the highest one is returned.

### Other responses

- `400 Invalid userId.`: `userId` is not a finite positive integer. Envelope: `{ "status": "error", "error": { "message": "Invalid userId.", "ignore": true } }`.
- `404 Season not found.`: `season` is not a known season id, or the season has no league data yet. Envelope: `{ "status": "error", "error": { "message": "Season not found.", "ignore": true } }`.
- `404 Player not found in sampled leagues.`: The aggregate loaded successfully but the requested user ID was not among the sampled contributions. Envelope: `{ "status": "error", "error": { "message": "Player not found in sampled leagues.", "ignore": true } }`.
- `500 (unhandled error)`: Envelope: `{ "status": "error", "error": { "message": "Could not load contributor lookup.", "ignore": true } }`.

### Notes

- Cache: `public, max-age=60, s-maxage=180, stale-while-revalidate=600`
- The 404 responses use `Cache-Control: no-store`.
- A 404 does not mean the player has no league, only that their contribution was not in the top-500 sample.

---

## Caveats

- **Leaderboard is exact; contributors are sampled.** `GET /v1/leagues` paginates over every league in the season. `GET /v1/leagues/players` and `/players/:userId` are drawn from the top 500 contributions only, and season detail from the top 100 leagues.
- **Ranking depth.** The board order is exact through the top 1,000 leagues (or, for a finalized season, through the captured standings). Below that, order and `Rank` follow the stored points, which can run slightly ahead of effective points for a league whose players left.
- **Server cache:** The contributor aggregate is held in memory for 3 minutes; leaderboard pages and the ranking for 60 seconds (a day for a finished season); season detail for 3 minutes (a day for a finished season). The first request after a cache miss may take slightly longer.
- **Display names:** Roblox display names are resolved in bulk. If the Roblox API is unavailable, names fall back to the numeric user ID as a string.
- **Duplicate names:** League names are not guaranteed unique. `GET /v1/leagues/:name` returns the highest-points match within the season.
