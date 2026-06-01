# /v1/account

The `/v1/account/*` endpoints return data about the **player who authorized your app**. They require a bearer access token issued through the [OAuth flow](authentication.md) and the matching scope.

Successful `/v1/account/*` responses are `Cache-Control: private, no-cache`; error responses are `Cache-Control: no-store`. Never cache or share account data across users.

There are **7 endpoints**, one per player-data view: `inventory`, `profile`, `extendedProfile`, `itemIndex`, `trades`, `booth`, and `mail`. These are the same 7 views, with the same `data` shapes, as the public [`/v1/players/:slug?include=`](players.md#public-views) surface — the only difference is gating: a bearer token + OAuth scope here, per-view `publicViews` opt-in there.

Three views (`profile`, `extendedProfile`, `itemIndex`) are **pass-through**: their `data` is a projection of whitelisted save keys, in the save's native PascalCase shape. The remaining four views (`inventory`, `trades`, `booth`, `mail`) keep curated envelopes with item-database enrichment and Roblox username resolution.

These endpoints read from a server-side cached snapshot of the player's Roblox save. The "no save snapshot" shape differs by endpoint: the **snapshot views** (`profile`, `extendedProfile`, `itemIndex`) return `{ "status": "ok", "data": null }` — the call succeeded but there's no save to read; the **enriched views** (`inventory`, `trades`, `booth`, `mail`) return their normal envelope with an empty array (e.g. `{ "items": [] }` or `{ "entries": [] }`).

**Freshness & the refresh quota.** Because the data comes from a cached snapshot, a response may be a few minutes old, and pulling a *fresh* snapshot from Roblox is limited by a per-player **daily quota** (10/day standard, 30/day VIP). Every account response includes a `refresh` object and `X-RateLimit-*` headers describing that budget. Read [Freshness & the refresh quota](refresh-quota.md) before building anything that needs up-to-the-minute data — it explains when a refresh actually happens and what to do when the quota is spent.

See [v1/overview.md](overview.md) for the response envelope, error codes, and rate limits.

---

## Enriched item shape

Several endpoints — `inventory`, `trades`, `booth`, and `mail` — return items enriched with metadata from the game's item database. This section is the canonical reference for those shapes. Per-endpoint sections link back here rather than repeating the tables.

### Inventory item fields (`EnrichedInventoryItem`)

Used by `GET /v1/account/inventory`. Source: `services/player-inventory.ts`.

| Field | Type | Description |
|---|---|---|
| `class` | string | Inventory category as written in the save (`Pet`, `Charm`, `Egg`, `Hoverboard`, `Consumable`, etc.). |
| `id` | string | Game-config id (e.g. `Cat`, `Diamonds`, `Huge Cosmic Axolotl`). |
| `count` | number | How many of this stack the player owns. |
| `stackKey` | string | Stable per-stack identifier. Two stacks of the same pet with different variants produce different `stackKey` values. Safe to use as a React key or database id. |
| `rawData` | object | Whitelisted item flags from the save. See the `rawData` sub-table below. |
| `displayName` | string | Human-readable item name resolved from the item database. Falls back to `id` when unmatched. |
| `icon` | string | Roblox asset id string, format `rbxassetid://<n>`. Empty string when unresolved. |
| `goldenIcon` | string | Golden-variant artwork (`rbxassetid://<n>`) for pets that ship dedicated golden art. Render this in place of `icon` for the golden variant. Empty string for non-pets and pets without golden art. |
| `rap` | number | Recent Average Price in diamonds. `0` when no RAP data is available. |
| `rapApproximate` | boolean | `true` when RAP was interpolated from related stacks (e.g. a tier variant rather than an exact match). |
| `exists` | number | Total in-game count for this stack across all players. |
| `rarity` | string \| undefined | Rarity tier name when known (`Common`, `Rare`, `Mythical`, etc.). Omitted when unresolved. |
| `rarityNumber` | number \| undefined | Numeric rarity index (1 = Common, ascending). Omitted when unresolved. |
| `collection` | string \| null | Internal collection name the metadata was resolved from (`Pets`, `Charms`, `Eggs`, etc.). `null` when the item could not be matched to any collection. |
| `category` | string \| undefined | Sub-category from the master collection record (e.g. `Huge`, `Titanic`). Omitted when not present. |

### Trade/booth/mail item fields (`EnrichedSaveItem` or `RawItemFallback`)

Used by `GET /v1/account/trades`, `GET /v1/account/booth`, and `GET /v1/account/mail`. Source: `services/save-items.ts`.

Each item in `given`, `received`, or `item` is one of two shapes, discriminated by the `kind` field:

**`kind: "enriched"`** — item was matched in the database:

| Field | Type | Description |
|---|---|---|
| `kind` | `"enriched"` | Discriminator. |
| `id` | string | Game-config id. |
| `displayName` | string | Human-readable name. |
| `icon` | string | Roblox asset id string, format `rbxassetid://<n>`. |
| `goldenIcon` | string | Golden-variant artwork for pets that ship it; render in place of `icon` for the golden variant. Empty string for non-pets and pets without golden art. |
| `count` | number | Stack quantity. |
| `rap` | number | Recent Average Price in diamonds. |
| `rapApproximate` | boolean | `true` when RAP is interpolated. |
| `exists` | number | Total in-game count. |
| `rarity` | string \| undefined | Rarity name when known. |
| `variant` | string | One of `Regular`, `Shiny`, `Golden`, `Rainbow`, `Shiny Golden`, `Shiny Rainbow`. Derived from `rawData.sh` and `rawData.pt`. |
| `tier` | number \| undefined | Tier number for Charms / Enchants / Potions / Consumables. Omitted when not tiered. |
| `collection` | string | Collection the metadata was resolved from. |
| `category` | string \| undefined | Sub-category from the master collection record (e.g. `Huge`, `Titanic`). Omitted when not present. |
| `rawData` | object | Whitelisted save flags. See `rawData` sub-table below. |

**`kind: "fallback"`** — item id was not found in the database:

| Field | Type | Description |
|---|---|---|
| `kind` | `"fallback"` | Discriminator. |
| `id` | string | Game-config id from the save. |
| `count` | number | Stack quantity. |
| `variant` | string | Same derivation as enriched (`Regular`, `Shiny`, etc.). |
| `tier` | number \| undefined | Tier number when present in save data. |
| `rawData` | object | Whitelisted save flags. |

### `rawData` fields

The `rawData` object on any item contains only the following whitelisted keys from the save. All other save fields (`_uq`, `_ct`, `_cu`, `_oc`, `_ol`, `_tr`, `_sb`, `_to`, `_lk`, `cv`, `xp`, `uid`) are stripped at the parser boundary and never sent to the client.

| Key | Meaning |
|---|---|
| `id` | Item id string (same as the top-level `id` field). |
| `_am` | Count / amount (mirrors top-level `count`). |
| `sh` | Shiny flag. Value is `1` or `true` when shiny; absent otherwise. |
| `pt` | Paint variant. `1` = Golden, `2` = Rainbow. Absent for unpainted items. Applied consistently across every endpoint that derives golden/rainbow flags or a `variant` label. |
| `tn` | Tier number for Charms, Enchants, Potions, and Consumables. |

---

## Common error responses

These error shapes apply to every `/v1/account/*` endpoint. Per-endpoint sections do not repeat them.

```json
// 401 — Authorization header missing or malformed
{ "status": "error", "error": { "message": "Missing bearer token.", "ignore": true } }
```

```json
// 401 — token expired or revoked
{ "status": "error", "error": { "message": "API key has expired or been revoked.", "ignore": true } }
```

```json
// 403 — token does not have the required scope
{ "status": "error", "error": { "message": "Requested scope is not allowed for this API key.", "ignore": true } }
```

```text
// 429 — rate-limited
HTTP/1.1 429 Too Many Requests
Retry-After: 12

{ "status": "error", "error": { "message": "Rate limit exceeded.", "ignore": true } }
```

The `Retry-After` header is in seconds. Respect it before retrying.

A `401` may carry other `message` strings depending on the exact token problem (e.g. `Invalid API key.`, `API key has been rotated.`, `Grant is no longer active.`), and an unexpected server fault returns `500` with `{ "status": "error", "error": { "message": "Internal error.", "ignore": true } }`. Treat the HTTP status code as authoritative — do not match on the `message` text.

```json
// 200 — player has no save snapshot (call succeeded, no data)
{ "status": "ok", "data": null, "refresh": { "...": "..." } }
```

---

## The `refresh` field

**Every** `/v1/account/*` response — success, no-save, or error-with-data — carries a
top-level `refresh` object alongside `status` and `data`. It reports the player's daily
fresh-data budget and whether this call used it. The same state is mirrored in
`X-RateLimit-*` response headers.

```json
"refresh": {
  "consumedThisCall": false,
  "used": 3,
  "limit": 10,
  "resetsAt": "2026-05-29T00:00:00.000Z",
  "nextRefreshEligibleAt": "2026-05-28T14:32:00.000Z",
  "quotaExhausted": false,
  "skipped": "fresh"
}
```

See [Freshness & the refresh quota](refresh-quota.md) for the full field reference, the
header table, and how the quota behaves when exhausted. **The example responses below omit
`refresh` for brevity, but it is always present.**

---

## GET /v1/account/inventory

Returns the authenticated player's full item inventory plus their equipped loadout, enriched with display metadata, RAP, and exists counts.

**Scope:** `player-data:pet-simulator-99:inventory:read`  
**Headers:** `Authorization: Bearer <access_token>`

### Example request

```bash
curl -H 'Authorization: Bearer <ACCESS_TOKEN>' \
  'https://ps99.biggamesapi.io/v1/account/inventory'
```

```python
import requests
r = requests.get(
    'https://ps99.biggamesapi.io/v1/account/inventory',
    headers={'Authorization': f'Bearer {access_token}'},
)
print(r.json())
```

### Response

| Field | Type | Description |
|---|---|---|
| `items` | `EnrichedInventoryItem[]` | All inventory items. See [Enriched item shape — Inventory item fields](#inventory-item-fields-enrichedinventoryitem) for field details. |
| `equipped` | `EquippedSummary` | The player's equipped loadout — pets, enchants, ultimate, hoverboard, booth. See [Equipped loadout shape](#equipped-loadout-shape) below. |
| `fetchedAt` | string | ISO 8601 timestamp of when the save snapshot was captured. |
| `cached` | boolean | `true` when the snapshot was served from cache rather than freshly fetched. |

When the player has no save, `data` is `{ "items": [] }` (not `null`); `equipped`, `fetchedAt`, and `cached` are absent in that case.

### Equipped loadout shape

`equipped` is an `EquippedSummary` object (source: `services/save-derived.ts`). Its `displayName` and `icon` fields are enriched from the item database.

**`pets` object:**

| Field | Type | Description |
|---|---|---|
| `list` | `EquippedPet[]` | One entry per equipped slot. |
| `equippedCount` | number | Length of `list`. |
| `maxEquipped` | number | Maximum pets the player can equip (from `MaxPetsEquipped`). `0` when absent. |

Each `EquippedPet`: `{ uid, slot, id, displayName, icon, goldenIcon, shiny, rainbow, golden }`.

| Field | Type | Description |
|---|---|---|
| `uid` | string | Unique instance id from the save. |
| `slot` | string | Slot key as written in `EquippedPets`. |
| `id` | string | Game-config id (e.g. `Huge Cosmic Axolotl`). |
| `displayName` | string | Human-readable name, enriched from the item database. |
| `icon` | string | Roblox asset id string. |
| `goldenIcon` | string | Golden-variant artwork; render in place of `icon` when `golden` is `true`. Empty string when the pet ships no dedicated golden art. |
| `shiny` | boolean | `true` when the pet's `sh` flag is set. |
| `golden` | boolean | `true` when `pt === 1`. |
| `rainbow` | boolean | `true` when `pt === 2`. |

**`enchants` object:** `{ list: EquippedEnchantSlot[], paidCount, maxEnchants, maxPaidEnchants }`. Each `EquippedEnchantSlot`: `{ uid, slot, id, displayName, icon, paid, level }`.

**Top-level nullable fields:**

| Field | Type | Description |
|---|---|---|
| `ultimate` | object \| null | `{ id: string \| null, displayName: string, icon: string }`. `null` when none equipped. |
| `hoverboard` | object \| null | `{ id: string, displayName: string, icon: string, shiny: boolean }`. `null` when none selected. |
| `booth` | object \| null | `{ id: string, displayName: string, icon: string }`. `null` when none selected. |

### Example response

```json
{
  "status": "ok",
  "data": {
    "items": [
      {
        "class": "Pet",
        "id": "Huge Cosmic Axolotl",
        "count": 1,
        "stackKey": "{\"id\":\"Huge Cosmic Axolotl\",\"sh\":1}",
        "rawData": { "id": "Huge Cosmic Axolotl", "_am": 1, "sh": 1 },
        "displayName": "Huge Cosmic Axolotl",
        "icon": "rbxassetid://18291048120",
        "goldenIcon": "",
        "rap": 4200000000,
        "rapApproximate": false,
        "exists": 312,
        "rarity": "Mythical",
        "rarityNumber": 5,
        "collection": "Pets"
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
            "shiny": true,
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
            "displayName": "Damage",
            "icon": "rbxassetid://12480204987",
            "paid": false,
            "level": 5
          }
        ],
        "paidCount": 0,
        "maxEnchants": 6,
        "maxPaidEnchants": 2
      },
      "ultimate": { "id": "Void", "displayName": "Void", "icon": "rbxassetid://17750000001" },
      "hoverboard": { "id": "Celestial", "displayName": "Celestial", "icon": "rbxassetid://17750000002", "shiny": false },
      "booth": { "id": "Galaxy", "displayName": "Galaxy", "icon": "rbxassetid://17750000003" }
    },
    "fetchedAt": "2026-05-13T12:00:00.000Z",
    "cached": true
  }
}
```

### Notes

- Items are returned in parse order (save key traversal order), not sorted. Sort client-side if you need a stable display order.
- Items whose `class` is not in the internal mapping still appear in `items` with `collection: null` and `displayName` equal to `id`.
- The `golden`/`rainbow` booleans on `EquippedPet` come from the `pt` save field: `pt === 1` is golden, `pt === 2` is rainbow. See [rawData fields](#rawdata-fields).
- For 401/403/429 errors, see [Common error responses](#common-error-responses).

---

## GET /v1/account/profile

Returns a flat pass-through of whitelisted player-state save keys, in the save's native PascalCase shape. There is no curation layer — fields are objects when the save stores objects, numbers when the save stores numbers. To compute summary counts (e.g. how many zones unlocked) walk the underlying object yourself.

The sensitive subset (`Gamepasses`, `Products`, `RobuxSpent`) is carved out into [`GET /v1/account/extendedProfile`](#get-v1accountextendedprofile) and is never returned here.

**Scope:** `player-data:pet-simulator-99:profile:read`  
**Headers:** `Authorization: Bearer <access_token>`

### Example request

```bash
curl -H 'Authorization: Bearer <ACCESS_TOKEN>' \
  'https://ps99.biggamesapi.io/v1/account/profile'
```

```python
import requests
r = requests.get(
    'https://ps99.biggamesapi.io/v1/account/profile',
    headers={'Authorization': f'Bearer {access_token}'},
)
print(r.json())
```

### Response

`data` is a flat object whose keys are a subset of the save's PascalCase top-level keys. Only keys actually present in the player's save are included; absent keys are simply omitted (no `null` placeholders). The following keys are whitelisted by this view:

**Identity / account**

| Field | Type | Description |
|---|---|---|
| `Age` | number | Account age in seconds. |
| `FirstJoinTimestamp` | number | Unix seconds when this account first joined PS99. |
| `LastJoinTimestamp` | number | Unix seconds of the player's most recent join. |
| `TotalSessions` | number | Lifetime session count. |

**Progression**

| Field | Type | Description |
|---|---|---|
| `Rank` | number | Current rank number. |
| `RankStars` | number | Stars earned toward the next rank. |
| `Rebirths` | number | Total rebirth count. |
| `GoalsCompleted` | number | Goals completed. |
| `Goals` | object | Active goal slots, keyed by index. Each goal: `{ Type, Stars, Amount, Progress, UID }`. |
| `EggsHatched` | number | Lifetime eggs hatched. |
| `EggHatchCount` | number | Distinct egg-hatch counter. |
| `MaximumAvailableEgg` | number | Highest egg index the player can access. |
| `PurchasedEggs` | object | Map of egg ids the player has purchased. |
| `UnlockedZones` | object | Map of unlocked zone ids. |
| `RoamingPetsCaught` | number | Count of roaming pets caught. |
| `LoginStreak` | object | Login-streak state. `{ Claimed, Last, … }`. |
| `Achievements` | object | Each entry: `{ Progress, Stage }`, keyed by achievement name. |
| `Mastery` | object | Mastery levels keyed by track name: `Record<string, number>`. |
| `UpgradesOwned` | object | Owned upgrade rows keyed by upgrade id. |
| `PetHatchCount` | object | Per-pet hatch counts keyed by pet id. |
| `MerchantExperience` | object | Merchant XP / level state. |

**Currencies**

| Field | Type | Description |
|---|---|---|
| `Currency` | object | All balances keyed by currency id, each entry `{ id, _am }`. Includes Diamonds and event currencies. |

**Statistics**

| Field | Type | Description |
|---|---|---|
| `Statistics` | `Record<string, number>` | Full raw Statistics dictionary as the game stores it. Includes `Login Count`, `Login Date`, `Playtime`, plus every other counter. Hundreds of keys; no grouping or sorting applied. |

**Slots / capacity**

| Field | Type | Description |
|---|---|---|
| `EggSlotsPurchased` | number | Total egg slots purchased. |
| `PetSlotsPurchased` | number | Total pet slots purchased. |

**Daycare**

| Field | Type | Description |
|---|---|---|
| `DaycareActive` | object | Currently active daycare assignment. |
| `DaycareVouchers` | number | Daycare-voucher count. |
| `ExclusiveDaycareActive` | object | Currently active exclusive daycare assignment. |
| `ExclusiveDaycareVouchers` | number | Exclusive-daycare voucher count. |

**Booth (player-state side)**

| Field | Type | Description |
|---|---|---|
| `BoothDiamondsEarned` | number | Lifetime diamonds earned through booth sales. |
| `BoothSlots` | number | Number of booth listing slots owned. |
| `RecentBoothId` | string | Last-visited booth id. |

**Preferences**

| Field | Type | Description |
|---|---|---|
| `FavoriteModeEnabled` | boolean | Favorite-mode toggle. |
| `FavoriteModeSelection` | object | Favorite-mode selection state (world). |
| `FavoriteModeSelectionPlaza` | object | Favorite-mode selection state (plaza). |
| `Keybinds` | array | Keybind config. |
| `RecentWorld` | number | Last-visited world index. |

For inventory + equipped loadout, item-index discovery, trade/booth/mail history, or the sensitive carve-out (`Gamepasses` / `Products` / `RobuxSpent`), call the appropriate dedicated endpoint.

### Example response

```json
{
  "status": "ok",
  "data": {
    "Age": 45525674.566,
    "FirstJoinTimestamp": 1705116330.185,
    "LastJoinTimestamp": 1779478000,
    "TotalSessions": 9695,
    "Rank": 40,
    "RankStars": 386,
    "Rebirths": 9,
    "GoalsCompleted": 18047,
    "EggsHatched": 635808137,
    "EggHatchCount": 84,
    "MaximumAvailableEgg": 291,
    "RoamingPetsCaught": 781,
    "BoothDiamondsEarned": 4232387156,
    "BoothSlots": 25,
    "RecentBoothId": "18",
    "RecentWorld": 1,
    "EggSlotsPurchased": 83,
    "PetSlotsPurchased": 80,
    "DaycareVouchers": 20,
    "ExclusiveDaycareVouchers": 7,
    "FavoriteModeEnabled": true,
    "Currency": {
      "Diamonds": { "id": "Diamonds", "_am": 8750000000 },
      "BlockPartyCoins": { "id": "BlockPartyCoins", "_am": 34200 }
    },
    "Statistics": {
      "Eggs Opened": 635807987,
      "Login Count": 9690,
      "Login Date": 1779478444,
      "Playtime": 45034130,
      "Breakables Broken": 212225297,
      "Huge Pets Opened": 393,
      "...": "..."
    },
    "Mastery": { "Pets": 98, "Eggs": 84, "...": "..." },
    "Achievements": {
      "Open Eggs": { "Progress": 634687911, "Stage": 6 },
      "...": "..."
    },
    "UnlockedZones": { "1": true, "2": true, "...": "..." },
    "PurchasedEggs": { "1": true, "2": true, "...": "..." },
    "LoginStreak": { "Claimed": 14, "...": "..." }
  }
}
```

### Notes

- Field shapes mirror the save document — keys are PascalCase, objects stay objects, arrays stay arrays. To get a count of unlocked zones, do `Object.keys(data.UnlockedZones).length`.
- `Statistics` is the full raw dictionary including login activity and playtime. If you intended Robux spend, gamepass ownership, or product purchases, request the `extendedProfile` scope.
- For 401/403/429 errors, see [Common error responses](#common-error-responses).

---

## GET /v1/account/extendedProfile

Returns the **sensitive carve-out** — gamepass ownership, product purchases, and lifetime Robux spend. Gated by its own scope so a player (or app) can hold the `profile` scope without exposing these values.

**Scope:** `player-data:pet-simulator-99:extendedProfile:read`  
**Headers:** `Authorization: Bearer <access_token>`

### Example request

```bash
curl -H 'Authorization: Bearer <ACCESS_TOKEN>' \
  'https://ps99.biggamesapi.io/v1/account/extendedProfile'
```

```python
import requests
r = requests.get(
    'https://ps99.biggamesapi.io/v1/account/extendedProfile',
    headers={'Authorization': f'Bearer {access_token}'},
)
print(r.json())
```

### Response

`data` is a flat pass-through of three whitelisted save keys. Only keys present in the player's save appear; absent keys are omitted.

| Field | Type | Description |
|---|---|---|
| `Gamepasses` | object | Owned gamepasses keyed by gamepass name, each value `true`. |
| `Products` | object | Product purchase history keyed by product id. |
| `RobuxSpent` | number | Lifetime Robux spent as reported by the save. |

### Example response

```json
{
  "status": "ok",
  "data": {
    "Gamepasses": { "Auto Hatch": true, "VIP": true },
    "Products": { "DiamondsSmall": { "id": "DiamondsSmall", "purchases": 3 } },
    "RobuxSpent": 24000
  }
}
```

### Notes

- These are the three keys excluded from the `profile` view. Hold both scopes to reconstruct the full set of player-state keys.
- For 401/403/429 errors, see [Common error responses](#common-error-responses).

---

## GET /v1/account/itemIndex

Returns the raw `ItemIndex` save object — every category bucket (`Pet`, `Egg`, `Charm`, …) the game maintains, in its native shape.

**Scope:** `player-data:pet-simulator-99:itemIndex:read`  
**Headers:** `Authorization: Bearer <access_token>`

### Example request

```bash
curl -H 'Authorization: Bearer <ACCESS_TOKEN>' \
  'https://ps99.biggamesapi.io/v1/account/itemIndex'
```

```python
import requests
r = requests.get(
    'https://ps99.biggamesapi.io/v1/account/itemIndex',
    headers={'Authorization': f'Bearer {access_token}'},
)
print(r.json())
```

### Response

`data` is a flat pass-through:

| Field | Type | Description |
|---|---|---|
| `ItemIndex` | object | The save's full `ItemIndex` object. Each top-level key is a category (`Pet`, `Egg`, `Charm`, etc.); each value is a bucket whose entries vary by category. |

**Pet bucket.** `ItemIndex.Pet` is keyed by variant-key strings — typically JSON like `{"id":"Cat","pt":1}` — with the value being the count of that variant the player has ever encountered. To get unique base pet ids, parse each key and dedupe on `id`.

**Other buckets.** `ItemIndex.Egg`, `ItemIndex.Charm`, etc. are simpler maps (often `Record<id, true>` for discovery flags).

### Example response

```json
{
  "status": "ok",
  "data": {
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
}
```

### Notes

- The Pet bucket's variant-key encoding is the game's native shape — these strings are JSON-parseable.
- For 401/403/429 errors, see [Common error responses](#common-error-responses).

---

## GET /v1/account/trades

Returns the authenticated player's trade history, with each side of each trade enriched with item metadata.

**Scope:** `player-data:pet-simulator-99:trades:read`  
**Headers:** `Authorization: Bearer <access_token>`

### Example request

```bash
curl -H 'Authorization: Bearer <ACCESS_TOKEN>' \
  'https://ps99.biggamesapi.io/v1/account/trades'
```

```python
import requests
r = requests.get(
    'https://ps99.biggamesapi.io/v1/account/trades',
    headers={'Authorization': f'Bearer {access_token}'},
)
print(r.json())
```

### Response

`data` is `{ entries: TradeEntry[] }`. Entries are sorted **newest first** (descending by `timestamp`).

Each `TradeEntry`:

| Field | Type | Description |
|---|---|---|
| `timestamp` | number | Unix timestamp (seconds) of the trade. |
| `otherParty` | object | `{ uid: number, displayName: string }`. `displayName` is resolved from the Roblox user API; falls back to the string representation of `uid` when the lookup fails. |
| `given` | array | Items the authenticated player gave. Each item uses the trade/booth/mail enriched shape — see [Trade/booth/mail item fields](#tradeboothmail-item-fields-enrichedsaveitem-or-rawitemfallback). |
| `received` | array | Items the authenticated player received. Same shape as `given`. |

When the player has no save, `data` is `{ "entries": [] }` (not `null`).

### Example response

```json
{
  "status": "ok",
  "data": {
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
        "received": [
          {
            "kind": "enriched",
            "id": "Damage",
            "displayName": "Damage Tier 5",
            "icon": "rbxassetid://12480204987",
            "goldenIcon": "",
            "count": 3,
            "rap": 850000,
            "rapApproximate": false,
            "exists": 4820,
            "rarity": "Legendary",
            "variant": "Regular",
            "tier": 5,
            "collection": "Charms",
            "rawData": { "id": "Damage", "_am": 3, "tn": 5 }
          }
        ]
      }
    ]
  }
}
```

### Notes

- Entries are sorted newest first.
- `otherParty.displayName` is resolved via the Roblox user API at response time. Network errors fall back to the string uid.
- Items not found in the database appear as `kind: "fallback"` objects. See [Trade/booth/mail item fields](#tradeboothmail-item-fields-enrichedsaveitem-or-rawitemfallback).
- For 401/403/429 errors, see [Common error responses](#common-error-responses).

---

## GET /v1/account/booth

Returns the authenticated player's booth transaction history (items bought and sold through the player-to-player market booth).

**Scope:** `player-data:pet-simulator-99:booth:read`  
**Headers:** `Authorization: Bearer <access_token>`

### Example request

```bash
curl -H 'Authorization: Bearer <ACCESS_TOKEN>' \
  'https://ps99.biggamesapi.io/v1/account/booth'
```

```python
import requests
r = requests.get(
    'https://ps99.biggamesapi.io/v1/account/booth',
    headers={'Authorization': f'Bearer {access_token}'},
)
print(r.json())
```

### Response

`data` is `{ entries: BoothEntry[] }`. Entries are sorted **newest first** (descending by `timestamp`).

Each `BoothEntry`:

| Field | Type | Description |
|---|---|---|
| `timestamp` | number | Unix timestamp (seconds) of the transaction. |
| `kind` | `"sale"` \| `"purchase"` | Transaction direction from the authenticated player's perspective. `"sale"` when the player had items in `given`; `"purchase"` when only `received` has items. |
| `otherParty` | object | `{ uid: number, displayName: string }` — the other player in the transaction. |
| `given` | array | Items the authenticated player gave. Non-empty when `kind` is `"sale"`. |
| `received` | array | Items the authenticated player received. Non-empty when `kind` is `"purchase"`. |

`given` and `received` use the trade/booth/mail enriched item shape. See [Trade/booth/mail item fields](#tradeboothmail-item-fields-enrichedsaveitem-or-rawitemfallback).

When the player has no save, `data` is `{ "entries": [] }` (not `null`).

### Example response

```json
{
  "status": "ok",
  "data": {
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
}
```

### Notes

- `kind` is derived solely from whether `given` is non-empty. There is no separate flag in the raw save.
- For 401/403/429 errors, see [Common error responses](#common-error-responses).

---

## GET /v1/account/mail

Returns the authenticated player's mail log — in-game messages that carry items or diamonds between players.

**Scope:** `player-data:pet-simulator-99:mail:read`  
**Headers:** `Authorization: Bearer <access_token>`

### Example request

```bash
curl -H 'Authorization: Bearer <ACCESS_TOKEN>' \
  'https://ps99.biggamesapi.io/v1/account/mail'
```

```python
import requests
r = requests.get(
    'https://ps99.biggamesapi.io/v1/account/mail',
    headers={'Authorization': f'Bearer {access_token}'},
)
print(r.json())
```

### Response

`data` is `{ entries: MailEntry[] }`. Entries are sorted **newest first** (descending by `timestamp`).

Each `MailEntry`:

| Field | Type | Description |
|---|---|---|
| `uuid` | string | Unique identifier for this mail entry. Falls back to a generated string (`mail-<timestamp>-<index>`) when the save entry has no `UUID` field. |
| `timestamp` | number | Unix timestamp (seconds) of the mail event. |
| `type` | string | Mail type from the save (e.g. `TradeOffer`, `GiftItem`). Passed through as-is; defaults to `"Unknown"` when absent. |
| `sender` | object \| null | `{ uid: number, displayName: string }`, or `null` when no sender id is present. |
| `receiver` | object \| null | `{ uid: number, displayName: string }`, or `null` when no receiver id is present. |
| `diamonds` | number \| null | Diamond amount attached to the mail, or `null` when absent. |
| `item` | `EnrichedOrFallback` \| null | Single enriched item attached to the mail, or `null` when none. See [Trade/booth/mail item fields](#tradeboothmail-item-fields-enrichedsaveitem-or-rawitemfallback). |

When the player has no save, `data` is `{ "entries": [] }` (not `null`).

### Example response

```json
{
  "status": "ok",
  "data": {
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
}
```

### Notes

- The `type` field reflects whatever string the game writes to the save. Tolerate unknown type values.
- `sender` and `receiver` display names are resolved from the Roblox user API at response time. Network errors fall back to the string uid.
- For the item field reference, see [Trade/booth/mail item fields](#tradeboothmail-item-fields-enrichedsaveitem-or-rawitemfallback).
- For 401/403/429 errors, see [Common error responses](#common-error-responses).
