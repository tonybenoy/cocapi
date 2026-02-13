# Caching

cocapi includes a built-in TTL-based in-memory response cache.

## Configuration

```python
from cocapi import CocApi, ApiConfig

config = ApiConfig(
    enable_caching=True,   # Default: True
    cache_ttl=600,         # Seconds (default: 300 = 5 minutes)
)

api = CocApi("token", config=config)
```

## How It Works

1. Before each request, the cache is checked using the URL + query params as key
2. If a valid (non-expired) entry exists, it's returned without making an HTTP request
3. Successful responses are stored in the cache with the configured TTL
4. Expired entries are cleaned up automatically

## Cache Stats

```python
stats = api.get_cache_stats()
print(stats)
# {
#     "enabled": True,
#     "size": 42,
#     "hits": 156,
#     "misses": 87,
#     "hit_rate": 0.642,
#     ...
# }
```

## Clearing the Cache

```python
cleared = api.clear_cache()
print(f"Cleared {cleared} entries")
```

## When to Disable Caching

- **Event polling** — Disable caching so polls always return fresh data:

    ```python
    config = ApiConfig(enable_caching=False)
    ```

- **Time-sensitive data** — When you need real-time accuracy (live war attacks, etc.)

- **Low-memory environments** — The cache stores full response dicts in memory
