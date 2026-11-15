"""
Per-call request controls (cache and rate-limit overrides).

These use :mod:`contextvars`, so they work identically for sync code and
asyncio tasks, and never leak across concurrent tasks.

Example::

    from cocapi import cache_control, without_rate_limit

    with cache_control(lookup=False):          # force a fresh fetch
        clan = api.clan_tag("#ABC")

    with cache_control(update=False):          # don't store this response
        clan = api.clan_tag("#ABC")

    with without_rate_limit():                 # skip the async rate limiter
        data = await api.clan_tag("#ABC")
"""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

_cache_lookup: ContextVar[bool] = ContextVar("cocapi_cache_lookup", default=True)
_cache_update: ContextVar[bool] = ContextVar("cocapi_cache_update", default=True)
_skip_rate_limit: ContextVar[bool] = ContextVar("cocapi_skip_rate_limit", default=False)


@contextmanager
def cache_control(lookup: bool = True, update: bool = True) -> Iterator[None]:
    """Override response caching for requests made inside the ``with`` block.

    Args:
        lookup: If False, ignore any cached entry and hit the API.
        update: If False, don't store the fresh response in the cache.
    """
    t1 = _cache_lookup.set(lookup)
    t2 = _cache_update.set(update)
    try:
        yield
    finally:
        _cache_lookup.reset(t1)
        _cache_update.reset(t2)


@contextmanager
def without_rate_limit() -> Iterator[None]:
    """Bypass the async rate limiter for requests made inside the block."""
    token = _skip_rate_limit.set(True)
    try:
        yield
    finally:
        _skip_rate_limit.reset(token)


def cache_lookup_enabled() -> bool:
    return _cache_lookup.get()


def cache_update_enabled() -> bool:
    return _cache_update.get()


def rate_limit_skipped() -> bool:
    return _skip_rate_limit.get()
