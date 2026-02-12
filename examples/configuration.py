"""Advanced configuration, caching, metrics, and middleware.

Demonstrates:
- ApiConfig options
- Cache management
- Request metrics
- Custom middleware
- Base URL override
"""

from cocapi import ApiConfig, CocApi
from cocapi.middleware import (
    add_request_id_middleware,
    add_user_agent_middleware,
)

# --- Full configuration ---
config = ApiConfig(
    timeout=30,
    max_retries=3,
    retry_delay=1.0,  # Base delay for exponential backoff
    # Caching
    enable_caching=True,
    cache_ttl=600,  # 10 minutes
    # Rate limiting (async only)
    enable_rate_limiting=True,
    requests_per_second=10.0,
    burst_limit=20,
    # Metrics
    enable_metrics=True,
    metrics_window_size=1000,
)

api = CocApi("YOUR_API_TOKEN", config=config)

# --- Make some requests ---
api.clan_tag("#2PP")
api.players("#900PUCPV")
api.clan_tag("#2PP")  # This one hits the cache

# --- Cache stats ---
stats = api.get_cache_stats()
print(f"Cache: {stats['hit_count']} hits, {stats['miss_count']} misses")
api.clear_cache()

# --- Metrics ---
metrics = api.get_metrics()
print(f"Requests: {metrics['total_requests']}")
print(f"Avg response time: {metrics.get('avg_response_time', 0):.3f}s")
api.clear_metrics()

# --- Middleware ---
# Add headers to every request
api.add_request_middleware(add_user_agent_middleware("MyBot/1.0"))
api.add_request_middleware(add_request_id_middleware())


# Custom middleware
def log_requests(
    url: str, headers: dict, params: dict
) -> tuple[str, dict, dict]:
    print(f"  -> {url}")
    return url, headers, params


api.add_request_middleware(log_requests)
api.clan_tag("#2PP")  # Will print the URL

# --- Base URL override (for proxies or testing) ---
# api.set_base_url("https://my-proxy.com/clash/v1", force=True)
# api.reset_base_url()  # Back to official
