"""
Configuration management for cocapi
"""

from dataclasses import dataclass
from typing import Optional


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

    # Monitoring and metrics
    enable_metrics: bool = False  # Track request metrics
    metrics_window_size: int = 1000  # Number of requests to track

    # Connection optimization
    enable_keepalive: bool = True  # Enable HTTP keep-alive
    max_connections: int = 10  # Maximum connections in pool
    max_keepalive_connections: int = 5  # Maximum keep-alive connections


@dataclass
class CacheEntry:
    """Cache entry with TTL support"""

    data: dict
    timestamp: float
    ttl: int

    def is_expired(self, current_time: float) -> bool:
        """Check if cache entry is expired"""
        return (current_time - self.timestamp) > self.ttl


@dataclass
class RequestMetric:
    """Metrics for a single API request"""

    endpoint: str
    method: str
    status_code: int
    response_time: float
    timestamp: float
    cache_hit: bool
    error_type: Optional[str] = None
