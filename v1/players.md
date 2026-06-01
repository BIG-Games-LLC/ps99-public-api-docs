# /v1/players

The `/v1/players/*` endpoints let you look up public player profiles without authentication. No bearer token or API key required.

Players control what's visible from their in-game dashboard. The `account.publicViews` field in every response tells you which views the player has enabled publicly. Per-view data uses the per-view envelope documented in [overview.md](overview.md#per-view-envelope).

Players who haven't linked a Roblox account, who haven't opted in to any public view, or whose slug doesn't resolve to an active account return `404 player_not_found`. There is no way to distinguish "account not found" from "account found but all views private" — this is intentional.

See [overview.md](overview.md) for the standard response envelope, HTTP status codes, rate limits, and the full cache-control policy table.

A player's public profile is divided into seven views, each toggled independently from the in-game dashboard. The `profile` view is a flat pass-through of whitelisted player-state save keys — progression, currencies, statistics, mastery, achievements, zones, and miscellaneous flags. The `extendedProfile` view is a separate gate for the sensitive carve-out — `Gamepasses`, `Products`, `RobuxSpent` — which never appear in any other view. See [Public views](#public-views) for the full list and the data each view returns.

---

## GET /v1/players/:slug

Look up a single player by username or Roblox user ID.

**Slug formats accepted:**

- **Username** (case-insensitive). Example: `chickenputty`.
- **Roblox user ID** (digits only). Example: `2655994526`. If the digit string doesn't match any linked user ID, the route falls through to a username lookup, so a purely numeric username will still resolve.

**Query parameters:**

| Parameter | Description |
| --- | --- |
| `include` | Comma-separated view keys, `*`, or omitted. Controls which `views` are returned. See [Include parameter](#include-parameter) below. |

**Cache-Control:** `public, max-age=300, s-maxage=900, stale-while-revalidate=1800`

### Include parameter

The `?include=` query parameter determines whether a `views` map appears in the response.

| Value | Behavior |
| --- | --- |
| Missing or empty | Response contains `account` only — no `views` key. |
| `*` | All views the player has opted in to are returned. |
| `profile,inventory` | Only the listed keys are returned. Unknown keys are silently dropped. |

Keys must use **camelCase** — the exact strings from [Public views](#public-views) (for example `itemIndex`, not `item-index`). Requesting a key for a view the player has not enabled returns `{ "available": false, "reason": "not_public" }` for that key rather than an error.

### Example responses

**Bare — no `?include=`**

```http
GET /v1/players/chickenputty
```

```json
{
  "status": "ok",
  "data": {
    "account": {
      "robloxUserId": "2655994526",
      "username": "chickenputty",
      "displayName": "ChickenPutty",
      "publicViews": {
        "profile": true,
        "inventory": true,
        "extendedProfile": true
      }
    }
  }
}
```

`publicViews` is a sparse map — only keys the player has explicitly enabled appear. The absence of a key means that view is private (or the player has never toggled it on). No `views` key is present because `?include=` was not set.

**With include**

```http
GET /v1/players/chickenputty?include=profile,inventory
```

```json
{
  "status": "ok",
  "data": {
    "account": {
      "robloxUserId": "2655994526",
      "username": "chickenputty",
      "displayName": "ChickenPutty",
      "publicViews": {
        "profile": true,
        "inventory": true,
        "extendedProfile": true
      }
    },
    "views": {
      "profile": {
        "available": true,
        "isStale": false,
        "fetchedAt": "2026-05-13T08:21:00.000Z",
        "data": {}
      },
      "inventory": {
        "available": true,
        "isStale": false,
        "fetchedAt": "2026-05-13T08:21:00.000Z",
        "data": {}
      }
    }
  }
}
```

### Response fields

**Top-level:**

| Field | Type | Description |
| --- | --- | --- |
| `status` | `"ok"` | Always `"ok"` on a 200 response. |
| `data.account` | object | Public account summary. Always present. |
| `data.views` | object | Per-view data map. Only present when `?include=` resolved at least one key. |

**`data.account`:**

| Field | Type | Description |
| --- | --- | --- |
| `robloxUserId` | string | The player's Roblox user ID as a string. |
| `username` | string | Roblox username. Falls back to the requested slug when the linked record has no stored username. |
| `displayName` | string or null | Roblox display name. `null` when not set. |
| `publicViews` | object | Sparse map of `{ [viewKey]: true }`. Only keys the player has enabled appear. Keys that are absent are private. |

**`data.views`:**

Each key in `views` is a camelCase view name. Each value is a per-view envelope — see [overview.md](overview.md#per-view-envelope) for all four shapes (`available: true`, `not_public`, `no_recent_data`, `not_implemented`).

### Other responses

**404 — player not found:**

```json
{
  "status": "error",
  "error": {
    "code": "player_not_found"
  }
}
```

Returned when the slug doesn't resolve to an active linked account, or when the account exists but has no publicly enabled views. `Cache-Control` is set to `no-store` on 404 responses.

**500 — internal error:**

```json
{
  "status": "error",
  "error": {
    "code": "internal_error"
  }
}
```

---

## GET /v1/players/search

Search for players by username or display name prefix.

**Query parameters:**

| Parameter | Required | Description |
| --- | --- | --- |
| `q` | Effectively yes | Search query string. Prefix-matched against `username` and `displayName`, case-insensitive. Must be at least 2 characters — shorter queries return `{ "results": [] }` without an error. |
| `limit` | No | Number of results. Clamped to 1–25. Default: 12. |

Only players with at least one publicly enabled view appear in results.

**Cache-Control:** `public, max-age=30, s-maxage=60, stale-while-revalidate=120`

**200 response:**

```json
{
  "status": "ok",
  "data": {
    "results": [
      {
        "robloxUserId": "2655994526",
        "username": "chickenputty",
        "displayName": "ChickenPutty"
      },
      {
        "robloxUserId": "3812047193",
        "username": "chickenwings_99",
        "displayName": null
      }
    ]
  }
}
```

Each result contains `robloxUserId`, `username`, and `displayName` (which may be `null`). Results are not sorted — order is determined by the database index.

**500 response:**

```json
{
  "status": "error",
  "error": {
    "code": "internal_error"
  }
}
```

---

## GET /v1/players/featured

Returns recently active players who have opted in to at least one public view. Useful for populating a "browse players" UI without a search term.

**Query parameters:**

| Parameter | Required | Description |
| --- | --- | --- |
| `limit` | No | Number of results. Clamped to 1–50. Default: 12. |

Results are sorted by `updatedAt` descending — the most recently active opted-in players appear first.

**Cache-Control:** `public, max-age=60, s-maxage=300, stale-while-revalidate=600`

**200 response:** Same shape as `/search` — `{ "status": "ok", "data": { "results": [...] } }` with each result containing `robloxUserId`, `username`, and `displayName`.

**500 response:** Same shape as `/search`.

---

## GET /v1/players

Browse every public player as a paginated list. Use this to build a directory or an
"all players" grid; use [`/search`](#get-v1playerssearch) when you have a query string and
[`/featured`](#get-v1playersfeatured) when you just want a recent sample.

Unlike search and featured, **all four query parameters are required** — there are no
defaults. Omitting or mis-typing any of them returns `400`.

**Query parameters:**

| Parameter | Required | Description |
| --- | --- | --- |
| `page` | Yes | 1-based page number. Must be an integer ≥ 1. |
| `pageSize` | Yes | Results per page. Must be an integer between 1 and 1000. |
| `sort` | Yes | `recent` (by last-active time) or `username` (alphabetical). Direction is controlled by `sortOrder`. |
| `sortOrder` | Yes | `asc` or `desc`. |

Only players with at least one publicly enabled view are included.

**Cache-Control:** `public, max-age=60, s-maxage=180, stale-while-revalidate=600`

**200 response:** `data` is an **array** of player summaries (not wrapped in a `results` object).

```http
GET /v1/players?page=1&pageSize=50&sort=recent&sortOrder=desc
```

```json
{
  "status": "ok",
  "data": [
    {
      "robloxUserId": "2655994526",
      "username": "chickenputty",
      "displayName": "ChickenPutty"
    },
    {
      "robloxUserId": "3812047193",
      "username": "chickenwings_99",
      "displayName": null
    }
  ]
}
```

**400 response** — a required parameter is missing or invalid:

```json
{
  "status": "error",
  "error": {
    "code": "invalid_query",
    "message": "pageSize must be between 1 and 1000"
  }
}
```

The `message` names the offending parameter. `Cache-Control` is `no-store` on 400 responses.

**500 response:** `{ "status": "error", "error": { "code": "internal_error" } }`.

---

## GET /v1/players/total

Returns the total number of public players — the size of the set `/v1/players` paginates
over. Useful for showing a count or computing how many pages exist.

**No path or query parameters.**

**Cache-Control:** `public, max-age=60, s-maxage=300, stale-while-revalidate=600`

**200 response:** `data` is a plain number.

```json
{
  "status": "ok",
  "data": 18324
}
```

**500 response:** `{ "status": "error", "error": { "code": "internal_error" } }`.

---

## Public views

A player's public profile is split into 7 independently toggled views, controlled from the in-game dashboard.

Three views — `profile`, `extendedProfile`, `itemIndex` — are **pass-through**: their payload is a projection of whitelisted save keys in the save's native PascalCase shape. The other four — `inventory`, `trades`, `booth`, `mail` — keep curated envelopes with item-database enrichment and Roblox username resolution.

`profile` ships the player-state save keys (progression, currencies, statistics, mastery, achievements, zones, miscellaneous flags). `extendedProfile` is the separately-gated sensitive carve-out: `Gamepasses`, `Products`, `RobuxSpent`. Enabling `profile` never exposes those three — they reach clients only through `extendedProfile`.

The seven `?include=` keys correspond 1:1 to the authenticated [`/v1/account/*` endpoints](account.md). For the three pass-through views the JSON is identical; for `inventory`/`trades`/`booth`/`mail` the public payload is wrapped in the per-view envelope but the inner `data` shape matches account.md.

| `?include=` key | Data summary | Shape |
| --- | --- | --- |
| `profile` | Whitelisted player-state save keys (progression, currencies, Statistics, mastery, achievements, zones, …). | [profile](#profile) |
| `inventory` | All owned items plus the equipped loadout. | [inventory](#inventory) |
| `extendedProfile` | Sensitive carve-out: `Gamepasses`, `Products`, `RobuxSpent`. | [extendedProfile](#extendedprofile) |
| `itemIndex` | Full raw `ItemIndex` save object (all categories). | [itemIndex](#itemindex) |
| `trades` | Trade history with other players. | [trades](#trades) |
| `booth` | Player booth sale/purchase log. | [booth](#booth) |
| `mail` | In-game mail log. | [mail](#mail) |

> **Heads-up:** `?include=` keys are camelCase. `itemIndex` and `extendedProfile` are the two multi-word keys — passing `item-index` or `extended-profile` silently returns nothing for that key, because the API drops unrecognized keys rather than erroring.

---

### profile

The `profile` view returns a flat pass-through of whitelisted player-state save keys, in the save's native PascalCase shape. Only keys present in the save appear (no `null` placeholders). The sensitive carve-out (`Gamepasses`, `Products`, `RobuxSpent`) is never returned here — it lives only in [`extendedProfile`](#extendedprofile).

```json
{
  "Age": 45525674.566,
  "FirstJoinTimestamp": 1705116330.185,
  "LastJoinTimestamp": 1779478000,
  "TotalSessions": 9695,
  "Rank": 40,
  "RankStars": 386,
  "Rebirths": 9,
  "GoalsCompleted": 18047,
  "EggsHatched": 635808137,
  "MaximumAvailableEgg": 291,
  "BoothDiamondsEarned": 4232387156,
  "BoothSlots": 25,
  "EggSlotsPurchased": 83,
  "PetSlotsPurchased": 80,
  "Currency": {
    "Diamonds": { "id": "Diamonds", "_am": 8750000000 },
    "BlockPartyCoins": { "id": "BlockPartyCoins", "_am": 34200 }
  },
  "Statistics": {
    "Eggs Opened": 635807987,
    "Login Count": 9690,
    "Playtime": 45034130,
    "Huge Pets Opened": 393,
    "...": "..."
  },
  "Mastery": { "Pets": 98, "Eggs": 84, "...": "..." },
  "Achievements": {
    "Open Eggs": { "Progress": 634687911, "Stage": 6 },
    "...": "..."
  },
  "UnlockedZones": { "1": true, "2": true, "...": "..." },
  "PurchasedEggs": { "1": true, "...": "..." },
  "LoginStreak": { "Claimed": 14, "...": "..." }
}
```

The shape is identical to [`GET /v1/account/profile`](account.md#get-v1accountprofile) — see that section for the full per-field reference.

---

### inventory

The `inventory` view returns the player's full item list and their enriched equipped loadout. The old standalone `equipped` view is folded into this view.

```json
{
  "items": [
    {
      "class": "Pet",
      "id": "Huge Cosmic Axolotl",
      "count": 1,
      "stackKey": "{\"id\":\"Huge Cosmic Axolotl\",\"sh\":1}",
      "displayName": "Huge Cosmic Axolotl",
      "icon": "rbxassetid://18291048120",
      "goldenIcon": "",
      "rap": 4200000000,
      "rapApproximate": false,
      "exists": 312,
      "rarity": "Mythical",
      "rarityNumber": 5,
      "collection": "Pets",
      "rawData": { "id": "Huge Cosmic Axolotl", "_am": 1, "sh": 1 }
    }
  ],
  "equipped": {
    "pets": {
      "list": [
        {
          "uid": "abc123def456",
          "slot": "1",
          "id": "Huge Cosmic Axolotl",
          "displayName": "Huge Cosmic Axolotl",
          "icon": "rbxassetid://18291048120",
          "goldenIcon": "",
          "shiny": false,
          "golden": false,
          "rainbow": false
        }
      ],
      "equippedCount": 1,
      "maxEquipped": 8
    },
    "enchants": {
      "list": [
        {
          "uid": "ench001xyz",
          "slot": "1",
          "id": "Damage",
          "displayName": "Damage Tier 5",
          "icon": "rbxassetid://12480204987",
          "paid": false,
          "level": 5
        }
      ],
      "paidCount": 0,
      "maxEnchants": 6,
      "maxPaidEnchants": 2
    },
    "ultimate": { "id": "Void", "displayName": "Void", "icon": "" },
    "hoverboard": { "id": "Celestial", "displayName": "Celestial", "icon": "", "shiny": false },
    "booth": { "id": "Galaxy", "displayName": "Galaxy", "icon": "" }
  },
  "fetchedAt": "2026-05-13T08:21:00.000Z",
  "cached": true
}
```

**`items`** — array of enriched inventory items. See [Enriched item shape](account.md#enriched-item-shape) for the per-item field list.

**`equipped`** — the equipped loadout, enriched (`displayName` and `icon` populated from the item database). Shape is `EquippedSummary` (source: `services/save-derived.ts`):

- `pets` — `{ list: EquippedPet[], equippedCount: number, maxEquipped: number }`. Each `EquippedPet`:

  | Field | Type | Description |
  | --- | --- | --- |
  | `uid` | string | Unique instance id from the save. |
  | `slot` | string | Slot key as written in `EquippedPets`. |
  | `id` | string | Game-config id. |
  | `displayName` | string | Human-readable name, resolved from the item database. |
  | `icon` | string | Roblox asset id string (`rbxassetid://<n>`). |
  | `goldenIcon` | string | Golden-variant artwork; render in place of `icon` when `golden` is `true`. Empty string when the pet ships no dedicated golden art. |
  | `shiny` | boolean | `true` when the pet's `sh` flag is set. |
  | `golden` | boolean | `true` when `pt === 1`. |
  | `rainbow` | boolean | `true` when `pt === 2`. |

- `enchants` — `{ list: EquippedEnchantSlot[], paidCount: number, maxEnchants: number, maxPaidEnchants: number }`. Each `EquippedEnchantSlot`:

  | Field | Type | Description |
  | --- | --- | --- |
  | `uid` | string | Unique instance id of the enchant. |
  | `slot` | string | Slot key. |
  | `id` | string | Enchant config id. |
  | `displayName` | string | Human-readable name, resolved from the item database. |
  | `icon` | string | Roblox asset id string. |
  | `paid` | boolean | `true` when the enchant occupies a paid slot. |
  | `level` | number | Enchant level. `0` when not found in inventory. |

- `ultimate` — `{ id: string | null, displayName: string, icon: string }` or `null` when none equipped.

- `hoverboard` — `{ id: string, displayName: string, icon: string, shiny: boolean }` or `null` when none selected.

- `booth` — `{ id: string, displayName: string, icon: string }` or `null` when none selected.

**`fetchedAt`** — ISO 8601 timestamp of the underlying save snapshot.

**`cached`** — always `true`.

---

### extendedProfile

The `extendedProfile` view returns the sensitive carve-out — three save keys not exposed by any other view. A player can enable `profile` while leaving this view off.

```json
{
  "Gamepasses": { "Auto Hatch": true, "VIP": true },
  "Products": { "DiamondsSmall": { "id": "DiamondsSmall", "purchases": 3 } },
  "RobuxSpent": 24000
}
```

| Field | Type | Description |
| --- | --- | --- |
| `Gamepasses` | object | Owned gamepasses keyed by gamepass name, each value `true`. |
| `Products` | object | Product purchase history keyed by product id. |
| `RobuxSpent` | number | Total Robux the player has spent. |

Only keys present in the save appear; absent keys are omitted (no `null` placeholders).

---

### itemIndex

The `itemIndex` view returns the full raw `ItemIndex` save object — every category bucket (`Pet`, `Egg`, `Charm`, …) the game maintains, in its native shape. Shape is identical to [`/v1/account/itemIndex`](account.md#get-v1accountitemindex).

```json
{
  "ItemIndex": {
    "Pet": {
      "{\"id\":\"Cat\"}": 14,
      "{\"id\":\"Cat\",\"pt\":1}": 3,
      "{\"id\":\"Dog\"}": 3
    },
    "Egg": { "1": true, "2": true, "3": true },
    "Charm": { "Lucky": true }
  }
}
```

| Field | Type | Description |
| --- | --- | --- |
| `ItemIndex` | object | The save's full `ItemIndex` object. Top-level keys are category names; sub-bucket shapes vary by category (the `Pet` bucket is keyed by JSON-encoded variant strings with counts as values; other buckets are typically `Record<id, true>` discovery maps). |

---

### trades

The `trades` view returns trade history with other players. Shape is identical to [`/v1/account/trades`](account.md#get-v1accounttrades). Entries are sorted newest first.

```json
{
  "entries": [
    {
      "timestamp": 1746900000,
      "otherParty": { "uid": 4827361920, "displayName": "CoolTrader99" },
      "given": [
        {
          "kind": "enriched",
          "id": "Huge Cosmic Axolotl",
          "displayName": "Huge Cosmic Axolotl",
          "icon": "rbxassetid://18291048120",
          "goldenIcon": "",
          "count": 1,
          "rap": 4200000000,
          "rapApproximate": false,
          "exists": 312,
          "rarity": "Mythical",
          "variant": "Shiny",
          "collection": "Pets",
          "rawData": { "id": "Huge Cosmic Axolotl", "_am": 1, "sh": 1 }
        }
      ],
      "received": []
    }
  ]
}
```

Each entry: `{ timestamp, otherParty: { uid, displayName }, given: [item], received: [item] }`. Items use the enriched trade item shape — see [Trade/booth/mail item fields](account.md#tradeboothmail-item-fields-enrichedsaveitem-or-rawitemfallback).

---

### booth

The `booth` view returns the player's booth transaction history (items bought and sold through the player-to-player market). Shape is identical to [`/v1/account/booth`](account.md#get-v1accountbooth). Entries are sorted newest first.

```json
{
  "entries": [
    {
      "timestamp": 1746880000,
      "kind": "sale",
      "otherParty": { "uid": 3012847201, "displayName": "BuyerFan2025" },
      "given": [
        {
          "kind": "enriched",
          "id": "Rainbow Huge Balloon Dog",
          "displayName": "Rainbow Huge Balloon Dog",
          "icon": "rbxassetid://15834021900",
          "goldenIcon": "",
          "count": 1,
          "rap": 220000000,
          "rapApproximate": false,
          "exists": 1840,
          "rarity": "Exclusive",
          "variant": "Rainbow",
          "collection": "Pets",
          "rawData": { "id": "Rainbow Huge Balloon Dog", "_am": 1, "pt": 2 }
        }
      ],
      "received": []
    }
  ]
}
```

Each entry adds a `kind` field (`"sale"` or `"purchase"`) to the base trade shape. Items use the enriched trade item shape — see [Trade/booth/mail item fields](account.md#tradeboothmail-item-fields-enrichedsaveitem-or-rawitemfallback).

---

### mail

The `mail` view returns the player's in-game mail log. Shape is identical to [`/v1/account/mail`](account.md#get-v1accountmail). Entries are sorted newest first.

```json
{
  "entries": [
    {
      "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "timestamp": 1746910000,
      "type": "GiftItem",
      "sender": { "uid": 2987341100, "displayName": "FriendlyTrader" },
      "receiver": { "uid": 1234567890, "displayName": "Me" },
      "diamonds": null,
      "item": {
        "kind": "enriched",
        "id": "Huge Festive Cat",
        "displayName": "Huge Festive Cat",
        "icon": "rbxassetid://14820934011",
        "goldenIcon": "",
        "count": 1,
        "rap": 680000000,
        "rapApproximate": false,
        "exists": 721,
        "rarity": "Exclusive",
        "variant": "Shiny",
        "collection": "Pets",
        "rawData": { "id": "Huge Festive Cat", "_am": 1, "sh": 1 }
      }
    }
  ]
}
```

Each entry: `{ uuid, timestamp, type, sender, receiver, diamonds, item }`. `sender`, `receiver`, and `item` may be `null`. Items use the enriched trade item shape — see [Trade/booth/mail item fields](account.md#tradeboothmail-item-fields-enrichedsaveitem-or-rawitemfallback).
