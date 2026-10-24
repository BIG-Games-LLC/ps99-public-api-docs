# League seasons, in-game ranking and `/v1/leaderboards`

**Released:** 2026-10-24

## Added

- **League seasons** ([#143], [#146]). Leagues now work the way clan battles do: every
  season is readable by id, not just the active one. See
  [v1/leagues.md](../v1/leagues.md).
  - [`GET /v1/leagues/seasons`](../v1/leagues.md#get-v1leaguesseasons) lists every season,
    newest first, with its window, state, rewards and payout record (`finalized`), and names
    the active one.
  - [`GET /v1/leagues/seasons/active`](../v1/leagues.md#get-v1leaguesseasonsactive) is the
    season the other league endpoints serve by default.
  - [`GET /v1/leagues/seasons/:seasonId`](../v1/leagues.md#get-v1leaguesseasonsseasonid) is
    season detail shaped like a clan battle: `meta`, `stats`, `topLeagues` (each with the
    reward its place earns), `topPlayers` and `podium`.
  - `?season=<seasonId>` on `GET /v1/leagues`, `/v1/leagues/:name`, `/v1/leagues/players`
    and `/v1/leagues/players/:userId`. Those responses now carry a `season` key (league
    detail: a `Season` object).
- **`Rank` on leaderboard rows and `Place` on league detail** ([#146]). League detail also
  carries `Season`, the `Reward` band its place falls in, and `Counted` on each point
  contribution.
- **`stats.awardsProcessed` and `topClans[].awardsProcessed`** on
  [clan battle detail](../v1/clans.md#get-v1clansbattlesbattleid) ([#145]). The game backend
  marks each medalled clan once it has handed out a finished battle's medals. A `past` battle
  with `stats.awardsProcessed: false` has finished but its medals are still pending.
- **`/v1/leaderboards`** ([#147]): the in-game event leaderboards, live or final. See
  [v1/leaderboards.md](../v1/leaderboards.md).
  - `GET /v1/leaderboards` lists every board with its state (`live`, `ended`, `final`,
    `inactive`).
  - `GET /v1/leaderboards/:id` pages a board (`page`, `pageSize` default 50, max 100).
    Finished boards read from the final standings rewards were paid from; `?source=live`
    reads the live copy instead.
  - `GET /v1/leaderboards/:id/players/:userId` returns one player's row.
- **`shiny` on reward items.** Every reward item (clan battle and league season rewards)
  now has a `shiny` boolean beside `particleTier`.

## Fixed

- **League points and order now match the in-game board** ([#143]). The leaderboard used
  to sort by the stored points total, which could differ from the board in two ways: the
  backend sometimes stored the same player's contribution twice, and a player who left a
  league kept counting. `Points` is now the effective score the game ranks and pays by
  (the first entry of each player currently on the roster), and the order is the game's:
  the top 1,000 leagues re-ranked by effective points. A finalized season is ranked from
  the standings rewards were paid from. A duplicated contribution is listed and counted
  once in league detail, `ContributorCount` and `/v1/leagues/players`.

## Changed

- **Reward item `variant` values are corrected, which can break clients matching the old
  values.** `variant` read `particleTier` as if it were the Shiny flag: `particleTier: 1`
  was labelled `"shinyGold"`, `particleTier: 2` was labelled `"shinyRainbow"`, and the
  item's Shiny flag was ignored. So a plain Rainbow Titanic read `"shinyRainbow"` and a
  Shiny one with no tier read `"regular"`. `variant` is now one of `"regular"`,
  `"golden"`, `"rainbow"`, `"shiny"`, `"shinyGold"` or `"shinyRainbow"`, built from
  `particleTier` (`1` Golden, `2` Rainbow) and `shiny`. This affects `headlineReward`,
  `placementRewards[].items` and `tieredRewards` on clan battle detail, and every reward
  item on the league season endpoints. If you mapped `"shinyGold"` to Golden or
  `"shinyRainbow"` to Rainbow, map `"golden"` and `"rainbow"` now, and treat the
  `shiny*` values as Shiny.
- **`headlineReward` can pick a different item**, since it ranks by the corrected variant.
- **League `Points` can be lower than before** for a league with duplicated contributions
  or players who left. `PointContributions` keeps every player's entry; the ones the board
  no longer counts have `Counted: false`.

## Notes

- A league literally named `seasons` or `players` cannot be read through
  `/v1/leagues/:name`, because those paths are the new endpoints. Find it with
  `GET /v1/leagues?search=` instead.
- A past clan battle's detail is now kept on the 3-minute refresh until its awards are
  processed, then cached for a day, so `awardsProcessed` turns `true` within minutes.
- `/v1/leaderboards/*` responses carry
  `Cache-Control: public, max-age=60, s-maxage=60, stale-while-revalidate=300`.

[#143]: https://github.com/BIG-Games-LLC/ps99-public-api-docs/issues/143
[#145]: https://github.com/BIG-Games-LLC/ps99-public-api-docs/issues/145
[#146]: https://github.com/BIG-Games-LLC/ps99-public-api-docs/issues/146
[#147]: https://github.com/BIG-Games-LLC/ps99-public-api-docs/issues/147
