# Item creation times, and `stackKey` matches its documented shape

**Released:** 2026-08-11

## Added

- **`rawData.createdAt` on inventory items.** A unix timestamp (**seconds**) for when
  the item was created, requested in
  [ps99-public-api-docs#138](https://github.com/BIG-Games-LLC/ps99-public-api-docs/issues/138).
  This is what distinguishes a huge that was hatched from one that was traded, bought or
  pulled from a box, and it makes new-hatch notifications possible again.

  It appears only on **individually-tracked** items — huges, exclusives and similar,
  which the game stores one entry per item. Ordinary stackable items (`_am` greater than
  1) have no creation time in the save and so have no `createdAt`; nor do the small
  number of tracked items whose entry carries no timestamp. The key is omitted rather
  than sent as `null`, so check for its presence.

  Inventory rows only — trade, booth and mail items do not carry it.

  The rest of the internal `_uq` block stays withheld. Those fields (`_cu` the original
  creator, `_ol` the full ownership chain) name the **players who previously owned an
  item**, who have not opted into appearing on another player's public profile. The
  creation timestamp describes the item rather than any person, which is why it is the
  part we publish. See [v1/account.md](../v1/account.md#rawdata-fields).

## Changed

- **`stackKey` now contains only whitelisted fields**, matching the shape this
  documentation has always described. It is a JSON string of the published `rawData`
  fields — `{"id":"Huge Cosmic Axolotl","_am":1,"sh":1,"createdAt":1723308371}`. Treat
  it as an opaque row identifier: it is stable, unique per row, and safe as a React key
  or database id, but it is not a place to read item data from. Read `rawData` instead.

- **Inventory rows are deduplicated.** Entries identical on every published field —
  same id, variant, tier and `createdAt` — now share a single row with `count` summed,
  rather than appearing as separate rows distinguished only by data the API does not
  expose. The total number of items you own is unchanged; the number of rows it takes
  to describe them is slightly smaller. If you display or paginate on row count, expect
  a modest drop. Sum `count` for an item total.

## Notes

- `createdAt` is in **seconds**, matching the save's own representation. Multiply by
  1000 before constructing a JavaScript `Date`.
- Creation times are not unique. Items hatched in the same second that are otherwise
  identical share a row, with `count` reflecting how many.
