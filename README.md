<p>
    <a href="https://github.com/tonybenoy/cocapi/actions">
        <img src="https://github.com/tonybenoy/cocapi/workflows/CI/badge.svg" alt="CI Status" height="20">
    </a>
    <a href="https://pypi.org/project/cocapi/"><img src="https://img.shields.io/pypi/v/cocapi" alt="Pypi version" height="21"></a>
    <a href="https://pypi.org/project/cocapi/"><img src="https://img.shields.io/pypi/dm/cocapi" alt="PyPI Downloads" height="21"></a>
    <a href="https://tonybenoy.github.io/cocapi/"><img src="https://img.shields.io/badge/docs-mkdocs-blue.svg" alt="Documentation" height="21"></a>
</p>
<p>
    <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python version" height="17"></a>
    <a href="https://github.com/tonybenoy/cocapi/blob/main/LICENSE"><img src="https://img.shields.io/github/license/tonybenoy/cocapi" alt="License" height="17"></a>
    <a href="https://github.com/astral-sh/ruff">
        <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff" height="17">
    </a>
</p>

# cocapi

A Python wrapper for the official [Clash of Clans API](https://developer.clashofclans.com/) with full async support, automatic key management, caching, retries, and optional Pydantic models.

**[Full Documentation](https://tonybenoy.github.io/cocapi/)**

## Features

- **Sync & async** — same methods, same names, both modes
- **Automatic key management** — login with email/password, keys are created, reused, and rotated automatically
- **Caching** — TTL-based response caching with stats
- **Retries** — exponential backoff for rate limits and server errors
- **Pagination & batch** — `paginate()` auto-follows cursors, `batch()` fetches many resources at once
- **Event polling** — real-time monitoring of clans, wars, and players with `async for` or callbacks
- **Pydantic models** — optional typed response objects with IDE autocompletion
- **Middleware** — plug in custom request/response processing
- **CLI** — `cocapi clan "#2PP"` from the terminal
- **Maintenance detection** — automatic detection of API maintenance windows

## Install

```bash
pip install cocapi

# With Pydantic model support
pip install 'cocapi[pydantic]'

# With CLI
pip install 'cocapi[cli]'
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

Keys are created automatically, reused when valid, and rotated when your IP changes. See the [Authentication guide](https://tonybenoy.github.io/cocapi/getting-started/authentication/) for details.

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

See the [Async guide](https://tonybenoy.github.io/cocapi/guides/async/) for more patterns.

## Configuration

All options are set through `ApiConfig`:

```python
from cocapi import CocApi, ApiConfig

config = ApiConfig(
    timeout=30,
    max_retries=3,
    enable_caching=True,
    cache_ttl=600,
    enable_rate_limiting=True,     # async only
    requests_per_second=10.0,
    enable_metrics=True,
    use_pydantic_models=True,      # requires cocapi[pydantic]
)

api = CocApi("your_token", config=config)
```

See the [Configuration guide](https://tonybenoy.github.io/cocapi/guides/configuration/) for all options.

## Pagination & Batch

```python
# Auto-paginate through all clan members
for member in api.paginate(api.clan_members, "#CLAN_TAG"):
    print(member["name"])

# Fetch multiple players at once
results = api.batch(api.players, ["#TAG1", "#TAG2", "#TAG3"])
```

Both work in sync and async. See the [Pagination & Batch guide](https://tonybenoy.github.io/cocapi/guides/pagination-batch/).

## Event Polling

Monitor clans, wars, and players in real time. Async only.

```python
from cocapi.events import EventStream, EventType

async with CocApi("token") as api:
    stream = EventStream(api)
    stream.watch_clans(["#2PP"], interval=60)
    stream.watch_wars(["#2PP"], interval=30)
    stream.watch_players(["#900PUCPV"], interval=120)

    async with stream:
        async for event in stream:
            print(event.event_type, event.tag)
            for change in event.changes:
                print(f"  {change.field}: {change.old_value} -> {change.new_value}")
```

Supports 20+ event types including member join/leave, war state transitions, troop/hero upgrades, maintenance detection, and more. See the [Event Polling guide](https://tonybenoy.github.io/cocapi/guides/events/).

## CLI

```bash
pip install 'cocapi[cli]'

# Login once (key is persisted)
cocapi login --email you@example.com --password yourpass

# Use without --token
cocapi clan "#2PP"
cocapi player "#900PUCPV"
cocapi war "#2PP"
cocapi search "clash" --limit 5
cocapi goldpass
```

See the [CLI guide](https://tonybenoy.github.io/cocapi/guides/cli/) for all commands.

## Error Handling

All endpoints return a dict (or Pydantic model). Errors never raise exceptions:

```python
result = api.clan_tag("#INVALID")
if result.get("result") == "error":
    print(result["message"])       # Human-readable message
    print(result["error_type"])    # "timeout", "connection", "http", "json", etc.
    print(result.get("status_code"))
```

See the [Error Handling guide](https://tonybenoy.github.io/cocapi/guides/error-handling/).

## Examples

Runnable scripts in the [`examples/`](examples/) folder:

| Script | What it covers |
|---|---|
| [`basic_usage.py`](examples/basic_usage.py) | Sync: clan info, player info, search, error handling |
| [`async_usage.py`](examples/async_usage.py) | Async with context manager, concurrent requests |
| [`credential_auth.py`](examples/credential_auth.py) | Email/password login, key persistence, auto-refresh |
| [`pagination_batch.py`](examples/pagination_batch.py) | `paginate()` and `batch()` in sync and async |
| [`event_polling.py`](examples/event_polling.py) | `EventStream` with `async for` — real-time monitoring |
| [`event_callbacks.py`](examples/event_callbacks.py) | `@stream.on()` decorators and `stream.run()` |
| [`configuration.py`](examples/configuration.py) | ApiConfig, caching, metrics, middleware |

## API Reference

Full API reference with all endpoints, parameters, and response schemas is available in the [documentation](https://tonybenoy.github.io/cocapi/reference/).

Key classes:
- [`CocApi`](https://tonybenoy.github.io/cocapi/reference/client/) — main entry point (sync/async)
- [`ApiConfig`](https://tonybenoy.github.io/cocapi/reference/config/) — configuration options
- [`EventStream`](https://tonybenoy.github.io/cocapi/reference/events/) — real-time event polling
- [Pydantic Schemas](https://tonybenoy.github.io/cocapi/reference/schemas/) — typed response models
- [All Endpoints](https://tonybenoy.github.io/cocapi/reference/api_methods/) — every API method

## Credits

- [All Contributors](../../contributors)

*cocapi is not affiliated with SuperCell.*
