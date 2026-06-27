# Account data fixes

**Released:** 2026-06-27

## Fixed

- **`/v1/account/*` snapshots now actually refresh.** A bug in the freshness check meant a
  player's cached snapshot was never re-pulled after the first one: the "skip the pull
  because the player hasn't played since" optimization compared the cached snapshot's own
  last-join timestamp against the time that snapshot was taken — a comparison that is always
  true — so every metered read reported `refresh.skipped: "cache-extension"`, spent no quota,
  and served stale data indefinitely. The optimization has been removed. Past the 5-minute
  freshness window a read now pulls fresh, up to the player's daily quota.

- **Per-variant RAP is now correct on item values** (`/v1/account/*` items and the public
  `/v1/players/*` inventory and trade/booth/mail views). The game stores a separate RAP
  document per pet variant — regular `{"id":"…"}`, golden `{"id":"…","pt":1}`, rainbow
  `{"id":"…","pt":2}`, shiny `{"id":"…","sh":true}`, and their combinations — all sharing one
  item `id`. The RAP index was keyed by the bare `id` only, so all six variants collapsed onto
  a single entry and the last document loaded won; every variant — **including the regular
  pet** — then reported that one arbitrary value (e.g. a regular Huge Ghostly Dragon showing a
  high-tier variant's multi-trillion RAP). RAP is now keyed by the full variant stack-key
  (`id` + `pt`/`sh`) on both enrichment paths, and the bare-`id` fallback is written only by
  the regular/non-paint document, so a variant can no longer clobber the regular pet's price.
  Each variant resolves to its own RAP; tiered items (Enchants/Potions, `tn`) are unaffected.

## Changed

- **`refresh.skipped`** can now only be `"fresh"` or `null`. The `"cache-extension"` value is
  no longer returned. If you branched on it, treat it as `null` (a pull was attempted).
- Because the "hasn't played since" optimization is gone, ordinary reads past the 5-minute
  window consume quota slots a little faster than before. The per-player daily limits
  (10 standard / 30 VIP) are unchanged, and rapid reads within the 5-minute window are still
  free.

## Added

- **Forced refresh:** append `?refresh=true` (or `?refresh=1`) to any `/v1/account/*` read to
  force a fresh Open Cloud pull immediately, bypassing the 5-minute freshness window. It still
  spends a quota slot and is still bounded by the daily limit. See
  [v1/refresh-quota.md](../v1/refresh-quota.md#forcing-a-refresh).
