# Releases feed: `/v1/releases` and `/v1/items/changes`

**Released:** _on deploy_

## Added

- **Releases feed** ([#87], [#103], [#107], [#113], [#144]). Each version of the game that goes
  live and is imported into biggamesapi.io is now a release you can read, so bots, wikis and
  "new pets" pages hear about new and changed items as soon as they land. See
  [v1/releases.md](../v1/releases.md).
  - [`GET /v1/releases`](../v1/releases.md#get-v1releases) lists releases newest first: the
    place version, `publishedAt`, `importedAt`, and how many items each collection added and
    changed. Paged (`page`, `pageSize` default 20, max 100).
  - [`GET /v1/releases/:version`](../v1/releases.md#get-v1releasesversion) lists every added
    and changed item in a release, grouped by collection, with its `configName`, display name,
    category, rarity and links to its data and icon. Changed items carry `changes`, the field by
    field before and after, for releases from 2026-10-25 on. `previous` and `next` link the
    neighbouring releases. `GET /v1/releases/latest` is the newest release.
  - [`GET /v1/items/changes?since=`](../v1/releases.md#get-v1itemschanges) flattens everything
    added or changed after a version or an ISO 8601 time, oldest first, so a bot can poll once
    and catch up. Paged (`pageSize` default 500, max 1000), with `latestVersion` to pass as
    `since` next time.

- **`changedSince` on [`/api/collection/:name`](../legacy/README.md#get-collection)**: only
  the items created or changed at or after an ISO 8601 date or epoch milliseconds.

## Notes

- Releases cover the collections served by `/api/collection` and list items only.
- `publishedAt` is `null` on some releases from before 2026-10-25, and those releases list
  changed items by name only (`changes: null`).
- Caching: `/v1/releases` `public, max-age=300, s-maxage=600, stale-while-revalidate=3600`;
  `/v1/releases/:version` `public, max-age=600, s-maxage=3600, stale-while-revalidate=86400`;
  `/v1/releases/latest` and `/v1/items/changes`
  `public, max-age=60, s-maxage=60, stale-while-revalidate=300`.

[#87]: https://github.com/BIG-Games-LLC/ps99-public-api-docs/issues/87
[#103]: https://github.com/BIG-Games-LLC/ps99-public-api-docs/issues/103
[#107]: https://github.com/BIG-Games-LLC/ps99-public-api-docs/issues/107
[#113]: https://github.com/BIG-Games-LLC/ps99-public-api-docs/issues/113
[#144]: https://github.com/BIG-Games-LLC/ps99-public-api-docs/issues/144
