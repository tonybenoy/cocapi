"""Tests for the 403 accessDenied.invalidIp auto-refresh flow."""

import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from cocapi import ApiConfig, CocApi


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_response(status_code: int, json_data: dict) -> httpx.Response:
    """Create a mock httpx.Response."""
    resp = httpx.Response(
        status_code=status_code,
        json=json_data,
        request=httpx.Request("GET", "https://api.clashofclans.com/v1/test"),
    )
    return resp


def _make_403_invalid_ip() -> httpx.Response:
    return _make_response(403, {"reason": "accessDenied.invalidIp"})


def _make_403_other() -> httpx.Response:
    return _make_response(403, {"reason": "accessDenied"})


def _make_200_ok() -> httpx.Response:
    return _make_response(200, {"items": [], "paging": {"cursors": {}}})


# ---------------------------------------------------------------------------
# Sync GET
# ---------------------------------------------------------------------------


class TestSyncGetAutoRefresh:
    def test_403_invalidIp_triggers_refresh_and_retries(self):
        """On 403 invalidIp, should call _refresh_token() then retry."""
        with patch.object(CocApi, "test", return_value={"result": "success"}):
            api = CocApi("old_token", config=ApiConfig(max_retries=1))
            api._km_email = "test@example.com"
            api._km_password = "pass"  # NOSONAR — fake test credential

        with (
            patch("httpx.get", side_effect=[_make_403_invalid_ip(), _make_200_ok()]),
            patch.object(api, "_refresh_token", return_value=True) as mock_refresh,
        ):
            result = api._sync_api_response("/test")

        mock_refresh.assert_called_once()
        assert result.get("result") != "error"

    def test_403_invalidIp_no_refresh_when_not_configured(self):
        """Without credential state, should NOT attempt refresh."""
        with patch.object(CocApi, "test", return_value={"result": "success"}):
            api = CocApi("token", config=ApiConfig(max_retries=1))
            # _km_email is None by default

        with patch("httpx.get", return_value=_make_403_invalid_ip()):
            result = api._sync_api_response("/test")

        assert result.get("result") == "error"

    def test_403_invalidIp_no_infinite_loop(self):
        """After refresh, if still 403, should NOT retry again."""
        with patch.object(CocApi, "test", return_value={"result": "success"}):
            api = CocApi("token", config=ApiConfig(max_retries=1))
            api._km_email = "test@example.com"
            api._km_password = "pass"  # NOSONAR — fake test credential

        with (
            patch("httpx.get", return_value=_make_403_invalid_ip()),
            patch.object(api, "_refresh_token", return_value=True) as mock_refresh,
        ):
            result = api._sync_api_response("/test")

        # Called once for the first 403, then the retry also gets 403
        # but _refresh_attempted=True prevents a second refresh
        mock_refresh.assert_called_once()
        assert result.get("result") == "error"

    def test_403_other_reason_no_refresh(self):
        """403 without invalidIp reason should NOT trigger refresh."""
        with patch.object(CocApi, "test", return_value={"result": "success"}):
            api = CocApi("token", config=ApiConfig(max_retries=1))
            api._km_email = "test@example.com"
            api._km_password = "pass"  # NOSONAR — fake test credential

        with (
            patch("httpx.get", return_value=_make_403_other()),
            patch.object(api, "_refresh_token") as mock_refresh,
        ):
            result = api._sync_api_response("/test")

        mock_refresh.assert_not_called()
        assert result.get("result") == "error"


# ---------------------------------------------------------------------------
# Sync POST
# ---------------------------------------------------------------------------


class TestSyncPostAutoRefresh:
    def test_post_403_invalidIp_triggers_refresh(self):
        with patch.object(CocApi, "test", return_value={"result": "success"}):
            api = CocApi("token", config=ApiConfig(max_retries=1))
            api._km_email = "test@example.com"
            api._km_password = "pass"  # NOSONAR — fake test credential

        resp_403 = _make_403_invalid_ip()
        resp_200 = _make_response(200, {"status": "ok", "tag": "#P1"})

        with (
            patch("httpx.post", side_effect=[resp_403, resp_200]),
            patch.object(api, "_refresh_token", return_value=True) as mock_refresh,
        ):
            result = api._sync_api_post_response("/test", {"token": "abc"})

        mock_refresh.assert_called_once()
        assert result.get("status") == "ok"

    def test_post_403_no_refresh_when_not_configured(self):
        with patch.object(CocApi, "test", return_value={"result": "success"}):
            api = CocApi("token", config=ApiConfig(max_retries=1))

        with patch("httpx.post", return_value=_make_403_invalid_ip()):
            result = api._sync_api_post_response("/test", {"token": "abc"})

        assert result.get("result") == "error"


# ---------------------------------------------------------------------------
# Async GET
# ---------------------------------------------------------------------------


class TestAsyncGetAutoRefresh:
    @pytest.mark.asyncio
    async def test_async_403_invalidIp_triggers_refresh(self):
        with patch.object(CocApi, "test", return_value={"result": "success"}):
            config = ApiConfig(max_retries=1)
            api = CocApi("token", config=config, async_mode=True)

        from cocapi.async_client import AsyncCocApiCore

        core = AsyncCocApiCore("token", config)
        core._km_email = "test@example.com"
        core._km_password = "pass"  # NOSONAR — fake test credential
        core._km_auto_refresh = True

        mock_client = AsyncMock()
        resp_403 = _make_403_invalid_ip()
        resp_200 = _make_200_ok()
        mock_client.get = AsyncMock(side_effect=[resp_403, resp_200])
        core._client = mock_client

        with patch.object(core, "_refresh_token", return_value=True) as mock_refresh:
            result = await core.make_request("/test")

        mock_refresh.assert_called_once()
        assert result.get("result") != "error"

    @pytest.mark.asyncio
    async def test_async_403_no_refresh_when_not_configured(self):
        config = ApiConfig(max_retries=1)

        from cocapi.async_client import AsyncCocApiCore

        core = AsyncCocApiCore("token", config)
        # _km_email is None by default

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=_make_403_invalid_ip())
        core._client = mock_client

        result = await core.make_request("/test")
        assert result.get("result") == "error"

    @pytest.mark.asyncio
    async def test_async_403_no_infinite_loop(self):
        config = ApiConfig(max_retries=1)

        from cocapi.async_client import AsyncCocApiCore

        core = AsyncCocApiCore("token", config)
        core._km_email = "test@example.com"
        core._km_password = "pass"  # NOSONAR — fake test credential
        core._km_auto_refresh = True

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=_make_403_invalid_ip())
        core._client = mock_client

        with patch.object(core, "_refresh_token", return_value=True) as mock_refresh:
            result = await core.make_request("/test")

        mock_refresh.assert_called_once()
        assert result.get("result") == "error"


# ---------------------------------------------------------------------------
# Async POST
# ---------------------------------------------------------------------------


class TestAsyncPostAutoRefresh:
    @pytest.mark.asyncio
    async def test_async_post_403_invalidIp_triggers_refresh(self):
        config = ApiConfig(max_retries=1)

        from cocapi.async_client import AsyncCocApiCore

        core = AsyncCocApiCore("token", config)
        core._km_email = "test@example.com"
        core._km_password = "pass"  # NOSONAR — fake test credential
        core._km_auto_refresh = True

        mock_client = AsyncMock()
        resp_403 = _make_403_invalid_ip()
        resp_200 = _make_response(200, {"status": "ok"})
        mock_client.post = AsyncMock(side_effect=[resp_403, resp_200])
        core._client = mock_client

        with patch.object(core, "_refresh_token", return_value=True) as mock_refresh:
            result = await core.make_post_request("/test", {"token": "abc"})

        mock_refresh.assert_called_once()
        assert result.get("status") == "ok"
