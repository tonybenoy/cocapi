"""
Error classification and optional typed exceptions.

API calls never raise by default; they return an error dict. Responses now
also carry an ``error_kind`` key (alongside the legacy ``error_type``) and, when
the API supplied one, ``reason``. Use :func:`raise_for_error` to convert an
error dict into a typed exception.
"""

from typing import Any

# error_kind values
MAINTENANCE = "maintenance"
NOT_FOUND = "not_found"
RATE_LIMITED = "rate_limited"
BAD_REQUEST = "bad_request"
INVALID_IP = "invalid_ip"
ACCESS_DENIED = "access_denied"
PRIVATE_WAR_LOG = "private_war_log"
SERVER_ERROR = "server_error"
HTTP_ERROR = "http_error"


def classify_http_error(
    status: int, body: Any = None, endpoint: str | None = None
) -> tuple[str, str | None]:
    """Return ``(error_kind, reason)`` for an HTTP error response."""
    reason = body.get("reason") if isinstance(body, dict) else None
    reason = reason if isinstance(reason, str) else None

    if status == 503 or reason == "inMaintenance":
        return MAINTENANCE, reason
    if status == 404:
        return NOT_FOUND, reason
    if status == 429:
        return RATE_LIMITED, reason
    if status == 400:
        return BAD_REQUEST, reason
    if status == 403:
        if reason == "accessDenied.invalidIp":
            return INVALID_IP, reason
        # A 403 on war endpoints with a valid key means the war log is private.
        if endpoint and ("/currentwar" in endpoint or "/warlog" in endpoint):
            if reason in (None, "accessDenied"):
                return PRIVATE_WAR_LOG, reason
        return ACCESS_DENIED, reason
    if status >= 500:
        return SERVER_ERROR, reason
    return HTTP_ERROR, reason


class CocApiError(Exception):
    """Base class for typed API errors."""

    def __init__(self, response: dict[str, Any]):
        self.response = response
        self.status_code = response.get("status_code") or response.get("http_status")
        self.kind = response.get("error_kind")
        self.reason = response.get("reason")
        super().__init__(response.get("message", "API error"))


class MaintenanceError(CocApiError): ...


class NotFoundError(CocApiError): ...


class RateLimitedError(CocApiError): ...


class BadRequestError(CocApiError): ...


class AccessDeniedError(CocApiError): ...


class PrivateWarLogError(AccessDeniedError): ...


class ServerError(CocApiError): ...


_KIND_TO_EXC: dict[str, type[CocApiError]] = {
    MAINTENANCE: MaintenanceError,
    NOT_FOUND: NotFoundError,
    RATE_LIMITED: RateLimitedError,
    BAD_REQUEST: BadRequestError,
    INVALID_IP: AccessDeniedError,
    ACCESS_DENIED: AccessDeniedError,
    PRIVATE_WAR_LOG: PrivateWarLogError,
    SERVER_ERROR: ServerError,
}


def raise_for_error(response: Any) -> Any:
    """Raise a typed :class:`CocApiError` if ``response`` is an error dict.

    Returns the response unchanged when it is not an error, so it can wrap calls::

        clan = raise_for_error(api.clan_tag("#ABC"))
    """
    if isinstance(response, dict) and response.get("result") == "error":
        exc = _KIND_TO_EXC.get(response.get("error_kind", ""), CocApiError)
        raise exc(response)
    return response
