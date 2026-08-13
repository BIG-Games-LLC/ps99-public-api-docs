# Profile Currency now carries real balances

**Released:** 2026-08-13

## Fixed

- **`Currency` on the profile view is no longer all zeros** ([#142]). Affects
  [`GET /v1/account/profile`](../v1/account.md#get-v1accountprofile), the public
  [`/v1/players/:slug?include=profile`](../v1/players.md#profile) view, and the
  first-party account snapshot.

  The documentation has always described `Currency` as the player's balances keyed by
  currency id (`{ "Diamonds": { "id": "Diamonds", "_am": … }, … }`), but the
  implementation passed through the save's **top-level `Currency` key** — a vestigial
  struct the game stopped writing years ago, which reads
  `{"Coins": 0, "Diamonds": 0, "Tokens": 0}` for every player. The balances players
  actually hold live in internal per-currency stacks elsewhere in the save.

  The profile view now derives `Currency` from those stacks: re-keyed by currency id,
  `_am` summed per id, in exactly the shape the docs describe. `Currency.Diamonds._am`
  is the player's real diamond balance; event currencies (`LuckyCoins`,
  `BlockPartyCoins`, …) appear alongside it.

## Notes

- If your integration read the zeros and worked around them (e.g. by pulling the
  `Diamonds` row out of the inventory view), both paths now agree — the inventory
  workaround keeps working, `class: "Currency"` rows are unchanged there.
- `Coins` and `Tokens` no longer appear unless the player genuinely holds a currency
  with that id (`Coins` is a real event currency; `Tokens` is not).
- The field is omitted entirely when the save has no currency data, matching the
  "only keys present in the save appear" rule the pass-through views follow.

[#142]: https://github.com/BIG-Games-LLC/ps99-public-api-docs/issues/142
