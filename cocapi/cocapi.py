"""
Clash of Clans API Wrapper - Main entry point for backward compatibility

This module provides the main CocApi class with full backward compatibility
while using the new modular architecture introduced in v3.0.0.
"""

# Import the modular client
# Import async client components for direct access
from .async_client import AsyncCocApiCore, AsyncRateLimiter
from .cache import CacheManager
from .client import CocApi

# Import all configuration and utility classes
from .config import ApiConfig, CacheEntry, RequestMetric
from .metrics import MetricsTracker
from .middleware import MiddlewareManager
from .models import create_dynamic_model, get_pydantic_info, validate_pydantic_available
from .utils import build_url, clean_tag, get_cache_key, validate_params

# Export everything for backward compatibility and advanced usage
__all__ = [
    # Main API class
    "CocApi",
    # Async components
    "AsyncCocApiCore",
    "AsyncRateLimiter",
    # Configuration
    "ApiConfig",
    "CacheEntry",
    "RequestMetric",
    # Component managers
    "CacheManager",
    "MetricsTracker",
    "MiddlewareManager",
    # Utility functions
    "create_dynamic_model",
    "validate_pydantic_available",
    "get_pydantic_info",
    "clean_tag",
    "build_url",
    "validate_params",
    "get_cache_key",
]

# For backward compatibility, expose the main class at module level
# Users can still import as: from cocapi.cocapi import CocApi
# or the preferred: from cocapi import CocApi
