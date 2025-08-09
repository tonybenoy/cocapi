"""
Middleware system for cocapi request/response processing
"""

import logging
from typing import Any, Callable, Dict, List, Tuple


class MiddlewareManager:
    """Manages request and response middleware"""

    def __init__(self) -> None:
        self.request_middleware: List[
            Callable[
                [str, Dict[str, str], Dict[str, Any]],
                Tuple[str, Dict[str, str], Dict[str, Any]],
            ]
        ] = []
        self.response_middleware: List[Callable[[Dict[str, Any]], Dict[str, Any]]] = []

    def add_request_middleware(
        self,
        middleware: Callable[
            [str, Dict[str, str], Dict[str, Any]],
            Tuple[str, Dict[str, str], Dict[str, Any]],
        ],
    ) -> None:
        """
        Add middleware function to process requests before they're sent.

        Args:
            middleware: Function that takes (url, headers, params) and returns modified versions

        Examples:
            def add_custom_header(url, headers, params):
                headers = headers.copy()
                headers['X-Custom'] = 'MyApp'
                return url, headers, params

            manager.add_request_middleware(add_custom_header)
        """
        self.request_middleware.append(middleware)

    def add_response_middleware(
        self, middleware: Callable[[Dict[str, Any]], Dict[str, Any]]
    ) -> None:
        """
        Add middleware function to process responses after they're received.

        Args:
            middleware: Function that takes response dict and returns modified version

        Examples:
            def add_timestamp(response):
                response['_processed_at'] = time.time()
                return response

            manager.add_response_middleware(add_timestamp)
        """
        self.response_middleware.append(middleware)

    def apply_request_middleware(
        self, url: str, headers: Dict[str, str], params: Dict[str, Any]
    ) -> Tuple[str, Dict[str, str], Dict[str, Any]]:
        """Apply all request middleware in order"""
        for middleware in self.request_middleware:
            try:
                url, headers, params = middleware(url, headers, params)
            except Exception as e:
                logging.warning(f"Request middleware failed: {e}")
        return url, headers, params

    def apply_response_middleware(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Apply all response middleware in order"""
        for middleware in self.response_middleware:
            try:
                response = middleware(response)
            except Exception as e:
                logging.warning(f"Response middleware failed: {e}")
        return response

    def clear_request_middleware(self) -> None:
        """Clear all request middleware"""
        self.request_middleware.clear()

    def clear_response_middleware(self) -> None:
        """Clear all response middleware"""
        self.response_middleware.clear()

    def clear_all_middleware(self) -> None:
        """Clear all middleware"""
        self.clear_request_middleware()
        self.clear_response_middleware()

    def get_middleware_info(self) -> Dict[str, Any]:
        """Get information about registered middleware"""
        return {
            "request_middleware_count": len(self.request_middleware),
            "response_middleware_count": len(self.response_middleware),
            "request_middleware_names": [
                getattr(mw, "__name__", "anonymous") for mw in self.request_middleware
            ],
            "response_middleware_names": [
                getattr(mw, "__name__", "anonymous") for mw in self.response_middleware
            ],
        }


# Common middleware functions that users can import and use
def add_user_agent_middleware(
    user_agent: str,
) -> Callable[
    [str, Dict[str, str], Dict[str, Any]], Tuple[str, Dict[str, str], Dict[str, Any]]
]:
    """Create middleware that adds custom User-Agent header"""

    def middleware(
        url: str, headers: Dict[str, str], params: Dict[str, Any]
    ) -> Tuple[str, Dict[str, str], Dict[str, Any]]:
        headers = headers.copy()
        headers["User-Agent"] = user_agent
        return url, headers, params

    middleware.__name__ = f"user_agent_{user_agent.replace(' ', '_')}"
    return middleware


def add_request_id_middleware() -> Callable[
    [str, Dict[str, str], Dict[str, Any]], Tuple[str, Dict[str, str], Dict[str, Any]]
]:
    """Create middleware that adds unique request ID to headers"""
    import uuid

    def middleware(
        url: str, headers: Dict[str, str], params: Dict[str, Any]
    ) -> Tuple[str, Dict[str, str], Dict[str, Any]]:
        headers = headers.copy()
        headers["X-Request-ID"] = str(uuid.uuid4())
        return url, headers, params

    middleware.__name__ = "request_id"
    return middleware


def add_debug_logging_middleware() -> Callable[
    [str, Dict[str, str], Dict[str, Any]], Tuple[str, Dict[str, str], Dict[str, Any]]
]:
    """Create middleware that logs request details"""

    def middleware(
        url: str, headers: Dict[str, str], params: Dict[str, Any]
    ) -> Tuple[str, Dict[str, str], Dict[str, Any]]:
        logging.debug(f"API Request: {url}")
        logging.debug(f"Headers: {headers}")
        logging.debug(f"Params: {params}")
        return url, headers, params

    middleware.__name__ = "debug_logging"
    return middleware


def add_response_timestamp_middleware() -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """Create middleware that adds processing timestamp to response"""
    import time

    def middleware(response: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(response, dict):
            response = response.copy()
            response["_processed_at"] = time.time()
        return response

    middleware.__name__ = "response_timestamp"
    return middleware


def add_response_size_middleware() -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """Create middleware that adds response size information"""
    import json

    def middleware(response: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(response, dict):
            response = response.copy()
            try:
                response_json = json.dumps(response)
                response["_response_size_bytes"] = len(response_json.encode("utf-8"))
            except Exception:
                # If serialization fails, estimate size
                response["_response_size_bytes"] = len(str(response))
        return response

    middleware.__name__ = "response_size"
    return middleware
