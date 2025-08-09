"""
Caching functionality for cocapi
"""

import time
from typing import Any, Dict, Optional

from .config import CacheEntry
from .utils import get_cache_key


class CacheManager:
    """Manages response caching with TTL support"""

    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache manager

        Args:
            default_ttl: Default time-to-live in seconds (5 minutes)
        """
        self.cache: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
        self._enabled = True
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "evictions": 0,
        }

    def enable(self) -> None:
        """Enable caching"""
        self._enabled = True

    def disable(self) -> None:
        """Disable caching"""
        self._enabled = False

    def is_enabled(self) -> bool:
        """Check if caching is enabled"""
        return self._enabled

    def get(
        self, url: str, params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response if available and not expired

        Args:
            url: Request URL
            params: Request parameters

        Returns:
            Cached response data or None if not found/expired
        """
        if not self._enabled:
            return None

        cache_key = get_cache_key(url, params)
        current_time = time.time()

        if cache_key in self.cache:
            entry = self.cache[cache_key]

            if not entry.is_expired(current_time):
                self._stats["hits"] += 1
                return entry.data
            else:
                # Remove expired entry
                del self.cache[cache_key]
                self._stats["evictions"] += 1

        self._stats["misses"] += 1
        return None

    def set(
        self,
        url: str,
        params: Optional[Dict[str, Any]],
        data: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> None:
        """
        Cache response data

        Args:
            url: Request URL
            params: Request parameters
            data: Response data to cache
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        if not self._enabled:
            return

        # Don't cache error responses
        if data.get("result") == "error":
            return

        cache_key = get_cache_key(url, params)
        ttl = ttl or self.default_ttl

        self.cache[cache_key] = CacheEntry(
            data=data.copy(), timestamp=time.time(), ttl=ttl
        )

        self._stats["sets"] += 1

    def invalidate(self, url: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Invalidate specific cached entry

        Args:
            url: Request URL
            params: Request parameters

        Returns:
            True if entry was found and removed, False otherwise
        """
        cache_key = get_cache_key(url, params)

        if cache_key in self.cache:
            del self.cache[cache_key]
            self._stats["evictions"] += 1
            return True

        return False

    def clear(self) -> int:
        """
        Clear all cached entries

        Returns:
            Number of entries cleared
        """
        count = len(self.cache)
        self.cache.clear()
        self._stats["evictions"] += count
        return count

    def cleanup_expired(self) -> int:
        """
        Remove expired entries

        Returns:
            Number of expired entries removed
        """
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items() if entry.is_expired(current_time)
        ]

        for key in expired_keys:
            del self.cache[key]

        self._stats["evictions"] += len(expired_keys)
        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (
            (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        )

        # Count expired entries
        current_time = time.time()
        expired_count = sum(
            1 for entry in self.cache.values() if entry.is_expired(current_time)
        )

        return {
            "enabled": self._enabled,
            "total_entries": len(self.cache),
            "expired_entries": expired_count,
            "valid_entries": len(self.cache) - expired_count,
            "default_ttl": self.default_ttl,
            "hit_rate": round(hit_rate, 2),
            "stats": self._stats.copy(),
        }

    def get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information"""
        current_time = time.time()
        entries = []

        for key, entry in self.cache.items():
            entries.append(
                {
                    "key": key,
                    "size_estimate": len(str(entry.data)),
                    "ttl": entry.ttl,
                    "age": round(current_time - entry.timestamp, 2),
                    "expires_in": round(
                        (entry.timestamp + entry.ttl) - current_time, 2
                    ),
                    "is_expired": entry.is_expired(current_time),
                }
            )

        # Sort by expiration time (soonest to expire first)
        from typing import cast

        entries.sort(key=lambda x: cast(float, x["expires_in"]))

        return {
            "entries": entries,
            "memory_usage_estimate": sum(e["size_estimate"] for e in entries),
        }

    def set_default_ttl(self, ttl: int) -> None:
        """Set default TTL for new cache entries"""
        self.default_ttl = ttl

    def get_entry_info(
        self, url: str, params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Get information about a specific cache entry"""
        cache_key = get_cache_key(url, params)

        if cache_key not in self.cache:
            return None

        entry = self.cache[cache_key]
        current_time = time.time()

        return {
            "key": cache_key,
            "ttl": entry.ttl,
            "age": round(current_time - entry.timestamp, 2),
            "expires_in": round((entry.timestamp + entry.ttl) - current_time, 2),
            "is_expired": entry.is_expired(current_time),
            "size_estimate": len(str(entry.data)),
            "cached_at": entry.timestamp,
        }

    def extend_ttl(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        additional_seconds: int = 300,
    ) -> bool:
        """
        Extend TTL for a specific cache entry

        Args:
            url: Request URL
            params: Request parameters
            additional_seconds: Seconds to add to current TTL

        Returns:
            True if entry was found and updated, False otherwise
        """
        cache_key = get_cache_key(url, params)

        if cache_key in self.cache:
            entry = self.cache[cache_key]
            entry.ttl += additional_seconds
            return True

        return False

    def touch(self, url: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Reset timestamp for cache entry (extends its life without changing TTL)

        Args:
            url: Request URL
            params: Request parameters

        Returns:
            True if entry was found and touched, False otherwise
        """
        cache_key = get_cache_key(url, params)

        if cache_key in self.cache:
            entry = self.cache[cache_key]
            entry.timestamp = time.time()
            return True

        return False
