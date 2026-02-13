# cocapi

<p>
    <a href="https://github.com/tonybenoy/cocapi/actions">
        <img src="https://github.com/tonybenoy/cocapi/workflows/CI/badge.svg" alt="CI Status" height="20">
    </a>
    <a href="https://pypi.org/project/cocapi/"><img src="https://img.shields.io/pypi/v/cocapi" alt="Pypi version" height="21"></a>
    <a href="https://pypi.org/project/cocapi/"><img src="https://img.shields.io/pypi/dm/cocapi" alt="PyPI Downloads" height="21"></a>
    <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python version" height="17"></a>
    <a href="https://github.com/tonybenoy/cocapi/blob/master/LICENSE"><img src="https://img.shields.io/github/license/tonybenoy/cocapi" alt="License" height="17"></a>
</p>

A Python wrapper for the official [Clash of Clans API](https://developer.clashofclans.com/) with full async support, automatic key management, caching, retries, and optional Pydantic models.

## Features

- **Sync & Async** — Same API, both modes. Use `await` in async, plain calls in sync.
- **Automatic Key Management** — Log in with developer portal credentials; keys are created, rotated, and persisted automatically.
- **Caching** — Built-in TTL-based response cache to reduce API calls.
- **Retries** — Exponential backoff on transient failures.
- **Rate Limiting** — Async token-bucket rate limiter with burst support.
- **Pagination & Batch** — `paginate()` iterates all pages; `batch()` fetches many resources at once.
- **Event Polling** — Monitor clans, wars, and players in real time with `EventStream`.
- **Pydantic Models** — Optional typed response models with IDE autocompletion.
- **Middleware** — Plug in custom request/response processing.
- **Metrics** — Track request counts, latencies, and error rates.
- **CLI** — Command-line interface for quick lookups.

## Quick Example

```python
from cocapi import CocApi

api = CocApi("your_api_token")

clan = api.clan_tag("#2PP")
print(clan["name"])

player = api.players("#900PUCPV")
print(player["trophies"])
```

Or with async:

```python
import asyncio
from cocapi import CocApi

async def main():
    async with CocApi("your_token") as api:
        clan = await api.clan_tag("#2PP")
        print(clan["name"])

asyncio.run(main())
```

## Next Steps

- [Installation](getting-started/installation.md) — Install cocapi and optional extras
- [Quick Start](getting-started/quickstart.md) — Get up and running in minutes
- [Authentication](getting-started/authentication.md) — Token vs credential-based auth
- [API Reference](reference/index.md) — Full auto-generated API docs
