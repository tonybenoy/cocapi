"""
Utility functions for cocapi
"""

import urllib.parse
from typing import Any


def clean_tag(tag: str) -> str:
    """Remove # prefix from clan/player tags if present"""
    return tag[1:] if tag.startswith("#") else tag


def build_url(
    base_url: str, endpoint: str, params: dict[str, Any] | None = None
) -> str:
    """Build a complete URL with parameters"""
    if params:
        # Filter out None values and empty parameters
        filtered_params = {k: v for k, v in params.items() if v is not None and v != ""}
        if filtered_params:
            query_string = urllib.parse.urlencode(filtered_params)
            return f"{base_url}{endpoint}?{query_string}"
    return f"{base_url}{endpoint}"


def validate_params(
    params: dict[str, Any] | None, valid_params: tuple[str, ...]
) -> bool:
    """Validate that all parameters are in the allowed list"""
    if not params:
        return True
    return all(param in valid_params for param in params.keys())


def get_cache_key(url: str, params: dict[str, Any] | None = None) -> str:
    """Generate a cache key from URL and parameters"""
    if params:
        sorted_params = sorted(params.items())
        param_str = "&".join(f"{k}={v}" for k, v in sorted_params)
        return f"{url}?{param_str}"
    return url


def is_successful_response(status_code: int) -> bool:
    """Check if HTTP status code indicates success"""
    return 200 <= status_code < 300


def should_retry_error(status_code: int) -> bool:
    """Determine if an HTTP error should be retried"""
    return status_code == 429 or status_code >= 500


def extract_items(result: Any) -> list[Any]:
    """Extract items list from a paginated API response (dict or Pydantic model)."""
    if isinstance(result, dict):
        return result.get("items", [])
    return getattr(result, "items", [])


def extract_after_cursor(result: Any) -> str | None:
    """Extract the 'after' cursor from a paginated API response (dict or Pydantic model)."""
    if isinstance(result, dict):
        paging = result.get("paging")
        if not paging:
            return None
        cursors = paging.get("cursors")
        if not cursors:
            return None
        return cursors.get("after")
    # Pydantic model path
    paging = getattr(result, "paging", None)
    if not paging:
        return None
    cursors = getattr(paging, "cursors", None)
    if not cursors:
        return None
    return getattr(cursors, "after", None)


def format_endpoint_for_metrics(endpoint: str) -> str:
    """Format endpoint path for metrics tracking (remove dynamic parts)"""
    # Replace clan/player tags with placeholder for better grouping
    import re

    # Replace patterns like /%23ABC123 with /%23{tag}
    endpoint = re.sub(r"/%23[A-Z0-9]+", "/%23{tag}", endpoint)
    # Replace other IDs with placeholder
    endpoint = re.sub(r"/[0-9]+", "/{id}", endpoint)
    return endpoint
