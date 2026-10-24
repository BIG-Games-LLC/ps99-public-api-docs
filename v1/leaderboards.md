# /v1/leaderboards

The `/v1/leaderboards` endpoints expose Pet Simulator 99's in-game **leaderboard contests**: the event boards (eggs hatched, boss wins, maze depth, speedruns and so on) and the permanent boards such as `RAP` and `Power`. Each board can be read **live**, as it stands in game right now, or **final**, as the frozen standings the game backend paid rewards from once the contest ended.

Every endpoint is read-only, requires no authentication, and returns the standard envelope (see [overview.md](overview.md) for envelope and caching details).

> **Field casing.** Board metadata and container keys are **camelCase** (`scoringEndsAt`, `leaderboard`, `entries`, `pageSize`). Rows are **PascalCase** (`Rank`, `UserID`, `DisplayName`, `Value`), like the [leagues](leagues.md) leaderboard.

---

## Board states

| `state` | Meaning |
|---|---|
| `live` | The board is running: the backend's copy of it was refreshed within the last 2 hours. |
| `ended` | Scoring has closed (`scoringEndsAt` has passed) but no final standings exist yet. The live copy is still readable. |
| `final` | The final standings the backend paid from have been captured. A board is read from them by default. |
| `inactive` | None of the above: an old board whose live copy is no longer refreshed and that has no final standings. |

A board with no contest window (`scoringEndsAt: null`), such as `RAP` or `Power`, is never `ended`: it is `live` while it is being refreshed and `inactive` otherwise.

## Values and codecs

`Value` is the raw score as the game stores it on the board, and the board is ordered by it, highest first. For most boards it is a plain count (`codec: "Integer"`). Some boards store an encoded score instead:

- Race boards (`codec` like `"Race(endTs=1787407200)"`) store an encoded value tied to the contest's end time, not the plain score.
- Speedrun boards store an inverted time, so the fastest run has the highest `Value` (values close to 2,147,483,647).

`codec` names the encoding when the game's config gives one. It can still read `"Integer"` or `null` for a board whose value is encoded, so do not show `Value` to players as-is without knowing the board.

---

## GET /v1/leaderboards

Lists every known board with its state: boards in the game's current config, plus older boards that only have final standings. Ordered by state (`live`, then `ended`, `final`, `inactive`), then newest first by `scoringEndsAt` (or `final.endedAt`).

**No path or query parameters.**

### Example request

```bash
curl 'https://ps99.biggamesapi.io/v1/leaderboards'
```

```python
import requests
r = requests.get('https://ps99.biggamesapi.io/v1/leaderboards')
print(r.json())
```

### Example response (200)

```json
{
  "status": "ok",
  "data": {
    "leaderboards": [
      {
        "id": "PSXRebornEggs",
        "state": "live",
        "scoringEndsAt": 1793376000,
        "listSize": 10000,
        "codec": "Integer",
        "live": { "updatedAt": 1792870300 },
        "final": null
      },
      {
        "id": "FiestaMazeRace2",
        "state": "ended",
        "scoringEndsAt": 1787407200,
        "listSize": 10000,
        "codec": "Race(endTs=1787407200)",
        "live": { "updatedAt": 1792870303 },
        "final": null
      },
      {
        "id": "HatchWarBossWins",
        "state": "final",
        "scoringEndsAt": 1791561600,
        "listSize": 10000,
        "codec": "Integer",
        "live": { "updatedAt": 1792870307 },
        "final": {
          "endedAt": 1791561600,
          "capturedAt": 1791562201,
          "entries": 11000,
          "rewardedThroughRank": 10000
        }
      },
      {
        "id": "FishingContest2",
        "state": "inactive",
        "scoringEndsAt": null,
        "listSize": 5000,
        "codec": null,
        "live": null,
        "final": null
      }
      // ...
    ]
  }
}
```

**Response fields**

| Field | Type | Description |
|---|---|---|
| `leaderboards` | array | Every known board. Each entry is a board meta object (below). |

**Board meta object**

The same object is returned as `leaderboard` by `GET /v1/leaderboards/:id`.

| Field | Type | Description |
|---|---|---|
| `id` | string | Board id, e.g. `HatchWarBossWins`. Pass it as `:id` (case-insensitive). |
| `state` | string | `"live"`, `"ended"`, `"final"` or `"inactive"` (see [Board states](#board-states)). |
| `scoringEndsAt` | number \| null | Unix timestamp (seconds) when scoring closes. `null` for a board with no contest window. |
| `listSize` | number \| null | How many rows the game shows for the board, from its config. `null` when not configured or the config is gone. |
| `codec` | string \| null | How `Value` is encoded (see [Values and codecs](#values-and-codecs)). `null` when the config names none. |
| `live` | object \| null | Present when a live copy of the board exists. |
| `live.updatedAt` | number \| null | Unix timestamp (seconds) when the backend last refreshed its live copy. |
| `final` | object \| null | Present when final standings exist for the board's current contest. |
| `final.endedAt` | number \| null | Unix timestamp (seconds) when the contest ended. |
| `final.capturedAt` | number \| null | Unix timestamp (seconds) when the final standings were captured. |
| `final.entries` | number \| null | How many rows the final standings hold. This goes a little past the last rewarded rank, not through every player. |
| `final.rewardedThroughRank` | number \| null | The last rank that earned a reward. |

### Other responses

- `500 (unhandled error)`: Envelope: `{ "status": "error", "error": { "message": "Could not load leaderboards.", "ignore": true } }`.

### Notes

- Cache: `public, max-age=60, s-maxage=60, stale-while-revalidate=300`
- The board list is rebuilt at most every 5 minutes server-side.
- Final standings from an earlier run of the same board (older than its current `scoringEndsAt`) are not used: a board that is running again reads `live` until its new run is final.
- The list can include internal test boards.

---

## GET /v1/leaderboards/:id

Returns one page of a board, live or final.

**Path parameters**

| Parameter | Type | Description |
|---|---|---|
| `id` | string | Board id (case-insensitive). Only `A-Z`, `a-z`, `0-9` and `_`, up to 64 characters. |

**Query parameters**

| Parameter | Type | Description |
|---|---|---|
| `page` | integer | 1-based page number. Defaults to `1`. |
| `pageSize` | integer | Rows per page. Defaults to `50`; capped at `100`. |
| `source` | string | _(Optional)_ `live` or `final`. Defaults to `final` when the board has final standings, otherwise `live`. Any other value is treated as the default. |

### Example request

```bash
curl 'https://ps99.biggamesapi.io/v1/leaderboards/HatchWarBossWins?page=1&pageSize=50'
```

```python
import requests
r = requests.get('https://ps99.biggamesapi.io/v1/leaderboards/HatchWarBossWins', params={
    'page': 1, 'pageSize': 50,
})
print(r.json())
```

### Example response (200, final)

```json
{
  "status": "ok",
  "data": {
    "leaderboard": {
      "id": "HatchWarBossWins",
      "state": "final",
      "scoringEndsAt": 1791561600,
      "listSize": 10000,
      "codec": "Integer",
      "live": { "updatedAt": 1792870307 },
      "final": {
        "endedAt": 1791561600,
        "capturedAt": 1791562201,
        "entries": 11000,
        "rewardedThroughRank": 10000
      }
    },
    "source": "final",
    "updatedAt": 1791562201,
    "total": 11000,
    "page": 1,
    "pageSize": 50,
    "entries": [
      {
        "Rank": 1,
        "UserID": 2554349520,
        "Name": null,
        "DisplayName": "Archer",
        "Value": 11150162,
        "RewardTier": 3
      },
      {
        "Rank": 2,
        "UserID": 109380530,
        "Name": null,
        "DisplayName": "Mini",
        "Value": 10017666,
        "RewardTier": 3
      }
      // ...
    ]
  }
}
```

### Example response (200, live)

```bash
curl 'https://ps99.biggamesapi.io/v1/leaderboards/PSXRebornSpeedrun?pageSize=2'
```

```json
{
  "status": "ok",
  "data": {
    "leaderboard": {
      "id": "PSXRebornSpeedrun",
      "state": "live",
      "scoringEndsAt": 1793376000,
      "listSize": 10000,
      "codec": "Integer",
      "live": { "updatedAt": 1792870295 },
      "final": null
    },
    "source": "live",
    "updatedAt": 1792870168,
    "total": 10,
    "page": 1,
    "pageSize": 2,
    "entries": [
      {
        "Rank": 1,
        "UserID": 417517762,
        "Name": "Sky_Fox7071",
        "DisplayName": "Sky_Fox7071",
        "Value": 2147473716
      },
      {
        "Rank": 2,
        "UserID": 516704828,
        "Name": "hank980810",
        "DisplayName": "Kakarotto",
        "Value": 2147473449
      }
    ]
  }
}
```

**Response fields**

| Field | Type | Description |
|---|---|---|
| `leaderboard` | object | The [board meta object](#get-v1leaderboards). |
| `source` | string | `"live"` or `"final"`: which standings this page comes from. |
| `updatedAt` | number \| null | Unix timestamp (seconds). For `live`, when the backend fetched the copy this page was read from; for `final`, when the standings were captured. |
| `total` | number | Rows available. For `live`, the rows in the backend's copy (up to 10,000). For `final`, `final.entries`. |
| `page` | number | The page number echoed back. |
| `pageSize` | number | The effective page size echoed back. |
| `entries` | array | The rows on this page, best first. |
| `entries[].Rank` | number | 1-based rank on the board. |
| `entries[].UserID` | number \| null | Roblox user ID. |
| `entries[].Name` | string \| null | Roblox username. Present on live rows; always `null` on final rows. |
| `entries[].DisplayName` | string \| null | Roblox display name. Live rows carry the name stored with the board (or the username). Final rows are resolved by the API and fall back to the string form of `UserID`. |
| `entries[].Value` | number | The raw stored score (see [Values and codecs](#values-and-codecs)). |
| `entries[].RewardTier` | number \| null | _(Final rows only)_ The reward tier this rank was paid in, named by the tier's last rank: `3` is the top 3 tier, `100` the top 100 tier. `null` for a rank past `rewardedThroughRank`. |

### Other responses

- `400 Invalid leaderboard id.`: `id` is empty, longer than 64 characters, or has characters outside `[A-Za-z0-9_]`. Envelope: `{ "status": "error", "error": { "message": "Invalid leaderboard id.", "ignore": true } }`.
- `404 Leaderboard not found.`: No board has that id. Envelope: `{ "status": "error", "error": { "message": "Leaderboard not found.", "ignore": true } }`.
- `404 No standings for this leaderboard.`: The board exists but has nothing to read for the requested source: no live copy and no final standings, `source=final` on a board without final standings, or `source=live` on a board without a live copy. Envelope: `{ "status": "error", "error": { "message": "No standings for this leaderboard.", "ignore": true } }`.
- `500 (unhandled error)`: Envelope: `{ "status": "error", "error": { "message": "Could not load leaderboard.", "ignore": true } }`.

### Notes

- Cache: `public, max-age=60, s-maxage=60, stale-while-revalidate=300`
- The 400 and 404 responses use `Cache-Control: no-store`.
- A live board is re-read at most once a minute server-side. The backend keeps up to 10,000 rows of a board (1,000 for some), so a live board has no rows past that depth.
- A page past the end returns an empty `entries` array, not an error.
- `?source=live` on a `final` board reads what the live copy holds now, which can differ from what was paid. Use the default (`final`) for results.

---

## GET /v1/leaderboards/:id/players/:userId

Returns one player's row on a board.

**Path parameters**

| Parameter | Type | Description |
|---|---|---|
| `id` | string | Board id (case-insensitive). Only `A-Z`, `a-z`, `0-9` and `_`, up to 64 characters. |
| `userId` | integer | Roblox user ID. Must be a finite positive integer. |

**Query parameters**

| Parameter | Type | Description |
|---|---|---|
| `source` | string | _(Optional)_ `live` or `final`, as for [`GET /v1/leaderboards/:id`](#get-v1leaderboardsid). |

### Example request

```bash
curl 'https://ps99.biggamesapi.io/v1/leaderboards/HatchWarBossWins/players/2554349520'
```

```python
import requests
r = requests.get('https://ps99.biggamesapi.io/v1/leaderboards/HatchWarBossWins/players/2554349520')
print(r.json())
```

### Example response (200)

```json
{
  "status": "ok",
  "data": {
    "leaderboard": "HatchWarBossWins",
    "source": "final",
    "entry": {
      "Rank": 1,
      "UserID": 2554349520,
      "Name": null,
      "DisplayName": "Archer",
      "Value": 11150162,
      "RewardTier": 3
    }
  }
}
```

**Response fields**

| Field | Type | Description |
|---|---|---|
| `leaderboard` | string | The board id. Unlike `GET /v1/leaderboards/:id`, this is the id string, not the meta object. |
| `source` | string | `"live"` or `"final"`. |
| `entry` | object | The player's row, the same shape as `entries[]` in [`GET /v1/leaderboards/:id`](#get-v1leaderboardsid). |

### Other responses

- `400 Invalid leaderboard id.`: Envelope: `{ "status": "error", "error": { "message": "Invalid leaderboard id.", "ignore": true } }`.
- `400 Invalid userId.`: `userId` is not a finite positive integer. Envelope: `{ "status": "error", "error": { "message": "Invalid userId.", "ignore": true } }`.
- `404 Leaderboard not found.`: Envelope: `{ "status": "error", "error": { "message": "Leaderboard not found.", "ignore": true } }`.
- `404 No standings for this leaderboard.`: As for `GET /v1/leaderboards/:id`. Envelope: `{ "status": "error", "error": { "message": "No standings for this leaderboard.", "ignore": true } }`.
- `404 Player is not on this leaderboard.`: The player has no row in the standings read (they are not on the board, or are below the depth the backend keeps). Envelope: `{ "status": "error", "error": { "message": "Player is not on this leaderboard.", "ignore": true } }`.
- `500 (unhandled error)`: Envelope: `{ "status": "error", "error": { "message": "Could not load leaderboard entry.", "ignore": true } }`.

### Notes

- Cache: `public, max-age=60, s-maxage=60, stale-while-revalidate=300`
- The 400 and 404 responses use `Cache-Control: no-store`.
- A 404 for a live board does not mean the player has no score, only that it is not in the top rows the backend keeps (up to 10,000).

---

## Caveats

- **Depth.** Live boards hold the top rows only (up to 10,000). Final standings go a little past the last rewarded rank. Neither covers every player who scored.
- **Freshness.** The live copy is refreshed by the game backend every few seconds while the board is in use, and this API re-reads it at most once a minute. The board list (states, `live.updatedAt`) is rebuilt every 5 minutes, so `leaderboard.live.updatedAt` and the page's `updatedAt` can differ.
- **Names.** Live rows carry the username and display name stored with the board. Final rows only store the user ID; the API resolves display names in bulk, and if the Roblox API is unavailable, a name falls back to the numeric user ID as a string.
