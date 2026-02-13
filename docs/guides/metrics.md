# Metrics

Track request counts, latencies, and error rates.

## Setup

```python
from cocapi import CocApi, ApiConfig

config = ApiConfig(
    enable_metrics=True,
    metrics_window_size=1000,  # Track last 1000 requests (default)
)

api = CocApi("token", config=config)
```

## Getting Metrics

```python
metrics = api.get_metrics()
print(metrics)
# {
#     "total_requests": 150,
#     "total_errors": 3,
#     "error_rate": 0.02,
#     "avg_response_time": 0.245,
#     "cache_hit_rate": 0.64,
#     "endpoints": {
#         "/clans/{tag}": {"count": 50, "avg_time": 0.21, ...},
#         "/players/{tag}": {"count": 100, "avg_time": 0.26, ...},
#     },
#     ...
# }
```

## Clearing Metrics

```python
api.clear_metrics()
```

## What's Tracked

Each request records:

- **Endpoint** — The API path
- **Method** — GET or POST
- **Status code** — HTTP response code
- **Response time** — Seconds from request to response
- **Cache hit** — Whether the response came from cache
- **Error type** — If the request failed (`timeout`, `connection`, `http`, etc.)

The `MetricsTracker` maintains a rolling window of the last `metrics_window_size` requests, so memory usage stays bounded.
