# Changelog

## v4.1.0

- **Error classification** — error dicts now include `error_kind` (`maintenance`, `private_war_log`, `invalid_ip`, `not_found`, `rate_limited`, ...) and `reason` when the API provides one. `error_type` is unchanged. New typed exceptions + `raise_for_error()` for opt-in raising
- **Current war with CWL fallback** — `api.clan_current_war_auto(tag)` falls back to the clan's Clan War League war (sync + async), handling private war logs
- **Per-call cache/rate-limit control** — `cache_control(lookup=, update=)` and `without_rate_limit()` context managers
- **Static game data** — `StaticData` loads/downloads (opt-in) troop, spell, hero, pet, equipment and league data with name/ID lookups
- **Army links** — `parse_army_link()` / `build_army_link()`
- **Event windows** — `clan_games_window()`, `raid_weekend_window()`, `legend_day_window()`
- `ClanCapital.clanGoldSinkTotal` schema field

## v4.0.0

- **Event Polling System** — New `cocapi.events` module with `EventStream` for real-time monitoring of clans, wars, and players via poll-and-compare
  - `ClanWatcher` — Detects clan field changes, member join/leave/update, role changes, donations
  - `WarWatcher` — War state machine tracking transitions, new attack detection
  - `PlayerWatcher` — Field-level diffs with upgrade detection (troops, spells, heroes, hero equipment, TH, BH)
  - Callback decorators via `@stream.on(EventType)`
  - Backpressure with bounded `asyncio.Queue`
  - Optional state persistence for restart recovery
  - Maintenance window detection
- **CLI** — New `cocapi` command-line interface (optional, via `cocapi[cli]`)
  - Persistent credential login (`cocapi login`)
  - Commands for all API endpoints
  - JSON output mode
- **Pydantic Models** — Optional typed response models (via `cocapi[pydantic]`)
  - 45+ schema classes covering all API responses
  - Model registry mapping endpoints to schemas
  - Dynamic model fallback for unknown endpoints
- **Credential-Based Auth** — `CocApi.from_credentials()` with automatic key management
  - IP detection, key creation, rotation on IP change
  - Key persistence with `persist_keys=True`
  - Standalone `SyncKeyManager` / `AsyncKeyManager`
- **Batch Fetch** — `api.batch()` for fetching multiple resources
- **Pagination Helper** — `api.paginate()` for auto-following cursors
- **Middleware System** — Request and response middleware with 5 built-in functions
- **Metrics Tracking** — `MetricsTracker` with rolling window
- **Custom Endpoints** — `api.custom_endpoint()` for future API additions
- **Base URL Override** — Configurable base URL for proxies/testing

## v3.0.0

- Enhanced `CocApi` with `ApiConfig` dataclass
- Caching, rate limiting, middleware, and metrics
- Async context manager support
- Dynamic Pydantic model generation

## v2.0.0

- Async support via httpx
- Improved error handling

## v1.0.0

- Initial release — sync-only wrapper for Clash of Clans API
