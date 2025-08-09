"""
Async functionality for cocapi
"""

import asyncio
import time
from typing import Any, Dict, Optional

import httpx

from .cache import CacheManager
from .config import ApiConfig
from .metrics import MetricsTracker
from .middleware import MiddlewareManager
from .models import create_dynamic_model
from .utils import build_url, is_successful_response, should_retry_error


class AsyncRateLimiter:
    """Simple async rate limiter using token bucket algorithm"""

    def __init__(self, rate: float, burst: int):
        """
        Initialize rate limiter

        Args:
            rate: Requests per second
            burst: Maximum burst requests
        """
        self.rate = rate
        self.burst = burst
        self.tokens = float(burst)
        self.last_update = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire permission to make a request"""
        async with self._lock:
            now = time.time()
            time_passed = now - self.last_update
            self.tokens = min(float(self.burst), self.tokens + time_passed * self.rate)
            self.last_update = now

            if self.tokens < 1:
                sleep_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(sleep_time)
                self.tokens = 0
            else:
                self.tokens -= 1


class AsyncCocApiCore:
    """Core async functionality for CocApi"""

    def __init__(self, token: str, config: ApiConfig):
        """
        Initialize async core

        Args:
            token: API token
            config: Configuration object
        """
        self.token = token
        self.config = config
        self.headers = {
            "authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        # Initialize components
        self.cache = CacheManager(default_ttl=config.cache_ttl)
        self.cache.enable() if config.enable_caching else self.cache.disable()

        self.metrics = MetricsTracker(max_metrics=config.metrics_window_size)
        self.metrics.enable() if config.enable_metrics else self.metrics.disable()

        self.middleware = MiddlewareManager()

        # Async-specific attributes
        self._client: Optional[httpx.AsyncClient] = None
        self._should_close_client = False
        self._rate_limiter: Optional[AsyncRateLimiter] = None

        if config.enable_rate_limiting:
            self._rate_limiter = AsyncRateLimiter(
                rate=config.requests_per_second, burst=config.burst_limit
            )

    async def __aenter__(self) -> "AsyncCocApiCore":
        """Async context manager entry"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.config.timeout,
                limits=httpx.Limits(
                    max_connections=self.config.max_connections,
                    max_keepalive_connections=self.config.max_keepalive_connections,
                ),
                http2=True,
            )
            self._should_close_client = True

        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit"""
        if self._should_close_client and self._client:
            await self._client.aclose()
            self._client = None
            self._should_close_client = False

    async def make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        use_dynamic_model: bool = False,
    ) -> Dict[str, Any]:
        """
        Make an async API request

        Args:
            endpoint: API endpoint path
            params: Request parameters
            use_dynamic_model: Whether to create dynamic Pydantic models

        Returns:
            API response as dictionary
        """
        start_time = time.time()
        cache_hit = False

        # Build URL
        url = build_url(self.config.base_url, endpoint, params)

        # Check cache first
        if self.config.enable_caching:
            cached_response = self.cache.get(url, params)
            if cached_response is not None:
                cache_hit = True

                # Record metrics for cache hit
                if self.config.enable_metrics:
                    self.metrics.record_request(
                        endpoint=endpoint,
                        method="GET",
                        status_code=200,
                        response_time=time.time() - start_time,
                        cache_hit=True,
                    )

                # Apply dynamic model if requested
                if use_dynamic_model:
                    cached_response = create_dynamic_model(cached_response, endpoint)

                return cached_response

        # Apply rate limiting
        if self._rate_limiter:
            await self._rate_limiter.acquire()

        # Apply request middleware
        headers = self.headers.copy()
        url, headers, params = self.middleware.apply_request_middleware(
            url, headers, params or {}
        )

        # Make the request with retries
        for attempt in range(self.config.max_retries):
            try:
                if not self._client:
                    raise RuntimeError(
                        "AsyncCocApiCore not initialized. Use 'async with' context manager."
                    )

                response = await self._client.get(url, headers=headers)
                response_time = time.time() - start_time

                if is_successful_response(response.status_code):
                    # Parse JSON response
                    try:
                        json_response = response.json()
                    except Exception as e:
                        error_response = self._handle_json_error(e, attempt)
                        if self.config.enable_metrics:
                            self.metrics.record_request(
                                endpoint=endpoint,
                                method="GET",
                                status_code=response.status_code,
                                response_time=response_time,
                                cache_hit=False,
                                error_type="json",
                            )
                        return error_response

                    # Apply response middleware
                    json_response = self.middleware.apply_response_middleware(
                        json_response
                    )

                    # Cache successful response
                    if self.config.enable_caching:
                        self.cache.set(url, params, json_response)

                    # Record metrics
                    if self.config.enable_metrics:
                        self.metrics.record_request(
                            endpoint=endpoint,
                            method="GET",
                            status_code=response.status_code,
                            response_time=response_time,
                            cache_hit=cache_hit,
                        )

                    # Apply dynamic model if requested
                    if use_dynamic_model:
                        json_response = create_dynamic_model(json_response, endpoint)

                    return json_response

                else:
                    # Handle HTTP errors
                    error_response = self._handle_http_error(
                        response.status_code, attempt
                    )

                    if self.config.enable_metrics:
                        self.metrics.record_request(
                            endpoint=endpoint,
                            method="GET",
                            status_code=response.status_code,
                            response_time=response_time,
                            cache_hit=False,
                            error_type="http",
                        )

                    if (
                        not should_retry_error(response.status_code)
                        or attempt >= self.config.max_retries - 1
                    ):
                        return error_response

                    # Wait before retry
                    await asyncio.sleep(self.config.retry_delay * (2**attempt))

            except httpx.TimeoutException as e:
                error_response = self._handle_network_error(e, attempt)
                response_time = time.time() - start_time

                if self.config.enable_metrics:
                    self.metrics.record_request(
                        endpoint=endpoint,
                        method="GET",
                        status_code=0,
                        response_time=response_time,
                        cache_hit=False,
                        error_type="timeout",
                    )

                if attempt >= self.config.max_retries - 1:
                    return error_response

                await asyncio.sleep(self.config.retry_delay * (2**attempt))

            except Exception as e:
                error_response = self._handle_network_error(e, attempt)
                response_time = time.time() - start_time

                if self.config.enable_metrics:
                    self.metrics.record_request(
                        endpoint=endpoint,
                        method="GET",
                        status_code=0,
                        response_time=response_time,
                        cache_hit=False,
                        error_type="connection",
                    )

                if attempt >= self.config.max_retries - 1:
                    return error_response

                await asyncio.sleep(self.config.retry_delay * (2**attempt))

        # This should never be reached, but just in case
        return {
            "result": "error",
            "message": "Max retries exceeded",
            "error_type": "retry_exhausted",
        }

    def _handle_http_error(self, status: int, attempt: int) -> Dict[str, Any]:
        """Handle HTTP error responses"""
        error_messages = {
            400: "Bad request - check your parameters",
            403: "Forbidden - invalid API token or access denied",
            404: "Not found - check clan/player tag",
            429: "Rate limited - too many requests",
        }

        if status >= 500:
            error_messages[status] = "Server error - try again later"

        error_response = {
            "result": "error",
            "message": error_messages.get(status, f"HTTP error {status}"),
            "status_code": status,
            "error_type": "http",
        }

        # Determine if we should retry
        should_retry = (
            status in [429] or status >= 500
        ) and attempt < self.config.max_retries - 1
        if should_retry:
            error_response["should_retry"] = True

        return error_response

    def _handle_network_error(self, error: Exception, attempt: int) -> Dict[str, Any]:
        """Handle network-related errors"""
        error_type = (
            "timeout" if isinstance(error, httpx.TimeoutException) else "connection"
        )

        messages = {
            "timeout": f"Request timeout after {self.config.timeout} seconds",
            "connection": "Connection error - check your internet connection",
        }

        error_response: Dict[str, Any] = {
            "result": "error",
            "message": messages[error_type],
            "error_type": error_type,
        }

        # Allow retry for network errors
        if attempt < self.config.max_retries - 1:
            error_response["should_retry"] = True

        return error_response

    def _handle_json_error(self, error: Exception, attempt: int) -> Dict[str, Any]:
        """Handle JSON parsing errors"""
        return {
            "result": "error",
            "message": "Invalid JSON response from API",
            "error_type": "json",
        }

    async def test_connection(self) -> Dict[str, Any]:
        """Test API connection"""
        try:
            response = await self.make_request("/locations")
            if response.get("result") == "error":
                return response
            return {"result": "success", "message": "API connection successful"}
        except Exception as e:
            return {
                "result": "error",
                "message": f"Connection test failed: {str(e)}",
                "error_type": "connection",
            }
