"""
Main CocApi client - simplified and modular version
"""

import logging
import time
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple, Union
from warnings import warn

import httpx

from .api_methods import ApiMethods
from .async_client import AsyncCocApiCore
from .cache import CacheManager
from .config import ApiConfig
from .metrics import MetricsTracker
from .middleware import MiddlewareManager
from .models import create_dynamic_model
from .utils import (
    build_url,
    is_successful_response,
    should_retry_error,
    validate_params,
)


class CocApi(ApiMethods):
    """
    Clash of Clans API Wrapper with enhanced v3.0.0 features

    Provides both sync and async interfaces with caching, metrics, middleware,
    and dynamic model generation capabilities.
    """

    def __init__(
        self,
        token: str,
        timeout: int = 20,
        status_code: bool = False,
        config: Optional[ApiConfig] = None,
        async_mode: bool = False,
    ):
        """
        Initialize CocApi with enhanced features

        Args:
            token: API token from developer.clashofclans.com
            timeout: Request timeout in seconds (backward compatibility)
            status_code: Include status code in responses (backward compatibility)
            config: Optional ApiConfig for advanced settings
            async_mode: Enable async mode (default: False for backward compatibility)
        """
        self.token = token
        self.timeout = timeout
        self.status_code = status_code
        self.config = config or ApiConfig(timeout=timeout)
        self.async_mode = async_mode

        # Use config timeout if provided, otherwise use parameter
        if config is None:
            self.config.timeout = timeout

        self.ENDPOINT = self.config.base_url  # Backward compatibility
        self.headers = {
            "authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        # Initialize components
        self.cache = CacheManager(default_ttl=self.config.cache_ttl)
        self.cache.enable() if self.config.enable_caching else self.cache.disable()

        self.metrics = MetricsTracker(max_metrics=self.config.metrics_window_size)
        self.metrics.enable() if self.config.enable_metrics else self.metrics.disable()

        self.middleware = MiddlewareManager()

        # Async core for async operations
        self._async_core: Optional[AsyncCocApiCore] = None

        self.DEFAULT_PARAMS = ("limit", "after", "before")
        self.ERROR_INVALID_PARAM = {
            "result": "error",
            "message": "Invalid params for method",
        }

        # Only test sync mode immediately (async mode tests in context manager)
        if not async_mode:
            test_response = self.test()
            if test_response.get("result") == "error":
                raise ValueError(
                    f"API initialization failed: {test_response.get('message')}"
                )

    # Async Context Manager Support
    async def __aenter__(self) -> "CocApi":
        """Async context manager entry - enables async mode automatically"""
        if not self.async_mode:
            self.async_mode = True  # Auto-enable async mode in context

        self._async_core = AsyncCocApiCore(self.token, self.config)
        await self._async_core.__aenter__()

        # Test API connection in async mode
        test_response = await self._async_core.test_connection()
        if test_response.get("result") == "error":
            await self.__aexit__(None, None, None)
            raise ValueError(
                f"Async API initialization failed: {test_response.get('message')}"
            )

        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit"""
        if self._async_core:
            await self._async_core.__aexit__(exc_type, exc_val, exc_tb)
            self._async_core = None

    # Core API method - handles both sync and async
    def _api_response(
        self,
        uri: str,
        params: Optional[Dict[str, Any]] = None,
        use_dynamic_model: bool = False,
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Core API method that routes to sync or async implementation"""
        if self.async_mode:
            if not self._async_core:
                raise RuntimeError(
                    "Async mode enabled but not in async context. Use 'async with' statement."
                )
            return self._async_core.make_request(uri, params, use_dynamic_model)
        else:
            return self._sync_api_response(uri, params, use_dynamic_model)

    def _sync_api_response(
        self,
        uri: str,
        params: Optional[Dict[str, Any]] = None,
        use_dynamic_model: bool = False,
    ) -> Dict[str, Any]:
        """Synchronous API response handling"""
        start_time = time.time()
        cache_hit = False

        # Build URL
        url = build_url(self.config.base_url, uri, params)

        # Check cache first
        if self.config.enable_caching:
            cached_response = self.cache.get(url, params)
            if cached_response is not None:
                cache_hit = True

                # Record metrics for cache hit
                if self.config.enable_metrics:
                    self.metrics.record_request(
                        endpoint=uri,
                        method="GET",
                        status_code=200,
                        response_time=time.time() - start_time,
                        cache_hit=True,
                    )

                # Apply dynamic model if requested
                if use_dynamic_model:
                    cached_response = create_dynamic_model(cached_response, uri)

                # Add status code if requested (backward compatibility)
                if self.status_code:
                    cached_response["status_code"] = 200

                return cached_response

        # Apply request middleware
        headers = self.headers.copy()
        url, headers, request_params = self.middleware.apply_request_middleware(
            url, headers, params or {}
        )

        # Make the request with retries
        for attempt in range(self.config.max_retries):
            try:
                response = httpx.get(url, headers=headers, timeout=self.config.timeout)
                response_time = time.time() - start_time

                if is_successful_response(response.status_code):
                    # Parse JSON response
                    try:
                        json_response = response.json()
                    except Exception as e:
                        error_response = self._handle_json_error(e, attempt)
                        if self.config.enable_metrics:
                            self.metrics.record_request(
                                endpoint=uri,
                                method="GET",
                                status_code=response.status_code,
                                response_time=response_time,
                                cache_hit=False,
                                error_type="json",
                            )
                        return self._add_status_code(
                            error_response, response.status_code
                        )

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
                            endpoint=uri,
                            method="GET",
                            status_code=response.status_code,
                            response_time=response_time,
                            cache_hit=cache_hit,
                        )

                    # Apply dynamic model if requested
                    if use_dynamic_model:
                        json_response = create_dynamic_model(json_response, uri)

                    return self._add_status_code(json_response, response.status_code)

                else:
                    # Handle HTTP errors
                    error_response = self._handle_http_error(
                        response.status_code, attempt
                    )

                    if self.config.enable_metrics:
                        self.metrics.record_request(
                            endpoint=uri,
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
                        return self._add_status_code(
                            error_response, response.status_code
                        )

                    # Wait before retry
                    time.sleep(self.config.retry_delay * (2**attempt))

            except httpx.TimeoutException as e:
                error_response = self._handle_network_error(e, attempt)
                response_time = time.time() - start_time

                if self.config.enable_metrics:
                    self.metrics.record_request(
                        endpoint=uri,
                        method="GET",
                        status_code=0,
                        response_time=response_time,
                        cache_hit=False,
                        error_type="timeout",
                    )

                if attempt >= self.config.max_retries - 1:
                    return self._add_status_code(error_response, 0)

                time.sleep(self.config.retry_delay * (2**attempt))

            except Exception as e:
                error_response = self._handle_network_error(e, attempt)
                response_time = time.time() - start_time

                if self.config.enable_metrics:
                    self.metrics.record_request(
                        endpoint=uri,
                        method="GET",
                        status_code=0,
                        response_time=response_time,
                        cache_hit=False,
                        error_type="connection",
                    )

                if attempt >= self.config.max_retries - 1:
                    return self._add_status_code(error_response, 0)

                time.sleep(self.config.retry_delay * (2**attempt))

        # This should never be reached
        return self._add_status_code(
            {
                "result": "error",
                "message": "Max retries exceeded",
                "error_type": "retry_exhausted",
            },
            0,
        )

    def _add_status_code(
        self, response: Dict[str, Any], status_code: int
    ) -> Dict[str, Any]:
        """Add status code to response if requested (backward compatibility)"""
        if self.status_code:
            response["status_code"] = status_code
        return response

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
            "error_type": "http",
        }

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

        return error_response

    def _handle_json_error(self, error: Exception, attempt: int) -> Dict[str, Any]:
        """Handle JSON parsing errors"""
        return {
            "result": "error",
            "message": "Invalid JSON response from API",
            "error_type": "json",
        }

    def _validate_params(self, params: Optional[Dict[str, Any]]) -> bool:
        """Validate request parameters"""
        return validate_params(params, self.DEFAULT_PARAMS)

    # Test method
    def test(self) -> Dict[str, Any]:
        """Test API connection"""
        try:
            response = self._sync_api_response("/locations")
            if response.get("result") == "error":
                return response
            return {"result": "success", "message": "API connection successful"}
        except Exception as e:
            return {
                "result": "error",
                "message": f"Connection test failed: {str(e)}",
                "error_type": "connection",
            }

    # V3.0.0 Enhanced Features
    def custom_endpoint(
        self,
        endpoint_path: str,
        params: Optional[Dict[str, Any]] = None,
        use_dynamic_model: bool = False,
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Call a custom API endpoint (future-proofing for new SuperCell endpoints)

        Args:
            endpoint_path: The endpoint path (e.g., "/clans/new-feature")
            params: Optional query parameters
            use_dynamic_model: Whether to generate dynamic Pydantic models

        Returns:
            API response as dict or Pydantic model
        """
        if not endpoint_path.startswith("/"):
            endpoint_path = "/" + endpoint_path

        return self._api_response(endpoint_path, params, use_dynamic_model)

    def set_base_url(self, new_base_url: str, force: bool = False) -> None:
        """
        Change the base API URL with safety warnings

        Args:
            new_base_url: New base URL to use
            force: Skip safety warnings (use with caution)
        """
        official_url = "https://api.clashofclans.com/v1"

        if new_base_url != official_url and not force:
            warn(
                f"⚠️  WARNING: Changing base URL from official endpoint!\n"
                f"   Official: {official_url}\n"
                f"   New URL:  {new_base_url}\n"
                f"   This may result in API failures or unexpected behavior.\n"
                f"   Use force=True to suppress this warning.",
                UserWarning,
                stacklevel=2,
            )

        original_url = self.config.base_url
        self.config.base_url = new_base_url
        self.ENDPOINT = new_base_url  # Update backward compatibility field

        logging.info(f"Base URL changed from {original_url} to {new_base_url}")

    def get_base_url(self) -> str:
        """Get current base URL"""
        return self.config.base_url

    def reset_base_url(self) -> None:
        """Reset to official SuperCell API URL"""
        official_url = "https://api.clashofclans.com/v1"
        original_url = self.config.base_url

        self.config.base_url = official_url
        self.ENDPOINT = official_url

        if original_url != official_url:
            warn(
                f"Base URL reset to official SuperCell endpoint: {official_url}",
                UserWarning,
                stacklevel=2,
            )
            logging.info(f"Base URL reset from {original_url} to {official_url}")
        else:
            logging.info("Base URL is already set to the official endpoint")

    # Middleware methods
    def add_request_middleware(
        self,
        middleware: Callable[
            [str, Dict[str, str], Dict[str, Any]],
            Tuple[str, Dict[str, str], Dict[str, Any]],
        ],
    ) -> None:
        """Add request middleware - delegates to middleware manager"""
        self.middleware.add_request_middleware(middleware)

    def add_response_middleware(
        self, middleware: Callable[[Dict[str, Any]], Dict[str, Any]]
    ) -> None:
        """Add response middleware - delegates to middleware manager"""
        self.middleware.add_response_middleware(middleware)

    # Metrics methods
    def get_metrics(self) -> Dict[str, Any]:
        """Get API metrics summary"""
        return self.metrics.get_metrics_summary()

    def clear_metrics(self) -> None:
        """Clear stored metrics"""
        self.metrics.clear_metrics()

    # Cache methods
    def clear_cache(self) -> int:
        """Clear API response cache"""
        return self.cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.cache.get_stats()

    # Continue with all the existing API methods...
    # For brevity, I'll include the key ones and the pattern

    # All API endpoint methods are inherited from ApiMethods mixin
