# Async Usage

cocapi supports both sync and async modes using the same API methods.

## Async Context Manager

Use `async with` to enable async mode:

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

The context manager:

1. Enables async mode automatically
2. Creates an async HTTP client with connection pooling
3. Tests the API connection
4. Cleans up the client on exit

## Concurrent Requests

Use `asyncio.gather` for concurrent requests:

```python
async with CocApi("token") as api:
    tags = ["#TAG1", "#TAG2", "#TAG3"]
    players = await asyncio.gather(*[api.players(t) for t in tags])
```

Or use the built-in [`batch()`](pagination-batch.md#batch-fetch) helper.

## Rate Limiting

Async mode includes a token-bucket rate limiter:

```python
from cocapi import CocApi, ApiConfig

config = ApiConfig(
    enable_rate_limiting=True,   # Default: True
    requests_per_second=10.0,    # Default: 10.0
    burst_limit=20,              # Default: 20
)

async with CocApi("token", config=config) as api:
    # Requests are automatically throttled
    for tag in many_tags:
        player = await api.players(tag)
```

!!! note
    Rate limiting only applies in async mode. Sync mode does not rate-limit.

## Connection Pooling

Configure the async HTTP connection pool:

```python
config = ApiConfig(
    enable_keepalive=True,             # Default: True
    max_connections=10,                # Default: 10
    max_keepalive_connections=5,       # Default: 5
)
```

## Sync vs Async Comparison

=== "Sync"

    ```python
    from cocapi import CocApi

    api = CocApi("token")
    clan = api.clan_tag("#2PP")
    print(clan["name"])
    ```

=== "Async"

    ```python
    import asyncio
    from cocapi import CocApi

    async def main():
        async with CocApi("token") as api:
            clan = await api.clan_tag("#2PP")
            print(clan["name"])

    asyncio.run(main())
    ```

## Credential Auth in Async

```python
from cocapi import CocApi

api = CocApi.from_credentials("email", "password")

async with api as api:
    clan = await api.clan_tag("#2PP")
```

The initial credential login is synchronous (it contacts the developer portal). Once the token is obtained, async mode works normally.
