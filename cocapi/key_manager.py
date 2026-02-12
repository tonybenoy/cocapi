"""
SuperCell Developer Portal Key Manager
=======================================
Automates API key management for the Clash of Clans developer portal.

Handles login, IP detection, key creation/revocation, and automatic
IP-based key rotation. Ported to httpx from the aiohttp reference
implementation (coc.py's http.py / marsidev/get-sc-key).

Developer Portal Internal API Endpoints:
    Base URL: https://developer.clashofclans.com/api

    POST /login          - Authenticate with email/password (session cookie)
    POST /apikey/list    - List all keys for the authenticated account
    POST /apikey/create  - Create a new API key
    POST /apikey/revoke  - Delete/revoke an existing API key
"""

import ipaddress
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# SuperCell Developer Portal API endpoints
_BASE_URL = "https://developer.clashofclans.com/api"
_LOGIN_URL = f"{_BASE_URL}/login"
_KEY_LIST_URL = f"{_BASE_URL}/apikey/list"
_KEY_CREATE_URL = f"{_BASE_URL}/apikey/create"
_KEY_REVOKE_URL = f"{_BASE_URL}/apikey/revoke"

# IP detection providers (ordered by reliability)
_IP_PROVIDERS = [
    "https://checkip.amazonaws.com",  # AWS-backed, highly reliable
    "https://icanhazip.com",  # Cloudflare-backed
    "https://api.ipify.org",  # Popular, generally reliable
    "https://ifconfig.me/ip",  # Simple, well-known
    "https://ipinfo.io/ip",  # Feature-rich service
    "https://api.my-ip.io/v2/ip.txt",  # Plain text response
]
_IP_DETECT_TIMEOUT = 5  # seconds per provider

# SuperCell enforces a max of 10 keys per account
_MAX_KEYS_PER_ACCOUNT = 10


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class KeyManagerError(Exception):
    """Base exception for key manager errors."""


class InvalidCredentials(KeyManagerError):
    """Raised when email/password login fails."""


class KeyLimitReached(KeyManagerError):
    """Raised when the 10 key per account limit is hit."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_valid_ip(ip: str) -> bool:
    """Validate that a string is a real IP address, not an error page."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def _extract_ip_from_response(data: dict[str, Any]) -> str | None:
    """
    Attempt to find the caller's IP address in the login response JSON.

    The developer portal response structure may vary, so we check
    multiple known/possible locations.
    """
    # Direct top-level fields
    for field_name in ("ip", "ipAddress", "ip_address", "clientIp"):
        val = data.get(field_name)
        if val and _is_valid_ip(str(val)):
            return str(val).strip()

    # Nested inside common wrapper objects
    for wrapper in ("auth", "developer", "session"):
        if isinstance(data.get(wrapper), dict):
            for field_name in ("ip", "ipAddress", "ip_address", "prevLoginIp"):
                val = data[wrapper].get(field_name)
                if val and _is_valid_ip(str(val)):
                    return str(val).strip()

    return None


def _filter_managed_keys(
    keys: list[dict[str, Any]],
    current_ip: str,
    key_name: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Partition keys into (valid, stale, unmanaged).

    valid:     key name matches AND current_ip is in the CIDR list
    stale:     key name matches AND current_ip is NOT in the CIDR list
    unmanaged: key name does not match (left untouched)
    """
    valid: list[dict[str, Any]] = []
    stale: list[dict[str, Any]] = []
    unmanaged: list[dict[str, Any]] = []

    for key in keys:
        if key.get("name") != key_name:
            unmanaged.append(key)
            continue

        cidrs = key.get("cidrRanges", [])
        # The portal stores IPs as plain ("1.2.3.4") or CIDR ("1.2.3.4/32")
        if current_ip in cidrs or f"{current_ip}/32" in cidrs:
            valid.append(key)
        else:
            stale.append(key)

    return valid, stale, unmanaged


# ---------------------------------------------------------------------------
# Local key persistence
# ---------------------------------------------------------------------------

_DEFAULT_KEY_STORAGE_PATH = Path.home() / ".cocapi" / "keys.json"
_ALLOWED_KEY_STORAGE_PARENT = Path.home()


def _safe_resolve(path: Path) -> Path:
    """Resolve *path* to an absolute path, rejecting traversal components.

    Also ensures the key storage path stays under the user's home directory
    to prevent writing sensitive tokens to arbitrary locations.
    """
    resolved = path.resolve()
    if ".." in resolved.parts:
        raise ValueError(f"Path traversal detected: {path}")
    try:
        resolved.relative_to(_ALLOWED_KEY_STORAGE_PARENT)
    except ValueError:
        raise ValueError(
            f"Key storage path must be under {_ALLOWED_KEY_STORAGE_PARENT}, "
            f"got: {resolved}"
        ) from None
    return resolved


def _load_cached_keys(cache_path: Path, key_name: str) -> tuple[list[str], str] | None:
    """
    Load cached tokens from disk.

    Returns (tokens, ip) if a valid cache entry exists, else None.
    """
    try:
        cache_path = _safe_resolve(cache_path)
        if not cache_path.is_file():
            return None
        data = json.loads(cache_path.read_text())
        entry = data.get(key_name)
        if not entry:
            return None
        tokens = entry.get("tokens", [])
        ip = entry.get("ip", "")
        if tokens and ip:
            return tokens, ip
    except (json.JSONDecodeError, OSError, KeyError) as e:
        logger.debug("Failed to load key cache from %s: %s", cache_path, e)
    return None


def _save_cached_keys(
    cache_path: Path, key_name: str, tokens: list[str], ip: str
) -> None:
    """Save tokens to disk, merging with any existing entries."""
    try:
        cache_path = _safe_resolve(cache_path)
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        # Merge with existing data (other key_names)
        data: dict[str, Any] = {}
        if cache_path.is_file():
            try:
                data = json.loads(cache_path.read_text())
            except (json.JSONDecodeError, OSError):
                data = {}

        data[key_name] = {
            "tokens": tokens,
            "ip": ip,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        cache_path.write_text(json.dumps(data, indent=2))
        # Restrict file permissions to owner-only (0600)
        if sys.platform != "win32":
            os.chmod(cache_path, 0o600)
        logger.info("Saved %d token(s) to %s", len(tokens), cache_path)
    except OSError as e:
        logger.warning("Failed to save key cache to %s: %s", cache_path, e)


def _invalidate_cached_keys(cache_path: Path, key_name: str) -> None:
    """Remove a specific key_name entry from the cache file."""
    try:
        cache_path = _safe_resolve(cache_path)
        if not cache_path.is_file():
            return
        data = json.loads(cache_path.read_text())
        if key_name in data:
            del data[key_name]
            cache_path.write_text(json.dumps(data, indent=2))
            if sys.platform != "win32":
                os.chmod(cache_path, 0o600)
            logger.info("Invalidated cached keys for '%s'", key_name)
    except (json.JSONDecodeError, OSError) as e:
        logger.debug("Failed to invalidate key cache: %s", e)


# ---------------------------------------------------------------------------
# SyncKeyManager
# ---------------------------------------------------------------------------


class SyncKeyManager:
    """
    Synchronous key manager for the SuperCell developer portal.

    Handles login, IP detection, and API key lifecycle management
    using httpx.Client with cookie persistence.

    Usage::

        with SyncKeyManager("email", "password") as km:
            tokens = km.manage_keys()
            # Use tokens[0] with CocApi

    Or via CocApi integration::

        api = CocApi.from_credentials("email@example.com", "password")
    """

    def __init__(
        self,
        email: str,
        password: str,
        key_name: str = "cocapi_auto",
        key_count: int = 1,
        key_description: str = "Auto-generated by cocapi KeyManager",
        key_scopes: str = "clash",
        persist_keys: bool = False,
        key_storage_path: str | None = None,
    ) -> None:
        self.email = email
        self.password = password
        self.key_name = key_name
        self.key_count = min(key_count, _MAX_KEYS_PER_ACCOUNT)
        self.key_description = key_description
        self.key_scopes = key_scopes
        self.persist_keys = persist_keys
        self._cache_path = (
            Path(key_storage_path) if key_storage_path else _DEFAULT_KEY_STORAGE_PATH
        )

        self._client = httpx.Client(follow_redirects=True)
        self._logged_in = False
        self._current_ip: str | None = None

    def __enter__(self) -> "SyncKeyManager":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    # ----- IP detection -----

    def _detect_ip(self) -> str:
        """
        Detect public IP using multiple providers with fallback.

        Tries each provider in order. Returns as soon as one succeeds.
        Validates the response is actually an IP (not an HTML error page).
        """
        for provider in _IP_PROVIDERS:
            try:
                resp = self._client.get(provider, timeout=_IP_DETECT_TIMEOUT)
                if resp.status_code == 200:
                    ip = resp.text.strip()
                    if _is_valid_ip(ip):
                        logger.info("Detected public IP: %s (via %s)", ip, provider)
                        return ip
                    else:
                        logger.debug("Invalid IP response from %s: %r", provider, ip)
            except (httpx.HTTPError, httpx.TimeoutException) as e:
                logger.debug("IP provider %s failed: %s", provider, e)
                continue

        raise KeyManagerError(
            "Could not detect public IP from any provider. "
            "Check your internet connection."
        )

    # ----- Login -----

    def _login(self) -> None:
        """
        Authenticate with the SuperCell developer portal.

        On success, sets session cookies on self._client for subsequent
        requests. Also attempts to extract the caller's IP from the response.
        """
        resp = self._client.post(
            _LOGIN_URL,
            json={"email": self.email, "password": self.password},
            timeout=30,
        )

        if resp.status_code == 403:
            raise InvalidCredentials(
                "Invalid email/password for developer.clashofclans.com. "
                "Make sure you're using your developer portal credentials."
            )

        if resp.status_code != 200:
            raise KeyManagerError(
                f"Developer portal login returned HTTP {resp.status_code}"
            )

        try:
            data = resp.json()
        except (ValueError, TypeError) as e:
            raise KeyManagerError(f"Invalid JSON from login endpoint: {e}") from e

        status_msg = data.get("status", {}).get("message", "")
        if status_msg and status_msg != "ok":
            raise InvalidCredentials(f"Developer portal login failed: {status_msg}")

        # Try to extract IP from login response (avoids external call)
        extracted_ip = _extract_ip_from_response(data)
        if extracted_ip:
            self._current_ip = extracted_ip
            logger.info(
                "Extracted IP from login response: %s (no external call needed)",
                self._current_ip,
            )

        self._logged_in = True
        logger.info("Successfully logged into developer portal")

    # ----- Key CRUD -----

    def _list_keys(self) -> list[dict[str, Any]]:
        """List all API keys on the account."""
        resp = self._client.post(_KEY_LIST_URL, json={}, timeout=30)
        if resp.status_code != 200:
            raise KeyManagerError(f"Failed to list keys: HTTP {resp.status_code}")
        try:
            data = resp.json()
        except (ValueError, TypeError) as e:
            raise KeyManagerError(f"Invalid JSON from key list endpoint: {e}") from e
        keys = data.get("keys", [])
        logger.info("Found %d existing keys on account", len(keys))
        return keys

    def _create_key(
        self,
        name: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create a new API key whitelisted to the current IP."""
        resp = self._client.post(
            _KEY_CREATE_URL,
            json={
                "name": name or self.key_name,
                "description": description or self.key_description,
                "cidrRanges": [self._current_ip],
                "scopes": [self.key_scopes],
            },
            timeout=30,
        )
        if resp.status_code != 200:
            raise KeyManagerError(f"Failed to create key: HTTP {resp.status_code}")
        try:
            data = resp.json()
        except (ValueError, TypeError) as e:
            raise KeyManagerError(f"Invalid JSON from key create endpoint: {e}") from e

        if "key" not in data:
            error_msg = data.get("status", {}).get("message", "Unknown error")
            raise KeyManagerError(f"Failed to create key: {error_msg}")

        key_data = data["key"]
        logger.info(
            "Created new API key '%s' for IP %s",
            key_data.get("name"),
            self._current_ip,
        )
        return key_data

    def _revoke_key(self, key_id: str) -> None:
        """Delete an API key from the account."""
        resp = self._client.post(_KEY_REVOKE_URL, json={"id": key_id}, timeout=30)
        if resp.status_code == 200:
            logger.info("Revoked key: %s", key_id)
        else:
            logger.warning("Failed to revoke key %s: HTTP %d", key_id, resp.status_code)

    # ----- Orchestration -----

    def manage_keys(self) -> list[str]:
        """
        Main orchestration: ensure we have valid keys for the current IP.

        If persist_keys is enabled, checks the local cache first. When the
        cached IP matches the current IP, returns cached tokens immediately
        without contacting the developer portal.

        1. (Optional) Check local cache
        2. Login to developer portal
        3. Detect current public IP
        4. List existing keys
        5. Revoke stale keys (wrong IP), keep valid ones
        6. Create new keys if needed
        7. (Optional) Save tokens to local cache
        8. Return list of usable API token strings
        """
        # Try local cache first (avoids login entirely)
        if self.persist_keys:
            cached = _load_cached_keys(self._cache_path, self.key_name)
            if cached:
                cached_tokens, cached_ip = cached
                current_ip = self._detect_ip()
                self._current_ip = current_ip
                if cached_ip == current_ip:
                    logger.info(
                        "Using %d cached token(s) (IP unchanged: %s)",
                        len(cached_tokens),
                        current_ip,
                    )
                    return cached_tokens
                logger.info(
                    "IP changed (%s -> %s), cached tokens invalidated",
                    cached_ip,
                    current_ip,
                )

        self._login()

        if not self._current_ip:
            self._current_ip = self._detect_ip()

        existing_keys = self._list_keys()
        valid, stale, unmanaged = _filter_managed_keys(
            existing_keys, self._current_ip, self.key_name
        )

        logger.info(
            "Key audit: %d valid, %d stale (wrong IP), %d unmanaged",
            len(valid),
            len(stale),
            len(unmanaged),
        )

        # Revoke stale keys (wrong IP)
        for key in stale:
            self._revoke_key(key["id"])

        # Collect tokens from valid keys
        tokens = [k["key"] for k in valid]

        # Determine how many new keys to create
        keys_needed = self.key_count - len(tokens)
        total_after_revoke = len(unmanaged) + len(valid)
        available_slots = _MAX_KEYS_PER_ACCOUNT - total_after_revoke

        if keys_needed > 0:
            keys_to_create = min(keys_needed, available_slots)

            if keys_to_create < keys_needed:
                logger.warning(
                    "Account has %d keys (max %d). Can only create %d of %d needed. "
                    "Delete some keys at https://developer.clashofclans.com "
                    "or lower key_count.",
                    total_after_revoke,
                    _MAX_KEYS_PER_ACCOUNT,
                    keys_to_create,
                    keys_needed,
                )

            for _i in range(keys_to_create):
                suffix = f" #{len(tokens) + 1}" if self.key_count > 1 else ""
                new_key = self._create_key(
                    name=self.key_name,
                    description=f"{self.key_description}{suffix}",
                )
                tokens.append(new_key["key"])

        if not tokens:
            raise KeyManagerError(
                "No usable API keys available. The account may have reached "
                "the 10-key limit with keys from other applications. "
                "Please delete unused keys at https://developer.clashofclans.com"
            )

        # Save to local cache if persistence is enabled
        if self.persist_keys:
            _save_cached_keys(self._cache_path, self.key_name, tokens, self._current_ip)

        logger.info("Key manager ready with %d token(s)", len(tokens))
        return tokens

    def refresh_keys(self) -> list[str]:
        """
        Re-detect IP and re-initialize keys.

        Call this when the API returns accessDenied.invalidIp.
        """
        logger.info("Refreshing keys due to IP change...")
        if self.persist_keys:
            _invalidate_cached_keys(self._cache_path, self.key_name)
        self._current_ip = None
        self._logged_in = False
        return self.manage_keys()


# ---------------------------------------------------------------------------
# AsyncKeyManager
# ---------------------------------------------------------------------------


class AsyncKeyManager:
    """
    Async key manager for the SuperCell developer portal.

    Same functionality as SyncKeyManager but using httpx.AsyncClient.

    Usage::

        async with AsyncKeyManager("email", "password") as km:
            tokens = await km.manage_keys()
    """

    def __init__(
        self,
        email: str,
        password: str,
        key_name: str = "cocapi_auto",
        key_count: int = 1,
        key_description: str = "Auto-generated by cocapi KeyManager",
        key_scopes: str = "clash",
        persist_keys: bool = False,
        key_storage_path: str | None = None,
    ) -> None:
        self.email = email
        self.password = password
        self.key_name = key_name
        self.key_count = min(key_count, _MAX_KEYS_PER_ACCOUNT)
        self.key_description = key_description
        self.key_scopes = key_scopes
        self.persist_keys = persist_keys
        self._cache_path = (
            Path(key_storage_path) if key_storage_path else _DEFAULT_KEY_STORAGE_PATH
        )

        self._client: httpx.AsyncClient | None = None
        self._logged_in = False
        self._current_ip: str | None = None

    async def __aenter__(self) -> "AsyncKeyManager":
        self._client = httpx.AsyncClient(follow_redirects=True)
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the underlying async HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    # ----- IP detection -----

    async def _detect_ip(self) -> str:
        """Detect public IP using multiple providers with fallback."""
        assert self._client is not None

        for provider in _IP_PROVIDERS:
            try:
                resp = await self._client.get(provider, timeout=_IP_DETECT_TIMEOUT)
                if resp.status_code == 200:
                    ip = resp.text.strip()
                    if _is_valid_ip(ip):
                        logger.info("Detected public IP: %s (via %s)", ip, provider)
                        return ip
                    else:
                        logger.debug("Invalid IP response from %s: %r", provider, ip)
            except (httpx.HTTPError, httpx.TimeoutException) as e:
                logger.debug("IP provider %s failed: %s", provider, e)
                continue

        raise KeyManagerError(
            "Could not detect public IP from any provider. "
            "Check your internet connection."
        )

    # ----- Login -----

    async def _login(self) -> None:
        """Authenticate with the SuperCell developer portal."""
        assert self._client is not None

        resp = await self._client.post(
            _LOGIN_URL,
            json={"email": self.email, "password": self.password},
            timeout=30,
        )

        if resp.status_code == 403:
            raise InvalidCredentials(
                "Invalid email/password for developer.clashofclans.com. "
                "Make sure you're using your developer portal credentials."
            )

        if resp.status_code != 200:
            raise KeyManagerError(
                f"Developer portal login returned HTTP {resp.status_code}"
            )

        try:
            data = resp.json()
        except (ValueError, TypeError) as e:
            raise KeyManagerError(f"Invalid JSON from login endpoint: {e}") from e

        status_msg = data.get("status", {}).get("message", "")
        if status_msg and status_msg != "ok":
            raise InvalidCredentials(f"Developer portal login failed: {status_msg}")

        extracted_ip = _extract_ip_from_response(data)
        if extracted_ip:
            self._current_ip = extracted_ip
            logger.info(
                "Extracted IP from login response: %s (no external call needed)",
                self._current_ip,
            )

        self._logged_in = True
        logger.info("Successfully logged into developer portal (async)")

    # ----- Key CRUD -----

    async def _list_keys(self) -> list[dict[str, Any]]:
        """List all API keys on the account."""
        assert self._client is not None
        resp = await self._client.post(_KEY_LIST_URL, json={}, timeout=30)
        if resp.status_code != 200:
            raise KeyManagerError(f"Failed to list keys: HTTP {resp.status_code}")
        try:
            data = resp.json()
        except (ValueError, TypeError) as e:
            raise KeyManagerError(f"Invalid JSON from key list endpoint: {e}") from e
        keys = data.get("keys", [])
        logger.info("Found %d existing keys on account", len(keys))
        return keys

    async def _create_key(
        self,
        name: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create a new API key whitelisted to the current IP."""
        assert self._client is not None
        resp = await self._client.post(
            _KEY_CREATE_URL,
            json={
                "name": name or self.key_name,
                "description": description or self.key_description,
                "cidrRanges": [self._current_ip],
                "scopes": [self.key_scopes],
            },
            timeout=30,
        )
        if resp.status_code != 200:
            raise KeyManagerError(f"Failed to create key: HTTP {resp.status_code}")
        try:
            data = resp.json()
        except (ValueError, TypeError) as e:
            raise KeyManagerError(f"Invalid JSON from key create endpoint: {e}") from e

        if "key" not in data:
            error_msg = data.get("status", {}).get("message", "Unknown error")
            raise KeyManagerError(f"Failed to create key: {error_msg}")

        key_data = data["key"]
        logger.info(
            "Created new API key '%s' for IP %s",
            key_data.get("name"),
            self._current_ip,
        )
        return key_data

    async def _revoke_key(self, key_id: str) -> None:
        """Delete an API key from the account."""
        assert self._client is not None
        resp = await self._client.post(_KEY_REVOKE_URL, json={"id": key_id}, timeout=30)
        if resp.status_code == 200:
            logger.info("Revoked key: %s", key_id)
        else:
            logger.warning("Failed to revoke key %s: HTTP %d", key_id, resp.status_code)

    # ----- Orchestration -----

    async def manage_keys(self) -> list[str]:
        """
        Main orchestration: ensure we have valid keys for the current IP.
        Same logic as SyncKeyManager.manage_keys() but async.
        """
        # Try local cache first (avoids login entirely)
        if self.persist_keys:
            cached = _load_cached_keys(self._cache_path, self.key_name)
            if cached:
                cached_tokens, cached_ip = cached
                current_ip = await self._detect_ip()
                self._current_ip = current_ip
                if cached_ip == current_ip:
                    logger.info(
                        "Using %d cached token(s) (IP unchanged: %s)",
                        len(cached_tokens),
                        current_ip,
                    )
                    return cached_tokens
                logger.info(
                    "IP changed (%s -> %s), cached tokens invalidated",
                    cached_ip,
                    current_ip,
                )

        await self._login()

        if not self._current_ip:
            self._current_ip = await self._detect_ip()

        existing_keys = await self._list_keys()
        valid, stale, unmanaged = _filter_managed_keys(
            existing_keys, self._current_ip, self.key_name
        )

        logger.info(
            "Key audit: %d valid, %d stale (wrong IP), %d unmanaged",
            len(valid),
            len(stale),
            len(unmanaged),
        )

        for key in stale:
            await self._revoke_key(key["id"])

        tokens = [k["key"] for k in valid]

        keys_needed = self.key_count - len(tokens)
        total_after_revoke = len(unmanaged) + len(valid)
        available_slots = _MAX_KEYS_PER_ACCOUNT - total_after_revoke

        if keys_needed > 0:
            keys_to_create = min(keys_needed, available_slots)

            if keys_to_create < keys_needed:
                logger.warning(
                    "Account has %d keys (max %d). Can only create %d of %d needed.",
                    total_after_revoke,
                    _MAX_KEYS_PER_ACCOUNT,
                    keys_to_create,
                    keys_needed,
                )

            for _i in range(keys_to_create):
                suffix = f" #{len(tokens) + 1}" if self.key_count > 1 else ""
                new_key = await self._create_key(
                    name=self.key_name,
                    description=f"{self.key_description}{suffix}",
                )
                tokens.append(new_key["key"])

        if not tokens:
            raise KeyManagerError(
                "No usable API keys available. The account may have reached "
                "the 10-key limit with keys from other applications. "
                "Please delete unused keys at https://developer.clashofclans.com"
            )

        if self.persist_keys:
            _save_cached_keys(self._cache_path, self.key_name, tokens, self._current_ip)

        logger.info("Key manager ready with %d token(s)", len(tokens))
        return tokens

    async def refresh_keys(self) -> list[str]:
        """Re-detect IP and re-initialize keys."""
        logger.info("Refreshing keys due to IP change...")
        if self.persist_keys:
            _invalidate_cached_keys(self._cache_path, self.key_name)
        self._current_ip = None
        self._logged_in = False
        return await self.manage_keys()
