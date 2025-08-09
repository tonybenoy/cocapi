"""
Configuration management for cocapi
"""

from dataclasses import dataclass


@dataclass
class ApiConfig:
    """Configuration class for CocApi"""

    base_url: str = "https://api.clashofclans.com/v1"
    timeout: int = 20
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds
    cache_ttl: int = 300  # seconds (5 minutes)
    enable_caching: bool = True
    enable_rate_limiting: bool = True

    # Pydantic model settings
    use_pydantic_models: bool = False  # Optional Pydantic model validation

    # Rate limiting settings
    requests_per_second: float = 10.0
    burst_limit: int = 20


@dataclass
class CacheEntry:
    """Cache entry with TTL support"""

    data: dict
    timestamp: float
    ttl: int

    def is_expired(self, current_time: float) -> bool:
        """Check if cache entry is expired"""
        return (current_time - self.timestamp) > self.ttl
