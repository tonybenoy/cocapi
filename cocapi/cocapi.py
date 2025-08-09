import asyncio
import logging
import time
import urllib.parse
from typing import Any, Awaitable, Dict, Optional, Tuple, Union
from warnings import warn

import httpx

from .config import ApiConfig, CacheEntry


class CocApi:
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

        # Cache for responses
        self._cache: Dict[str, CacheEntry] = {}

        # Async-specific attributes
        self._client: Optional[httpx.AsyncClient] = None
        self._should_close_client = False
        self._rate_limiter = None
        if async_mode and self.config.enable_rate_limiting:
            self._rate_limiter = AsyncRateLimiter(
                rate=self.config.requests_per_second, burst=self.config.burst_limit
            )

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

    async def __aenter__(self) -> "CocApi":
        """Async context manager entry - enables async mode automatically"""
        if not self.async_mode:
            self.async_mode = True  # Auto-enable async mode in context

        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.config.timeout)
            self._should_close_client = True

            # Initialize rate limiter if needed
            if self.config.enable_rate_limiting and self._rate_limiter is None:
                self._rate_limiter = AsyncRateLimiter(
                    rate=self.config.requests_per_second, burst=self.config.burst_limit
                )

            # Test API connection in async mode
            test_response = await self._async_test()
            if test_response.get("result") == "error":
                await self.__aexit__(None, None, None)
                raise ValueError(
                    f"API initialization failed: {test_response.get('message')}"
                )

        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit"""
        if self._should_close_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    def __check_if_dict_invalid(self, params: Dict, valid_items: Tuple = ()) -> bool:
        valid_items = self.DEFAULT_PARAMS if not valid_items else valid_items
        return set(params.keys()).issubset(valid_items)

    def _get_cache_key(self, uri: str, params: Dict[str, Any]) -> str:
        """Generate cache key from URI and parameters"""
        param_str = urllib.parse.urlencode(sorted(params.items()))
        return f"{uri}?{param_str}" if param_str else uri

    def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if available and not expired"""
        if not self.config.enable_caching:
            return None

        entry = self._cache.get(cache_key)
        if entry and not entry.is_expired(time.time()):
            logging.debug(f"Cache hit for {cache_key}")
            return entry.data

        # Remove expired entry
        if entry:
            del self._cache[cache_key]

        return None

    def _cache_response(self, cache_key: str, response: Dict[str, Any]) -> None:
        """Cache response with TTL"""
        if not self.config.enable_caching:
            return

        # Don't cache errors
        if response.get("result") == "error":
            return

        self._cache[cache_key] = CacheEntry(
            data=response.copy(), timestamp=time.time(), ttl=self.config.cache_ttl
        )
        logging.debug(f"Cached response for {cache_key}")

    def clear_cache(self) -> None:
        """Clear all cached responses"""
        self._cache.clear()
        logging.info("Cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        current_time = time.time()
        total_entries = len(self._cache)
        expired_entries = sum(
            1 for entry in self._cache.values() if entry.is_expired(current_time)
        )

        return {
            "total_entries": total_entries,
            "active_entries": total_entries - expired_entries,
            "expired_entries": expired_entries,
            "cache_enabled": self.config.enable_caching,
        }

    def _process_response_with_pydantic(
        self, response: Dict[str, Any], endpoint_type: str
    ) -> Union[Dict[str, Any], Any]:
        """
        Process API response with optional Pydantic model validation.

        Args:
            response: Raw API response dictionary
            endpoint_type: Type of endpoint (clan, player, etc.) to determine model

        Returns:
            Either the original dict or a Pydantic model instance
        """
        if not self.config.use_pydantic_models:
            return response

        # Return error responses as-is
        if response.get("result") == "error":
            return response

        try:
            # Lazy import to avoid dependency when not using models
            from .models import (
                Clan,
                ClanSearchResult,
                LocationRankingList,
                Player,
            )

            # Map endpoint types to models
            model_mapping = {
                "clan": Clan,
                "player": Player,
                "clan_search": ClanSearchResult,
                "location_ranking": LocationRankingList,
            }

            model_class = model_mapping.get(endpoint_type)
            if model_class:
                return model_class(**response)

            # If no specific model, return dict
            return response

        except ImportError:
            # Pydantic not installed, return dict
            return response
        except Exception as e:
            # Model validation failed, log warning and return dict
            logging.warning(f"Pydantic model validation failed: {e}")
            return response

    def _infer_endpoint_type(self, uri: str) -> str:
        """
        Infer the endpoint type from URI for Pydantic model selection.

        Args:
            uri: API endpoint URI

        Returns:
            Endpoint type string
        """
        if "/clans/" in uri and "/members" not in uri and "/warlog" not in uri:
            return "clan"
        elif "/players/" in uri:
            return "player"
        elif "/clans" in uri and "?" in uri:  # Clan search with params
            return "clan_search"
        elif "/locations/" in uri and "/rankings/" in uri:
            return "location_ranking"
        else:
            return "generic"

    def __api_response(
        self,
        uri: str,
        params: Optional[Dict[str, Any]] = None,
        status_code: bool = False,
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Unified API response handler - returns sync or async based on mode
        """
        if self.async_mode:
            return self.__async_api_response(uri, params, status_code)
        else:
            return self.__sync_api_response(uri, params, status_code)

    def __sync_api_response(
        self,
        uri: str,
        params: Optional[Dict[str, Any]] = None,
        status_code: bool = False,
    ) -> Dict[str, Any]:
        """
        Synchronous API response handler with caching and retry logic
        """
        params = params or {}
        cache_key = self._get_cache_key(uri, params)

        # Check cache first
        cached = self._get_cached_response(cache_key)
        if cached is not None:
            if status_code or self.status_code:
                cached["status_code"] = 200  # Assume 200 for cached responses
            # Process cached response with Pydantic if enabled
            endpoint_type = self._infer_endpoint_type(uri)
            return self._process_response_with_pydantic(cached, endpoint_type)

        # Build URL
        if params:
            url = f"{self.ENDPOINT}{uri}?{urllib.parse.urlencode(params)}"
        else:
            url = f"{self.ENDPOINT}{uri}"

        # Make request with retries
        for attempt in range(self.config.max_retries):
            try:
                response = httpx.get(
                    url=url, headers=self.headers, timeout=self.config.timeout
                )

                # Handle HTTP errors
                if response.status_code == 400:
                    return {
                        "result": "error",
                        "message": "Bad request - check your parameters",
                        "status_code": response.status_code,
                    }
                elif response.status_code == 403:
                    return {
                        "result": "error",
                        "message": "Forbidden - check your API token",
                        "status_code": response.status_code,
                    }
                elif response.status_code == 404:
                    return {
                        "result": "error",
                        "message": "Not found - check clan/player tag",
                        "status_code": response.status_code,
                    }
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    if attempt < self.config.max_retries - 1:
                        wait_time = self.config.retry_delay * (2**attempt)
                        logging.warning(
                            f"Rate limited, waiting {wait_time}s before retry"
                        )
                        time.sleep(wait_time)
                        continue
                    return {
                        "result": "error",
                        "message": "Rate limited - too many requests",
                        "status_code": response.status_code,
                    }
                elif response.status_code >= 500:
                    # Server error - retry
                    if attempt < self.config.max_retries - 1:
                        wait_time = self.config.retry_delay * (2**attempt)
                        logging.warning(f"Server error, retrying in {wait_time}s")
                        time.sleep(wait_time)
                        continue
                    return {
                        "result": "error",
                        "message": "Server error - try again later",
                        "status_code": response.status_code,
                    }

                response.raise_for_status()
                response_json = response.json()

                # Add status code if requested
                if status_code or self.status_code:
                    response_json["status_code"] = response.status_code

                # Cache successful response
                self._cache_response(cache_key, response_json)

                # Process with Pydantic if enabled
                endpoint_type = self._infer_endpoint_type(uri)
                return self._process_response_with_pydantic(
                    response_json, endpoint_type
                )

            except httpx.TimeoutException:
                if attempt < self.config.max_retries - 1:
                    wait_time = self.config.retry_delay * (2**attempt)
                    logging.warning(f"Timeout, retrying in {wait_time}s")
                    time.sleep(wait_time)
                    continue
                return {
                    "result": "error",
                    "message": f"Request timeout after {self.config.timeout} seconds",
                    "error_type": "timeout",
                }
            except httpx.ConnectError:
                if attempt < self.config.max_retries - 1:
                    wait_time = self.config.retry_delay * (2**attempt)
                    logging.warning(f"Connection error, retrying in {wait_time}s")
                    time.sleep(wait_time)
                    continue
                return {
                    "result": "error",
                    "message": "Connection error - check your internet connection",
                    "error_type": "connection",
                }
            except httpx.HTTPStatusError as e:
                return {
                    "result": "error",
                    "message": f"HTTP error: {e.response.status_code}",
                    "status_code": e.response.status_code,
                    "error_type": "http",
                }
            except ValueError as e:
                return {
                    "result": "error",
                    "message": "Invalid JSON response from API",
                    "error_type": "json",
                    "exception": str(e),
                }
            except Exception as e:
                logging.error(f"Unexpected error in API request: {e}")
                if attempt < self.config.max_retries - 1:
                    wait_time = self.config.retry_delay * (2**attempt)
                    time.sleep(wait_time)
                    continue
                return {
                    "result": "error",
                    "message": "Unexpected error occurred",
                    "error_type": "unknown",
                    "exception": str(e),
                }

        # Should not reach here, but just in case
        return {
            "result": "error",
            "message": "Max retries exceeded",
            "error_type": "retry_exhausted",
        }

    async def __async_api_response(
        self,
        uri: str,
        params: Optional[Dict[str, Any]] = None,
        status_code: bool = False,
    ) -> Dict[str, Any]:
        """
        Asynchronous API response handler with caching and rate limiting
        """
        if self._client is None:
            raise RuntimeError(
                "Client not initialized. Use 'async with CocApi(...)' pattern"
            )

        params = params or {}
        cache_key = self._get_cache_key(uri, params)

        # Check cache first
        cached = self._get_cached_response(cache_key)
        if cached is not None:
            if status_code or self.status_code:
                cached["status_code"] = 200  # Assume 200 for cached responses
            # Process cached response with Pydantic if enabled
            endpoint_type = self._infer_endpoint_type(uri)
            return self._process_response_with_pydantic(cached, endpoint_type)

        # Rate limiting
        if self._rate_limiter:
            await self._rate_limiter.acquire()

        # Build URL
        if params:
            url = f"{self.config.base_url}{uri}?{urllib.parse.urlencode(params)}"
        else:
            url = f"{self.config.base_url}{uri}"

        # Make request with retries
        for attempt in range(self.config.max_retries):
            try:
                response = await self._client.get(url=url, headers=self.headers)

                # Handle HTTP errors (same logic as sync version)
                if response.status_code == 400:
                    return {
                        "result": "error",
                        "message": "Bad request - check your parameters",
                        "status_code": response.status_code,
                    }
                elif response.status_code == 403:
                    return {
                        "result": "error",
                        "message": "Forbidden - check your API token",
                        "status_code": response.status_code,
                    }
                elif response.status_code == 404:
                    return {
                        "result": "error",
                        "message": "Not found - check clan/player tag",
                        "status_code": response.status_code,
                    }
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    if attempt < self.config.max_retries - 1:
                        wait_time = self.config.retry_delay * (2**attempt)
                        logging.warning(
                            f"Rate limited, waiting {wait_time}s before retry"
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    return {
                        "result": "error",
                        "message": "Rate limited - too many requests",
                        "status_code": response.status_code,
                    }
                elif response.status_code >= 500:
                    # Server error - retry
                    if attempt < self.config.max_retries - 1:
                        wait_time = self.config.retry_delay * (2**attempt)
                        logging.warning(f"Server error, retrying in {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                    return {
                        "result": "error",
                        "message": "Server error - try again later",
                        "status_code": response.status_code,
                    }

                response.raise_for_status()
                response_json = response.json()

                # Add status code if requested
                if status_code or self.status_code:
                    response_json["status_code"] = response.status_code

                # Cache successful response
                self._cache_response(cache_key, response_json)

                # Process with Pydantic if enabled
                endpoint_type = self._infer_endpoint_type(uri)
                return self._process_response_with_pydantic(
                    response_json, endpoint_type
                )

            except httpx.TimeoutException:
                if attempt < self.config.max_retries - 1:
                    wait_time = self.config.retry_delay * (2**attempt)
                    logging.warning(f"Timeout, retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                return {
                    "result": "error",
                    "message": f"Request timeout after {self.timeout} seconds",
                    "error_type": "timeout",
                }
            except httpx.ConnectError:
                if attempt < self.config.max_retries - 1:
                    wait_time = self.config.retry_delay * (2**attempt)
                    logging.warning(f"Connection error, retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                return {
                    "result": "error",
                    "message": "Connection error - check your internet connection",
                    "error_type": "connection",
                }
            except httpx.HTTPStatusError as e:
                return {
                    "result": "error",
                    "message": f"HTTP error: {e.response.status_code}",
                    "status_code": e.response.status_code,
                    "error_type": "http",
                }
            except ValueError as e:
                return {
                    "result": "error",
                    "message": "Invalid JSON response from API",
                    "error_type": "json",
                    "exception": str(e),
                }
            except Exception as e:
                logging.error(f"Unexpected error in API request: {e}")
                if attempt < self.config.max_retries - 1:
                    wait_time = self.config.retry_delay * (2**attempt)
                    await asyncio.sleep(wait_time)
                    continue
                return {
                    "result": "error",
                    "message": "Unexpected error occurred",
                    "error_type": "unknown",
                    "exception": str(e),
                }

        # Should not reach here, but just in case
        return {
            "result": "error",
            "message": "Max retries exceeded",
            "error_type": "retry_exhausted",
        }

    def test(self) -> Dict[str, Any]:
        """
        Function to test if the api is up and running (sync version)
        """
        if self.async_mode and self._client is not None:
            # Already in async mode, don't use sync httpx
            raise RuntimeError("Use async context manager for testing in async mode")

        response = httpx.get(url=self.ENDPOINT, headers=self.headers)
        if response.status_code == 200:
            return {"result": "success", "message": "Api is up and running!"}
        elif response.status_code == 403:
            return {
                "result": "error",
                "message": "Invalid token",
            }
        else:
            response_json = {
                "result": "error",
                "message": "Api is Down!",
            }
            if self.status_code:
                response_json.update({"status_code": response.status_code})
            return response_json

    async def _async_test(self) -> Dict[str, Any]:
        """Test if the API is up and running (async version)"""
        if self._client is None:
            # For initialization test, create temporary client
            async with httpx.AsyncClient(timeout=self.timeout) as temp_client:
                try:
                    response = await temp_client.get(
                        url=self.config.base_url, headers=self.headers
                    )
                    if response.status_code == 200:
                        return {
                            "result": "success",
                            "message": "Api is up and running!",
                        }
                    elif response.status_code == 403:
                        return {"result": "error", "message": "Invalid token"}
                    else:
                        return {"result": "error", "message": "Api is Down!"}
                except Exception as e:
                    return {"result": "error", "message": f"Connection failed: {e}"}
        else:
            # Use existing client
            try:
                response = await self._client.get(
                    url=self.config.base_url, headers=self.headers
                )
                if response.status_code == 200:
                    return {"result": "success", "message": "Api is up and running!"}
                elif response.status_code == 403:
                    return {"result": "error", "message": "Invalid token"}
                else:
                    return {"result": "error", "message": "Api is Down!"}
            except Exception as e:
                return {"result": "error", "message": f"Connection failed: {e}"}

    # All API methods now automatically work in sync or async mode
    def clan_leaguegroup(
        self, tag: str
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Retrieve information about clan's current clan war league group
        """
        return self.__api_response(uri=f"/clans/%23{tag[1:]}/currentwar/leaguegroup")

    def warleague(self, sid: str) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Retrieve information about a clan war league war.
        """
        return self.__api_response(uri=f"/clanwarleagues/wars/{str(sid)}")

    def clan_war_log(
        self, tag: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Retrieve clan's clan war log
        """
        params = params or {}
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(uri=f"/clans/%23{tag[1:]}/warlog", params=params)

    def clan(
        self, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Search all clans by name and/or filtering the results using
        various criteria.At least one filtering criteria must be defined and if
        name is used as part of search, it is required to be at least three
        characters long.It is not possible to specify ordering for results so
        clients should not rely on any specific ordering as that may change
        in the future releases of the API.
        """
        params = params or {}
        valid_items = tuple(
            [
                "name",
                "warFrequency",
                "locationId",
                "minMembers",
                "maxMembers",
                "minClanPoints",
                "minClanLevel",
                "labelIds",
            ]
            + list(self.DEFAULT_PARAMS)
        )
        if not self.__check_if_dict_invalid(params=params, valid_items=valid_items):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(uri="/clans", params=params)

    def clan_current_war(
        self, tag: str
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Retrieve information about clan's current clan war
        """
        return self.__api_response(uri=f"/clans/%23{tag[1:]}/currentwar")

    def clan_tag(self, tag: str) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Get information about a single clan by clan tag.
        Clan tags can be found using clan search operation.
        """
        return self.__api_response(uri=f"/clans/%23{tag[1:]}")

    def clan_members(
        self, tag: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to List clan members
        """
        params = params or {}
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(uri=f"/clans/%23{tag[1:]}/members", params=params)

    def clan_capitalraidseasons(
        self, tag: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Retrieve clan's capital raid seasons
        """
        params = params or {}
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(
            uri=f"/clans/%23{tag[1:]}/capitalraidseasons", params=params
        )

    def players(self, tag: str) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Get information about a single player by player tag.
        Player tags can be found either in game or by from clan member lists.
        """
        return self.__api_response(uri=f"/players/%23{tag[1:]}")

    def location_id_clan_rank(
        self, id: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Get clan rankings for a specific location
        """
        params = params or {}
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(
            uri=f"/locations/{str(id)}/rankings/clans", params=params
        )

    def location_id_player_rank(
        self, id: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Get player rankings for a specific location
        """
        params = params or {}
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(
            uri=f"/locations/{str(id)}/rankings/players", params=params
        )

    def location_clan_versus(
        self, id: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Get clan versus rankings for a specific location
        """
        warn(
            "This end will be deprecated in the future.",
            DeprecationWarning,
            stacklevel=2,
        )
        params = params or {}
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM

        return self.__api_response(
            uri=f"/locations/{str(id)}/rankings/clans-versus", params=params
        )

    def location_players_builder_base(
        self, id: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Get player builder base rankings for a specific location
        """

        params = params or {}
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM

        return self.__api_response(
            uri=f"/locations/{str(id)}/rankings/players-builder-base", params=params
        )

    def location_clans_builder_base(
        self, id: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Get clan builder base rankings for a specific location
        """

        params = params or {}
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM

        return self.__api_response(
            uri=f"/locations/{str(id)}/rankings/clans-builder-base", params=params
        )

    def location_player_versus(
        self, id: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Get player versus rankings for a specific location
        """
        warn(
            "This end will be deprecated in the future.",
            DeprecationWarning,
            stacklevel=2,
        )
        params = params or {}
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(
            uri=f"/locations/{str(id)}/rankings/players-versus", params=params
        )

    def location(
        self, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function List all available locations
        Will be depricated in the future in favour of locations

        """
        warn(
            "This method will be \
            deprecated in the future in favour\
            of locations to maintain parity with original api",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.locations(params=params)

    def locations(
        self, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to List all available locations
        """
        params = params or {}
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(uri="/locations", params=params)

    def location_rankings_capitals(
        self, id: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Get capital rankings for a specific location
        """
        params = params or {}
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(
            uri=f"/locations/{str(id)}/rankings/capitals", params=params
        )

    def location_id(self, id: str) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Get information about specific location
        """
        return self.__api_response(uri=f"/locations/{str(id)}")

    def league(
        self, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Get list of leagues
        """
        params = params or {}
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(uri="/leagues", params=params)

    def league_id(self, id: str) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Get league information
        """
        return self.__api_response(uri=f"/leagues/{str(id)}")

    def league_season(
        self, id: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Get league seasons.
        Note that league season information is available only for Legend League.
        """
        params = params or {}
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(uri=f"/leagues/{str(id)}/seasons", params=params)

    def league_season_id(
        self, id: str, sid: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Get league season rankings.
        Note that league season information is available only for Legend League.
        """
        params = params or {}
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(
            uri=f"/leagues/{str(id)}/seasons/{str(sid)}", params=params
        )

    def warleagues(self) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Get list of clan war leagues
        """
        return self.__api_response(
            uri="/warleagues",
        )

    def warleagues_id(
        self, league_id: str
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Get information about a clan war league
        """
        return self.__api_response(
            uri=f"/warleagues/{str(league_id)}",
        )

    def labels_clans(
        self, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Get labels for a clan
        """
        params = params or {}
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(uri="/labels/clans", params=params)

    def labels_players(
        self, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Get labels for a player
        """
        params = params or {}
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(uri="/labels/players/", params=params)

    def capitalleagues(
        self, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Get list of capital leagues
        """
        params = params or {}
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(uri="/capitalleagues", params=params)

    def capitalleagues_id(
        self, league_id: str
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Get information about a capital league
        """
        return self.__api_response(uri=f"/capitalleagues/{str(league_id)}")

    def builderbaseleagues(
        self, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Get list of builder base leagues
        """
        params = params or {}
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(uri="/builderbaseleagues", params=params)

    def builderbaseleagues_id(
        self, league_id: str
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Get information about a builder base league
        """
        return self.__api_response(uri=f"/builderbaseleagues/{str(league_id)}")

    def goldpass_seasons_current(
        self,
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Get current gold pass season
        """
        return self.__api_response(uri="/goldpass/seasons/current")

    def player_verifytoken(
        self, token: str, player_tag: str
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """
        Function to Verify player token
        """
        if self.async_mode:
            return self._async_player_verifytoken(token, player_tag)
        else:
            return self._sync_player_verifytoken(token, player_tag)

    def _sync_player_verifytoken(self, token: str, player_tag: str) -> Dict[str, Any]:
        """Sync version of player token verification"""
        try:
            response = httpx.post(
                url=f"{self.ENDPOINT}/players/%23{player_tag[1:]}/verifytoken",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
                data={"token": token},
            )
            response_json = dict(response.json())

            if self.status_code:
                response_json = dict(response_json, status_code=response.status_code)
            return response_json
        except Exception as e:
            return {
                "status": "error",
                "message": "Something broke",
                "exception": str(e),
            }

    async def _async_player_verifytoken(
        self, token: str, player_tag: str
    ) -> Dict[str, Any]:
        """Async version of player token verification"""
        if self._client is None:
            raise RuntimeError(
                "Client not initialized. Use 'async with CocApi(...)' pattern"
            )

        try:
            response = await self._client.post(
                url=f"{self.config.base_url}/players/%23{player_tag[1:]}/verifytoken",
                headers=self.headers,
                json={"token": token},
            )
            response_json = response.json()
            if self.status_code:
                response_json["status_code"] = response.status_code
            return response_json
        except Exception as e:
            return {
                "result": "error",
                "message": "Token verification failed",
                "error_type": "verification",
                "exception": str(e),
            }


class AsyncRateLimiter:
    """
    Token bucket rate limiter for async operations
    """

    def __init__(self, rate: float, burst: int):
        """
        Args:
            rate: Requests per second
            burst: Maximum burst size
        """
        self.rate = rate
        self.burst = burst
        self.tokens = float(burst)
        self.last_update = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire a token, waiting if necessary"""
        async with self._lock:
            now = time.time()

            # Add tokens based on elapsed time
            elapsed = now - self.last_update
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last_update = now

            # Wait if no tokens available
            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1
