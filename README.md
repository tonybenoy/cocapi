<p>
    <a href="https://github.com/tonybenoy/cocapi/actions">
        <img src="https://github.com/tonybenoy/cocapi/workflows/CI/badge.svg" alt="CI Status" height="20">
    </a>
    <a href="https://pypi.org/project/cocapi/"><img src="https://img.shields.io/pypi/v/cocapi" alt="Pypi version" height="21"></a>
</p>
<p>
    <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python version" height="17"></a>
    <a href="https://github.com/tonybenoy/cocapi/blob/master/LICENSE"><img src="https://img.shields.io/github/license/tonybenoy/cocapi" alt="License" height="17"></a>
    <a href="https://github.com/astral-sh/ruff">
        <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff" height="17">
    </a>
</p>

# cocapi

A Python wrapper for the official [Clash of Clans API](https://developer.clashofclans.com/) with full async support, automatic key management, caching, retries, and optional Pydantic models.

## Install

```bash
pip install cocapi

# With Pydantic model support
pip install 'cocapi[pydantic]'
```

Requires Python 3.10+.

## Quick Start

### With an API Token

Get a token from [developer.clashofclans.com](https://developer.clashofclans.com/):

```python
from cocapi import CocApi

api = CocApi("your_api_token")

clan = api.clan_tag("#2PP")
print(clan["name"])

player = api.players("#900PUCPV")
print(player["trophies"])
```

### With Email/Password (Automatic Key Management)

Skip manual key creation entirely. cocapi logs into the developer portal, detects your IP, and manages keys for you:

```python
from cocapi import CocApi

api = CocApi.from_credentials("you@example.com", "your_password")
clan = api.clan_tag("#2PP")
```

Keys are created automatically, reused when valid, and rotated when your IP changes. See [Authentication](#authentication) for details.

### Async

```python
import asyncio
from cocapi import CocApi

async def main():
    async with CocApi("your_token") as api:
        clan = await api.clan_tag("#2PP")
        player = await api.players("#900PUCPV")
        print(clan["name"], player["trophies"])

asyncio.run(main())
```

## Authentication

cocapi supports two ways to authenticate:

### 1. API Token

Pass a token directly. You manage key creation and IP binding yourself at the developer portal.

```python
api = CocApi("your_token")
```

### 2. Developer Portal Credentials

Provide your email and password. cocapi handles everything:

```python
api = CocApi.from_credentials("email", "password")
```

What happens automatically:
- Logs into the developer portal and detects your public IP
- Creates API keys bound to that IP (or reuses existing ones)
- If your IP changes mid-session and the API returns 403, revokes the old key and creates a new one
- Respects the 10-key-per-account SuperCell limit

#### Configuration Options

```python
from cocapi import CocApi, ApiConfig

config = ApiConfig(
    key_count=2,               # Number of keys to maintain (default: 1)
    key_name="my-bot",         # Key name on the portal (default: "cocapi_auto")
    auto_refresh_keys=True,    # Auto-rotate on IP change (default: True)
)
api = CocApi.from_credentials("email", "password", config=config)
```

#### Persisting Keys Locally

For scripts that run repeatedly, enable `persist_keys` to cache the token on disk. On the next run, if your IP hasn't changed, the cached token is reused without contacting the developer portal:

```python
config = ApiConfig(persist_keys=True)
api = CocApi.from_credentials("email", "password", config=config)
# First run:  logs in, creates key, saves to ~/.cocapi/keys.json
# Next runs:  detects IP, matches cache, skips login entirely
```

Disabled by default. Storage path is customizable via `key_storage_path`.

#### Standalone Key Manager

Use `SyncKeyManager` or `AsyncKeyManager` directly if you need tokens outside of `CocApi`:

```python
from cocapi import SyncKeyManager

with SyncKeyManager("email", "password", key_count=3) as km:
    tokens = km.manage_keys()
    print(f"Got {len(tokens)} token(s)")

# Async version
from cocapi import AsyncKeyManager

async with AsyncKeyManager("email", "password") as km:
    tokens = await km.manage_keys()
```

## Configuration

All options are set through `ApiConfig`:

```python
from cocapi import CocApi, ApiConfig

config = ApiConfig(
    # Request settings
    timeout=30,
    max_retries=3,
    retry_delay=1.0,           # Base delay for exponential backoff

    # Caching
    enable_caching=True,
    cache_ttl=600,             # Seconds (default: 300)

    # Rate limiting (async only)
    enable_rate_limiting=True,
    requests_per_second=10.0,
    burst_limit=20,

    # Metrics
    enable_metrics=True,
    metrics_window_size=1000,

    # Pydantic models (requires cocapi[pydantic])
    use_pydantic_models=True,
)

api = CocApi("your_token", config=config)

# Runtime management
api.get_cache_stats()
api.get_metrics()
api.clear_cache()
api.clear_metrics()
```

### Middleware

Add custom processing to requests and responses:

```python
from cocapi import CocApi
from cocapi.middleware import add_user_agent_middleware, add_request_id_middleware

api = CocApi("your_token")
api.add_request_middleware(add_user_agent_middleware("MyApp/1.0"))
api.add_request_middleware(add_request_id_middleware())

# Custom middleware
def add_custom_header(url, headers, params):
    headers["X-My-Header"] = "value"
    return url, headers, params

api.add_request_middleware(add_custom_header)
```

### Custom Endpoints

Call new SuperCell endpoints without waiting for a library update:

```python
result = api.custom_endpoint("/new-endpoint")
result = api.custom_endpoint("/clans/search", {"name": "clash", "limit": 10})

# With dynamic Pydantic model
result = api.custom_endpoint("/new-endpoint", use_dynamic_model=True)
```

### Base URL Override

For proxies or testing environments:

```python
config = ApiConfig(base_url="https://my-proxy.com/clash/v1")
api = CocApi("token", config=config)

# Or at runtime
api.set_base_url("https://staging.example.com/v1", force=True)
api.reset_base_url()
```

## Pagination

Endpoints that return lists (clan members, rankings, leagues, etc.) use cursor-based pagination. The `paginate()` helper auto-follows cursors and yields items one by one:

```python
# Iterate through all clan members
for member in api.paginate(api.clan_members, "#CLAN_TAG"):
    print(member["name"])

# Custom page size
for clan in api.paginate(api.location_id_clan_rank, "32000087", limit=50):
    print(clan["name"])
```

Pass the method reference and its arguments (excluding the `params` dict). The helper manages `limit` and `after` internally.

Works with async too:

```python
async with CocApi("token") as api:
    async for member in api.paginate(api.clan_members, "#CLAN_TAG"):
        print(member["name"])
```

Works with any list endpoint: `clan_members`, `clan_war_log`, `clan_capitalraidseasons`, `location`, `location_id_clan_rank`, `location_id_player_rank`, `league`, `league_season`, `league_season_id`, `labels_clans`, `labels_players`, `capitalleagues`, `builderbaseleagues`, `leaguetiers`, and all other ranking/listing endpoints.

> **Note**: `clan()` search has a special signature and should be paginated manually using the `params` dict if needed.

## Batch Fetch

Fetch multiple resources in one call. Sync runs sequentially; async runs concurrently with `asyncio.gather`:

```python
# Fetch multiple players at once
results = api.batch(api.players, ["#TAG1", "#TAG2", "#TAG3"])
for player in results:
    print(player["name"], player["trophies"])

# Methods with multiple args — pass tuples
results = api.batch(api.league_season_id, [("29000022", "2025-01"), ("29000022", "2025-02")])
```

Async with concurrency control:

```python
async with CocApi("token") as api:
    results = await api.batch(api.clan_tag, clan_tags, max_concurrent=5)
```

If one call fails, its position in the result list gets the error dict. Other calls are unaffected.

## CLI

Install with the `cli` extra:

```bash
pip install 'cocapi[cli]'
```

### Login with credentials (persisted)

Log in once with your developer portal email/password. The API key is saved to `~/.cocapi/keys.json` and reused automatically:

```bash
cocapi login --email you@example.com --password yourpass

# Now all commands work without --token
cocapi clan "#2PP"
cocapi goldpass
```

### Other authentication methods

```bash
# Explicit token
cocapi clan "#2PP" --token YOUR_TOKEN

# Environment variable
export COCAPI_TOKEN="YOUR_TOKEN"
cocapi clan "#2PP"

# Inline credentials (also persisted)
cocapi clan "#2PP" --email you@example.com --password yourpass
```

### Commands

Add `--json` to any command for raw JSON output. Add `--limit N` where supported.

**Clans**

```bash
cocapi clan "#2PP"                           # Clan info
cocapi members "#2PP" --limit 10             # Clan members
cocapi war "#2PP"                            # Current war
cocapi warlog "#2PP"                         # War log
cocapi cwl "#2PP"                            # CWL league group
cocapi raids "#2PP"                          # Capital raid seasons
cocapi search "clash" --limit 5              # Search clans by name
cocapi search "war" --min-level 10 --war-frequency always  # Advanced search
```

**Players**

```bash
cocapi player "#900PUCPV"                    # Player info
cocapi verify-token "#900PUCPV" "abc123"     # Verify in-game token
```

**Locations & Rankings**

```bash
cocapi locations                             # List all locations
cocapi location 32000006                     # Specific location info
cocapi rankings 32000087 clans               # Clan rankings for location
cocapi rankings 32000087 players             # Player rankings
cocapi rankings 32000087 clans-builder-base  # Builder base clan rankings
cocapi rankings 32000087 players-builder-base
cocapi rankings 32000087 capitals            # Capital rankings
```

**Leagues**

```bash
cocapi leagues                               # List leagues
cocapi league 29000022                       # Specific league info
cocapi league-seasons 29000022               # List seasons (Legend League)
cocapi league-seasons 29000022 2025-01       # Season rankings
cocapi war-leagues                           # List war leagues
cocapi war-leagues 48000000                  # Specific war league
cocapi capital-leagues                       # List capital leagues
cocapi capital-leagues 85000000              # Specific capital league
cocapi builder-base-leagues                  # List builder base leagues
cocapi builder-base-leagues 44000000         # Specific builder base league
cocapi league-tiers                          # List league tiers
cocapi league-tiers 105000001               # Specific league tier
```

**Other**

```bash
cocapi goldpass                              # Current gold pass season
cocapi labels clans                          # Clan labels
cocapi labels players                        # Player labels
cocapi cwl-war "#WARTAG"                     # Specific CWL war
```

## API Reference

All methods work in both sync and async mode. In async, use `await`. Pagination parameters (`limit`, `after`, `before`) can be passed as a dict.

---

### Clans

#### Clan Info
```python
api.clan_tag(tag)  # e.g. "#2PP"
```
<details>
 <summary>Response</summary>

```json
{
  "tag": "string",
  "name": "string",
  "type": "string",
  "description": "string",
  "location": {"id": 0, "name": "string", "isCountry": true, "countryCode": "string"},
  "isFamilyFriendly": true,
  "badgeUrls": {"small": "string", "large": "string", "medium": "string"},
  "clanLevel": 0,
  "clanPoints": 0,
  "clanBuilderBasePoints": 0,
  "clanCapitalPoints": 0,
  "capitalLeague": {"id": 0, "name": "string"},
  "requiredTrophies": 0,
  "requiredBuilderBaseTrophies": 0,
  "requiredTownhallLevel": 0,
  "warFrequency": "string",
  "warWinStreak": 0,
  "warWins": 0,
  "isWarLogPublic": true,
  "warLeague": {"id": 0, "name": "string"},
  "members": 0,
  "memberList": [{"tag": "string", "name": "string", "role": "string", "townHallLevel": 0, "expLevel": 0, "trophies": 0, "clanRank": 0, "donations": 0, "donationsReceived": 0}],
  "labels": [{"id": 0, "name": "string", "iconUrls": {}}],
  "clanCapital": {"capitalHallLevel": 0, "districts": []},
  "chatLanguage": {"id": 0, "name": "string", "languageCode": "string"}
}
```
</details>

#### Clan Members
```python
api.clan_members(tag)
api.clan_members(tag, {"limit": 20})
```

#### Search Clans
```python
api.clan("clash", 10)

# With filters
api.clan(
    "war", 20,
    war_frequency="always",
    location_id=32000006,
    min_members=30,
    max_members=50,
    min_clan_points=20000,
    min_clan_level=10,
    label_ids="56000000,56000001",
)
```

#### War Log
```python
api.clan_war_log(tag)
```
<details>
 <summary>Response</summary>

```json
{"items": [{"result": "string", "endTime": "string", "teamSize": 0, "attacksPerMember": 0, "clan": {"tag": "string", "name": "string", "stars": 0, "destructionPercentage": 0.0}, "opponent": {"tag": "string", "name": "string", "stars": 0, "destructionPercentage": 0.0}}], "paging": {"cursors": {}}}
```
</details>

#### Current War
```python
api.clan_current_war(tag)
```
<details>
 <summary>Response</summary>

```json
{"state": "string", "teamSize": 0, "preparationStartTime": "string", "startTime": "string", "endTime": "string", "clan": {"tag": "string", "name": "string", "clanLevel": 0, "attacks": 0, "stars": 0, "destructionPercentage": 0.0, "members": [{"tag": "string", "name": "string", "townhallLevel": 0, "mapPosition": 0, "attacks": [{"order": 0, "attackerTag": "string", "defenderTag": "string", "stars": 0, "destructionPercentage": 0}]}]}, "opponent": {"tag": "string", "name": "string", "clanLevel": 0, "members": []}}
```
</details>

#### Clan War League Group
```python
api.clan_leaguegroup(tag)
```
<details>
 <summary>Response</summary>

```json
{"tag": "string", "state": "string", "season": "string", "clans": [{"tag": "string", "clanLevel": 0, "name": "string", "members": [{"tag": "string", "townHallLevel": 0, "name": "string"}], "badgeUrls": {}}], "rounds": [{"warTags": ["string"]}]}
```
</details>

#### Capital Raid Seasons
```python
api.clan_capitalraidseasons(tag)
api.clan_capitalraidseasons(tag, {"limit": 5})
```

#### CWL War by Tag
```python
api.warleague(war_tag)
```

---

### Players

#### Player Info
```python
api.players(player_tag)  # e.g. "#900PUCPV"
```
<details>
 <summary>Response</summary>

```json
{
  "tag": "string",
  "name": "string",
  "townHallLevel": 0,
  "expLevel": 0,
  "trophies": 0,
  "bestTrophies": 0,
  "warStars": 0,
  "attackWins": 0,
  "defenseWins": 0,
  "builderHallLevel": 0,
  "builderBaseTrophies": 0,
  "role": "string",
  "warPreference": "string",
  "donations": 0,
  "donationsReceived": 0,
  "clan": {"tag": "string", "name": "string", "clanLevel": 0, "badgeUrls": {}},
  "achievements": [{"name": "string", "stars": 0, "value": 0, "target": 0, "info": "string"}],
  "troops": [{"name": "string", "level": 0, "maxLevel": 0, "village": "string"}],
  "heroes": [{"name": "string", "level": 0, "maxLevel": 0, "village": "string"}],
  "heroEquipment": [],
  "spells": [{"name": "string", "level": 0, "maxLevel": 0, "village": "string"}]
}
```
</details>

#### Verify Player Token
```python
api.verify_player_token(player_tag, "player_api_token")
```
Returns `{"tag": "string", "token": "string", "status": "string"}`.

---

### Locations

#### All Locations
```python
api.location()
api.location({"limit": 10})
```
<details>
 <summary>Response</summary>

```json
{"items": [{"id": 0, "name": "string", "isCountry": true, "countryCode": "string"}], "paging": {"cursors": {}}}
```
</details>

#### Single Location
```python
api.location_id("32000006")
```
<details>
 <summary>Response</summary>

```json
{"id": 0, "name": "string", "isCountry": true, "countryCode": "string"}
```
</details>

#### Top Clans in a Location
```python
api.location_id_clan_rank(location_id)
api.location_id_clan_rank(location_id, {"limit": 10})
```
<details>
 <summary>Response</summary>

```json
{"items": [{"tag": "string", "name": "string", "location": {"id": 0, "name": "string", "isCountry": true, "countryCode": "string"}, "badgeUrls": {}, "clanLevel": 0, "members": 0, "clanPoints": 0, "rank": 0, "previousRank": 0}], "paging": {"cursors": {}}}
```
</details>

#### Top Players in a Location
```python
api.location_id_player_rank(location_id)
```
<details>
 <summary>Response</summary>

```json
{"items": [{"tag": "string", "name": "string", "expLevel": 0, "trophies": 0, "attackWins": 0, "defenseWins": 0, "rank": 0, "previousRank": 0, "clan": {"tag": "string", "name": "string", "badgeUrls": {}}, "league": {"id": 0, "name": "string", "iconUrls": {}}, "leagueTier": {"id": 0, "name": "string", "iconUrls": {}}}], "paging": {"cursors": {}}}
```
</details>

#### Top Builder Base Clans in a Location
```python
api.location_clans_builder_base(location_id)
```
<details>
 <summary>Response</summary>

```json
{"items": [{"tag": "string", "name": "string", "location": {"id": 0, "name": "string", "isCountry": true, "countryCode": "string"}, "badgeUrls": {}, "clanLevel": 0, "members": 0, "rank": 0, "previousRank": 0, "clanBuilderBasePoints": 0}], "paging": {"cursors": {}}}
```
</details>

#### Top Builder Base Players in a Location
```python
api.location_players_builder_base(location_id)
```
<details>
 <summary>Response</summary>

```json
{"items": [{"tag": "string", "name": "string", "expLevel": 0, "rank": 0, "previousRank": 0, "builderBaseTrophies": 0, "clan": {"tag": "string", "name": "string", "badgeUrls": {}}, "builderBaseLeague": {"id": 0, "name": "string"}}], "paging": {"cursors": {}}}
```
</details>

#### Capital Rankings in a Location
```python
api.location_capital_rankings(location_id)
```
<details>
 <summary>Response</summary>

```json
{"items": [{"tag": "string", "name": "string", "location": {"id": 0, "name": "string", "isCountry": true, "countryCode": "string"}, "badgeUrls": {}, "clanLevel": 0, "members": 0, "rank": 0, "previousRank": 0, "clanCapitalPoints": 0}], "paging": {"cursors": {}}}
```
</details>

#### Top Versus Clans in a Location (Deprecated)
```python
api.location_clan_versus(location_id)
```
> **Deprecated**: May return an error with `error_type: "deprecated"`.

#### Top Versus Players in a Location (Deprecated)
```python
api.location_player_versus(location_id)
```
> **Deprecated**: May return an error with `error_type: "deprecated"`.

---

### Leagues

#### List Leagues
```python
api.league()
api.league({"limit": 5})
```
<details>
 <summary>Response</summary>

```json
{"items": [{"id": 0, "name": "string", "iconUrls": {}}], "paging": {"cursors": {}}}
```
</details>

#### League Info
```python
api.league_id("29000022")
```
<details>
 <summary>Response</summary>

```json
{"id": 0, "name": "string", "iconUrls": {"small": "string", "tiny": "string", "medium": "string"}}
```
</details>

#### Legend League Seasons
```python
api.league_season("29000022")
```
<details>
 <summary>Response</summary>

```json
{"items": [{"id": "string"}], "paging": {"cursors": {}}}
```
</details>

#### Legend League Season Rankings
```python
api.league_season_id("29000022", "2025-01", {"limit": 100})
```
Note: `limit` must be between 100 and 25,000.
<details>
 <summary>Response</summary>

```json
{"items": [{"tag": "string", "name": "string", "expLevel": 0, "trophies": 0, "attackWins": 0, "defenseWins": 0, "rank": 0, "clan": {"tag": "string", "name": "string", "badgeUrls": {}}, "leagueTier": {"id": 0, "name": "string", "iconUrls": {}}}], "paging": {"cursors": {}}}
```
</details>

#### Capital Leagues
```python
api.capitalleagues()
api.capitalleagues_id("85000000")
```
<details>
 <summary>Response</summary>

```json
{"items": [{"id": 0, "name": "string"}], "paging": {"cursors": {}}}
```
</details>

#### Builder Base Leagues
```python
api.builderbaseleagues()
api.builderbaseleagues_id("44000000")
```
<details>
 <summary>Response</summary>

```json
{"items": [{"id": 0, "name": "string"}], "paging": {"cursors": {}}}
```
</details>

#### League Tiers
```python
api.leaguetiers()
api.leaguetiers_id("105000001")
```
<details>
 <summary>Response</summary>

```json
{"items": [{"id": 0, "name": "string", "iconUrls": {"small": "string", "large": "string"}}], "paging": {"cursors": {}}}
```
</details>

#### War Leagues
```python
api.warleagues()
api.warleagues_id("48000000")
```
<details>
 <summary>Response</summary>

```json
{"items": [{"id": 0, "name": "string"}], "paging": {"cursors": {}}}
```
</details>

---

### Gold Pass

```python
api.goldpass()
```
<details>
 <summary>Response</summary>

```json
{"startTime": "string", "endTime": "string"}
```
</details>

---

### Labels

#### Clan Labels
```python
api.labels_clans()
```
<details>
 <summary>Response</summary>

```json
{"items": [{"id": 0, "name": "string", "iconUrls": {}}], "paging": {"cursors": {}}}
```
</details>

#### Player Labels
```python
api.labels_players()
```
<details>
 <summary>Response</summary>

```json
{"items": [{"id": 0, "name": "string", "iconUrls": {}}], "paging": {"cursors": {}}}
```
</details>

---

## Error Handling

All endpoints return a dict. Errors have this structure:

```python
result = api.clan_tag("#INVALID")
if result.get("result") == "error":
    print(result["message"])      # Human-readable message
    print(result["error_type"])   # "timeout", "connection", "http", "json", "retry_exhausted", "unknown"
    print(result.get("status_code"))  # HTTP status code if applicable
```

## Pydantic Models

When `use_pydantic_models=True` (requires `pip install 'cocapi[pydantic]'`), endpoints return typed model objects instead of dicts:

```python
from cocapi import CocApi, ApiConfig

config = ApiConfig(use_pydantic_models=True)
api = CocApi("token", config=config)

clan = api.clan_tag("#2PP")
print(clan.name)        # Attribute access with IDE autocompletion
print(clan.clanLevel)

player = api.players("#TAG")
print(player.trophies)
```

Available models: `Clan`, `Player`, `ClanMember`, `League`, `Location`, `Achievement`, `ClanWar`, `GoldPassSeason`, and more. Import directly from `cocapi`.

## Credits

- [All Contributors](../../contributors)

*cocapi is not affiliated with SuperCell.*
