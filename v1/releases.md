# /v1/releases and /v1/items/changes

These endpoints tell you **what changed in Pet Simulator 99's item data, and when**. Every time a new version of the game goes live, biggamesapi.io imports its item data (pets, eggs, hoverboards, boosts and the other collections under [`/api/collection`](../legacy/README.md#get-collection)). Each import is a **release**: the place version, when it was published and imported, and the items it added or changed.

Use them to post "new pets just dropped", keep a wiki in sync, or refresh only the items that changed instead of downloading whole collections.

Every endpoint is read-only, requires no authentication, and returns the standard envelope (see [overview.md](overview.md) for envelope and caching details). Field names are **camelCase**.

---

## What counts as a release

- One release per published version of the game (place 8737899170) that biggamesapi.io imported. A version that was published but never imported (for example one held for a manual check) has no release until it is imported.
- A release lists only the collections served by [`/api/collection`](../legacy/README.md#get-collection). Other game data is not part of it.
- **Added** means the item was not in biggamesapi.io before this release. **Changed** means its data changed (the same change that moves the item's `dateModified`). Runtime values the game fills in on its own, such as cached power, never count as a change.
- A release can have no added or changed items: the game updated, but nothing in the item data did.
- A release lists items only. It never says anything about players.

## Times

| Field | Meaning |
|---|---|
| `publishedAt` | When the version went live, from Roblox's version history. `null` when it is not known (some releases before 2026-10-25). |
| `importedAt` | When biggamesapi.io finished importing it: from this moment the changes are in `/api/collection`. Usually a few minutes after `publishedAt`. |

Both are ISO 8601 strings in UTC.

---

## GET /v1/releases

Lists releases, newest first.

### Query parameters

| Parameter | Type | Description |
|---|---|---|
| `page` | integer | 1-based page number. Defaults to `1`. |
| `pageSize` | integer | Releases per page. Defaults to `20`; capped at `100`. |

### Example request

```bash
curl 'https://ps99.biggamesapi.io/v1/releases?pageSize=2'
```

```python
import requests
r = requests.get('https://ps99.biggamesapi.io/v1/releases', params={'pageSize': 2})
print(r.json())
```

### Example response (200)

```json
{
  "status": "ok",
  "data": {
    "releases": [
      {
        "version": 27452,
        "publishedAt": "2026-10-24T20:50:12.000Z",
        "importedAt": "2026-10-24T20:54:42.129Z",
        "added": 0,
        "changed": 0,
        "collections": {}
      },
      {
        "version": 27451,
        "publishedAt": "2026-10-24T18:44:03.000Z",
        "importedAt": "2026-10-24T18:47:59.978Z",
        "added": 34,
        "changed": 67,
        "collections": {
          "Boosts": { "added": 6, "changed": 0 },
          "Booths": { "added": 3, "changed": 2 },
          "Eggs": { "added": 1, "changed": 0 },
          "GuildBattles": { "added": 1, "changed": 0 },
          "Hoverboards": { "added": 3, "changed": 2 },
          "Pets": { "added": 20, "changed": 23 },
          "Ranks": { "added": 0, "changed": 40 }
        }
      }
    ],
    "total": 21,
    "page": 1,
    "pageSize": 2
  }
}
```

### Response fields

| Field | Type | Description |
|---|---|---|
| `releases` | array | Release summaries on this page, newest first (below). |
| `total` | number | How many releases exist. |
| `page` | number | The page returned. |
| `pageSize` | number | The page size used. |

Each release summary:

| Field | Type | Description |
|---|---|---|
| `version` | number | The place version. Pass it as `:version` below. |
| `publishedAt` | string \| null | When the version went live (see [Times](#times)). |
| `importedAt` | string \| null | When biggamesapi.io imported it. |
| `added` | number | Items added, across all collections. |
| `changed` | number | Items changed, across all collections. |
| `collections` | object | Per collection name, `{ "added": n, "changed": n }`. Only collections with at least one added or changed item appear. |

---

## GET /v1/releases/:version

Every item a release added or changed, grouped by collection.

### Path parameters

| Parameter | Type | Description |
|---|---|---|
| `version` | integer or `latest` | A place version from `/v1/releases`, or `latest` for the newest release. |

### Example request

```bash
curl 'https://ps99.biggamesapi.io/v1/releases/27451'
```

```python
import requests
r = requests.get('https://ps99.biggamesapi.io/v1/releases/latest')
print(r.json())
```

### Example response (200, shortened)

```json
{
  "status": "ok",
  "data": {
    "version": 27451,
    "publishedAt": "2026-10-24T18:44:03.000Z",
    "importedAt": "2026-10-24T18:47:59.978Z",
    "added": 34,
    "changed": 67,
    "collections": {
      "Boosts": {
        "added": [
          {
            "configName": "Boost | Luck",
            "data": "https://ps99.biggamesapi.io/api/collection/Boosts?configName=Boost%20%7C%20Luck",
            "icon": "https://ps99.biggamesapi.io/image/84698880918228"
          }
        ],
        "changed": []
      },
      "Ranks": {
        "added": [],
        "changed": [
          {
            "configName": "1 | Noob",
            "data": "https://ps99.biggamesapi.io/api/collection/Ranks?configName=1%20%7C%20Noob",
            "icon": null
          }
        ]
      }
    }
  }
}
```

### Response fields

The summary fields from [`GET /v1/releases`](#get-v1releases), except that `collections` maps each collection name to:

| Field | Type | Description |
|---|---|---|
| `added` | array | Items this release added (item shape below). |
| `changed` | array | Items this release changed. |

Each item:

| Field | Type | Description |
|---|---|---|
| `configName` | string | The item's name in its collection, the same `configName` `/api/collection` returns. |
| `data` | string | URL of the item's current data in [`/api/collection`](../legacy/README.md#get-collection). |
| `icon` | string \| null | URL of the item's icon through [`/image`](../legacy/README.md#get-image), or `null` when the item has no icon (for example Ranks). |

`data` and `icon` point at the item **as it is now**, not as it was in that release. Pets use their regular (not golden) thumbnail.

### Other responses

| Status | When |
|---|---|
| 400 | `version` is neither a number nor `latest`: `Version must be a place version number or latest.` |
| 404 | No release for that version (never published, or not imported yet): `Release not found.` |

---

## GET /v1/items/changes

Everything added or changed after a version or a time, one row per item per release, **oldest first**. Built for bots: poll it with the last version you saw and you catch up on every release you missed in one go.

### Query parameters

| Parameter | Type | Description |
|---|---|---|
| `since` | integer or string | **Required.** A place version (rows from releases after it) or an ISO 8601 time like `2026-10-20T00:00:00Z` or `2026-10-20` (rows from releases imported after it). `since=0` returns every release. |
| `page` | integer | 1-based page number. Defaults to `1`. |
| `pageSize` | integer | Rows per page. Defaults to `500`; capped at `1000`. |

### Example request

```bash
curl 'https://ps99.biggamesapi.io/v1/items/changes?since=27450&pageSize=2'
```

```python
import requests
r = requests.get('https://ps99.biggamesapi.io/v1/items/changes', params={'since': 27450})
print(r.json())
```

### Example response (200)

```json
{
  "status": "ok",
  "data": {
    "since": { "version": 27450 },
    "latestVersion": 27452,
    "changes": [
      {
        "version": 27451,
        "publishedAt": "2026-10-24T18:44:03.000Z",
        "importedAt": "2026-10-24T18:47:59.978Z",
        "collection": "Boosts",
        "configName": "Boost | Luck",
        "change": "added",
        "data": "https://ps99.biggamesapi.io/api/collection/Boosts?configName=Boost%20%7C%20Luck",
        "icon": "https://ps99.biggamesapi.io/image/84698880918228"
      },
      {
        "version": 27451,
        "publishedAt": "2026-10-24T18:44:03.000Z",
        "importedAt": "2026-10-24T18:47:59.978Z",
        "collection": "Boosts",
        "configName": "Boost | HugeLuck",
        "change": "added",
        "data": "https://ps99.biggamesapi.io/api/collection/Boosts?configName=Boost%20%7C%20HugeLuck",
        "icon": "https://ps99.biggamesapi.io/image/130520371018728"
      }
    ],
    "total": 101,
    "page": 1,
    "pageSize": 2,
    "hasMore": true
  }
}
```

### Response fields

| Field | Type | Description |
|---|---|---|
| `since` | object | What you asked for: `{ "version": n }` or `{ "time": "<ISO>" }`. |
| `latestVersion` | number \| null | The newest release's version. Save it and pass it as `since` next time. |
| `changes` | array | Rows on this page (below). |
| `total` | number | Rows across all pages. |
| `page` | number | The page returned. |
| `pageSize` | number | The page size used. |
| `hasMore` | boolean | `true` when another page follows. |

Each row has `version`, `publishedAt` and `importedAt` of its release, plus `collection`, `configName`, `change` (`"added"` or `"changed"`), `data` and `icon` as in [`GET /v1/releases/:version`](#get-v1releasesversion).

### Polling

1. Start with `since=0` (or the newest `version` from `/v1/releases` if you only want what comes next).
2. Read every page while `hasMore` is `true`.
3. Save `latestVersion` and use it as `since` next time. Every 10 to 15 minutes is plenty: the game updates a few times a week.

Rows are ordered oldest release first and new releases only add rows at the end, so a release landing while you page does not shift earlier pages. An item changed in three releases appears three times, once per release. Fetch its `data` once if you only want its current state.

### Other responses

| Status | When |
|---|---|
| 400 | `since` is missing or is neither a number nor an ISO 8601 time: `since must be a place version number or an ISO 8601 time.` |

---

## Caching

| Endpoint | `Cache-Control` |
|---|---|
| `/v1/releases` | `public, max-age=300, s-maxage=600, stale-while-revalidate=3600` |
| `/v1/releases/:version` | `public, max-age=600, s-maxage=3600, stale-while-revalidate=86400` |
| `/v1/releases/latest`, `/v1/items/changes` | `public, max-age=60, s-maxage=60, stale-while-revalidate=300` |

A new release can take up to a minute after `importedAt` to show up.
