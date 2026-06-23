# Quickstart

This guide gets you from zero to a working authenticated API call in five short steps. You need a terminal and either `curl` or Python 3. The first two steps need nothing but an internet connection — no account, no token, no setup. By the end you'll have called a real authenticated endpoint on your own behalf. Budget about 5 minutes.

## Step 1: Your first request — no auth required

The `/v1/players/featured` endpoint is public, so it's a great way to confirm the API is reachable and see what a normal response looks like.

```bash
curl 'https://ps99.biggamesapi.io/v1/players/featured?limit=3'
```

```python
import requests
r = requests.get('https://ps99.biggamesapi.io/v1/players/featured', params={'limit': 3})
print(r.json())
```

Notice that the response is always wrapped in the same envelope: `{ "status": "ok", "data": { "results": [...] } }`. Every endpoint in this API uses that same shape, which means you can write a single error-checking helper and reuse it everywhere. Each item in `results` is a player summary with a `slug` field you can plug straight into Step 2. If something goes wrong you'll see `"status": "error"` at the top level instead. See [v1/overview.md](v1/overview.md#response-envelope) for the full breakdown.

## Step 2: Look up a public player profile

Public player profiles let you pull stats, inventory, and more — without any OAuth token — as long as the player has made those views public.

```bash
curl 'https://ps99.biggamesapi.io/v1/players/chickenputty?include=profile,inventory'
```

```python
import requests
r = requests.get(
    'https://ps99.biggamesapi.io/v1/players/chickenputty',
    params={'include': 'profile,inventory'},
)
print(r.json())
```

Two things to pay attention to in the response. First, `account.publicViews` lists the views that player has chosen to make public. Second, if you ask for a view that isn't public (or doesn't exist for that player), you'll get `{ "available": false, "reason": "not_public" }` instead of real data — the request still succeeds with HTTP 200, it just tells you what it can't show you. That design means your code never has to special-case 403 or 404 for missing views; check `available` instead. See [v1/players.md](v1/players.md) for the full list of views and query options.

## Step 3: Register a developer app

You need a `client_id` and `client_secret` before you can run the OAuth flow — this step gets you both.

This is the only part of the tutorial that happens in a browser instead of a terminal.

Go to [https://db.biggames.io/settings/developer-apps](https://db.biggames.io/settings/developer-apps) and sign in with your BIG Games account. If you don't have one yet, create one — it's the same account you'd use to play the game.

Click "Create app". You'll provide an app name, one or more redirect URIs (the URL your server will receive the auth code at), and the list of scopes your app needs. Scopes look like `player-data:pet-simulator-99:profile:read` and control exactly what data your app can access.

After saving, the dashboard shows you a `client_id` (public — safe to ship in your app) and a `client_secret` (private — keep this on your server only, never in a browser or a mobile app). Write down both now; the secret is only shown once. See [v1/authentication.md](v1/authentication.md) for the full scope list and security notes.

## Step 4: Send the player through the OAuth flow (brief)

OAuth gets you a short-lived access token that proves a specific player has authorized your app — without you ever seeing their password. This is the part where the player sees a consent screen and approves your app. Redirect them to the authorization URL with your parameters filled in:

```http
GET https://db.biggames.io/oauth/authorize
  ?client_id=YOUR_CLIENT_ID
  &redirect_uri=https://yourapp.example/callback
  &scope=player-data:pet-simulator-99:profile:read
  &code_challenge=<challenge>
  &code_challenge_method=S256
  &state=<random>
```

After the player approves, they're sent back to your `redirect_uri` with `?code=...&state=...` appended. Verify that `state` matches what you sent — this prevents cross-site request forgery attacks. Then exchange the code for an access token:

```bash
curl -X POST https://db.biggames.io/oauth/token \
  -u "YOUR_CLIENT_ID:YOUR_CLIENT_SECRET" \
  -d 'grant_type=authorization_code' \
  -d 'code=THE_CODE_FROM_CALLBACK' \
  -d 'redirect_uri=https://yourapp.example/callback' \
  -d 'code_verifier=YOUR_PKCE_CODE_VERIFIER'
```

This is intentionally brief — the full flow, including how to generate a PKCE `code_verifier`/`code_challenge` pair and handle the `state` parameter safely, lives in [v1/authentication.md](v1/authentication.md).

## Step 5: Make your first authenticated request

This is the payoff: call a real endpoint that returns live data scoped to the player who authorized your app.

Pass the token as a Bearer credential in the `Authorization` header — the token is tied to the player who approved your app, so this call returns their data.

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  https://ps99.biggamesapi.io/v1/account/profile
```

```python
import requests
r = requests.get(
    'https://ps99.biggamesapi.io/v1/account/profile',
    headers={'Authorization': f'Bearer {access_token}'},
)
print(r.json())
```

A successful response includes the player's display name, Roblox user ID, linked accounts, and more. The shape is the same standard envelope you saw in Step 1 — `{ "status": "ok", "data": { ... } }` — so your existing error-check logic applies here too. See [v1/account.md](v1/account.md) for the full shape of each authenticated endpoint.

If the token is missing or wrong you'll get a 401 with this body:

```json
{
  "status": "error",
  "error": {
    "message": "Missing bearer token.",
    "ignore": true
  }
}
```

The `ignore: true` field is a hint to logging tools that this is an expected client error, not a server problem. Double-check that your token hasn't expired and that you're sending the header as `Authorization: Bearer <token>` — the word "Bearer" and the space before the token are both required.

## What to read next

- [v1/overview.md](v1/overview.md) — response envelope, errors, rate limits, caching
- [v1/authentication.md](v1/authentication.md) — full OAuth 2.0 + PKCE flow with security notes
- [v1/refresh-quota.md](v1/refresh-quota.md) — how account data is cached and the daily fresh-pull budget
- [v1/players.md](v1/players.md) — public player profile lookups, search, featured, list, total
- [v1/account.md](v1/account.md) — all 7 authenticated endpoints
- [v1/clans.md](v1/clans.md) — clans aggregator and battle detail
- [v1/leagues.md](v1/leagues.md) — leagues leaderboard, detail, and top contributors
- [legacy/README.md](legacy/README.md) — the original `/api/*` endpoints (still supported)
