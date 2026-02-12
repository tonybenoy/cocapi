"""
Tests for cocapi key_manager module.

All tests use mocked HTTP responses — no real API calls.
"""

import json

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from cocapi.key_manager import (
    AsyncKeyManager,
    InvalidCredentials,
    KeyManagerError,
    SyncKeyManager,
    _extract_ip_from_response,
    _invalidate_cached_keys,
    _load_cached_keys,
    _save_cached_keys,
    _filter_managed_keys,
    _is_valid_ip,
)


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------

_DEFAULT_CIDR = ["1.2.3.4"]


def _make_key(
    key_id: str = "key-1",
    name: str = "cocapi_auto",
    key: str = "token-abc123",
    cidr_ranges: list[str] | None = None,
) -> dict:
    return {
        "id": key_id,
        "name": name,
        "key": key,
        "description": "test key",
        "cidrRanges": _DEFAULT_CIDR if cidr_ranges is None else cidr_ranges,
        "scopes": ["clash"],
    }


def _mock_response(status_code: int = 200, json_data: dict | None = None) -> Mock:
    resp = Mock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.text = ""
    return resp


# ===========================================================================
# Pure function tests
# ===========================================================================


class TestIsValidIp:
    def test_valid_ipv4(self) -> None:
        assert _is_valid_ip("1.2.3.4") is True

    def test_valid_ipv6(self) -> None:
        assert _is_valid_ip("::1") is True

    def test_invalid_string(self) -> None:
        assert _is_valid_ip("not-an-ip") is False

    def test_html_page(self) -> None:
        assert _is_valid_ip("<html>error</html>") is False

    def test_empty(self) -> None:
        assert _is_valid_ip("") is False


class TestExtractIpFromResponse:
    def test_top_level_ip(self) -> None:
        assert _extract_ip_from_response({"ip": "5.6.7.8"}) == "5.6.7.8"

    def test_top_level_ipAddress(self) -> None:
        assert _extract_ip_from_response({"ipAddress": "5.6.7.8"}) == "5.6.7.8"

    def test_nested_in_auth(self) -> None:
        data = {"auth": {"ip": "9.9.9.9"}}
        assert _extract_ip_from_response(data) == "9.9.9.9"

    def test_nested_in_developer(self) -> None:
        data = {"developer": {"ipAddress": "10.0.0.1"}}
        assert _extract_ip_from_response(data) == "10.0.0.1"

    def test_no_ip_found(self) -> None:
        assert _extract_ip_from_response({"status": {"message": "ok"}}) is None

    def test_invalid_ip_ignored(self) -> None:
        assert _extract_ip_from_response({"ip": "not-valid"}) is None


class TestFilterManagedKeys:
    def test_all_valid(self) -> None:
        keys = [_make_key(cidr_ranges=["1.2.3.4"])]
        valid, stale, unmanaged = _filter_managed_keys(keys, "1.2.3.4", "cocapi_auto")
        assert len(valid) == 1
        assert len(stale) == 0
        assert len(unmanaged) == 0

    def test_all_stale(self) -> None:
        keys = [_make_key(cidr_ranges=["9.9.9.9"])]
        valid, stale, unmanaged = _filter_managed_keys(keys, "1.2.3.4", "cocapi_auto")
        assert len(valid) == 0
        assert len(stale) == 1

    def test_unmanaged_keys_untouched(self) -> None:
        keys = [_make_key(name="other_app", cidr_ranges=["1.2.3.4"])]
        valid, stale, unmanaged = _filter_managed_keys(keys, "1.2.3.4", "cocapi_auto")
        assert len(valid) == 0
        assert len(stale) == 0
        assert len(unmanaged) == 1

    def test_mixed_keys(self) -> None:
        keys = [
            _make_key(key_id="1", cidr_ranges=["1.2.3.4"]),  # valid
            _make_key(key_id="2", cidr_ranges=["9.9.9.9"]),  # stale
            _make_key(key_id="3", name="other", cidr_ranges=["1.2.3.4"]),  # unmanaged
        ]
        valid, stale, unmanaged = _filter_managed_keys(keys, "1.2.3.4", "cocapi_auto")
        assert len(valid) == 1
        assert len(stale) == 1
        assert len(unmanaged) == 1

    def test_empty_cidr(self) -> None:
        keys = [_make_key(cidr_ranges=[])]
        valid, stale, _ = _filter_managed_keys(keys, "1.2.3.4", "cocapi_auto")
        assert len(valid) == 0
        assert len(stale) == 1


# ===========================================================================
# SyncKeyManager tests
# ===========================================================================


class TestSyncKeyManager:
    def test_init_defaults(self) -> None:
        km = SyncKeyManager("test@example.com", "password123")
        assert km.email == "test@example.com"
        assert km.key_name == "cocapi_auto"
        assert km.key_count == 1
        km.close()

    def test_key_count_capped_at_10(self) -> None:
        km = SyncKeyManager("a@b.com", "p", key_count=20)
        assert km.key_count == 10
        km.close()

    def test_context_manager(self) -> None:
        with SyncKeyManager("a@b.com", "p") as km:
            assert km.email == "a@b.com"

    @patch("cocapi.key_manager.httpx.Client")
    def test_detect_ip_first_provider_succeeds(self, mock_client_cls: Mock) -> None:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        resp = _mock_response(200)
        resp.text = "  1.2.3.4  "
        mock_client.get.return_value = resp

        km = SyncKeyManager("a@b.com", "p")
        km._client = mock_client
        ip = km._detect_ip()
        assert ip == "1.2.3.4"
        km.close()

    @patch("cocapi.key_manager.httpx.Client")
    def test_detect_ip_fallback(self, mock_client_cls: Mock) -> None:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        fail_resp = _mock_response(500)
        ok_resp = _mock_response(200)
        ok_resp.text = "5.6.7.8"
        mock_client.get.side_effect = [fail_resp, ok_resp]

        km = SyncKeyManager("a@b.com", "p")
        km._client = mock_client
        ip = km._detect_ip()
        assert ip == "5.6.7.8"
        km.close()

    @patch("cocapi.key_manager.httpx.Client")
    def test_detect_ip_all_fail(self, mock_client_cls: Mock) -> None:
        import httpx

        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.get.side_effect = httpx.TimeoutException("timeout")

        km = SyncKeyManager("a@b.com", "p")
        km._client = mock_client
        with pytest.raises(KeyManagerError, match="Could not detect public IP"):
            km._detect_ip()
        km.close()

    @patch("cocapi.key_manager.httpx.Client")
    def test_login_success(self, mock_client_cls: Mock) -> None:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        resp = _mock_response(200, {"status": {"message": "ok"}})
        mock_client.post.return_value = resp

        km = SyncKeyManager("a@b.com", "p")
        km._client = mock_client
        km._login()
        assert km._logged_in is True
        km.close()

    @patch("cocapi.key_manager.httpx.Client")
    def test_login_extracts_ip(self, mock_client_cls: Mock) -> None:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        resp = _mock_response(200, {"status": {"message": "ok"}, "ip": "10.0.0.1"})
        mock_client.post.return_value = resp

        km = SyncKeyManager("a@b.com", "p")
        km._client = mock_client
        km._login()
        assert km._current_ip == "10.0.0.1"
        km.close()

    @patch("cocapi.key_manager.httpx.Client")
    def test_login_invalid_credentials(self, mock_client_cls: Mock) -> None:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        resp = _mock_response(403)
        mock_client.post.return_value = resp

        km = SyncKeyManager("a@b.com", "wrong")
        km._client = mock_client
        with pytest.raises(InvalidCredentials):
            km._login()
        km.close()

    @patch("cocapi.key_manager.httpx.Client")
    def test_login_portal_error_message(self, mock_client_cls: Mock) -> None:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        resp = _mock_response(200, {"status": {"message": "invalid credentials"}})
        mock_client.post.return_value = resp

        km = SyncKeyManager("a@b.com", "wrong")
        km._client = mock_client
        with pytest.raises(InvalidCredentials, match="invalid credentials"):
            km._login()
        km.close()

    @patch("cocapi.key_manager.httpx.Client")
    def test_manage_keys_fresh_account(self, mock_client_cls: Mock) -> None:
        """No existing keys → login, detect IP, create one."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        login_resp = _mock_response(200, {"status": {"message": "ok"}})
        list_resp = _mock_response(200, {"keys": []})
        create_resp = _mock_response(
            200,
            {"key": _make_key(key="new-token-xyz", cidr_ranges=["1.2.3.4"])},
        )

        ip_resp = _mock_response(200)
        ip_resp.text = "1.2.3.4"

        # post calls: login, list_keys, create_key
        mock_client.post.side_effect = [login_resp, list_resp, create_resp]
        # get call: detect_ip
        mock_client.get.return_value = ip_resp

        km = SyncKeyManager("a@b.com", "p")
        km._client = mock_client
        tokens = km.manage_keys()
        assert tokens == ["new-token-xyz"]
        km.close()

    @patch("cocapi.key_manager.httpx.Client")
    def test_manage_keys_existing_valid(self, mock_client_cls: Mock) -> None:
        """Valid key exists → return its token, no create/revoke."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        login_resp = _mock_response(
            200, {"status": {"message": "ok"}, "ip": "1.2.3.4"}
        )
        list_resp = _mock_response(
            200,
            {"keys": [_make_key(key="existing-token", cidr_ranges=["1.2.3.4"])]},
        )

        mock_client.post.side_effect = [login_resp, list_resp]

        km = SyncKeyManager("a@b.com", "p")
        km._client = mock_client
        tokens = km.manage_keys()
        assert tokens == ["existing-token"]
        # Should only have called login + list (no revoke or create)
        assert mock_client.post.call_count == 2
        km.close()

    @patch("cocapi.key_manager.httpx.Client")
    def test_manage_keys_revoke_stale_create_new(self, mock_client_cls: Mock) -> None:
        """Stale key (wrong IP) → revoke it, create new one."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        login_resp = _mock_response(
            200, {"status": {"message": "ok"}, "ip": "1.2.3.4"}
        )
        list_resp = _mock_response(
            200,
            {"keys": [_make_key(key_id="old-id", key="old-token", cidr_ranges=["9.9.9.9"])]},
        )
        revoke_resp = _mock_response(200)
        create_resp = _mock_response(
            200,
            {"key": _make_key(key="fresh-token", cidr_ranges=["1.2.3.4"])},
        )

        mock_client.post.side_effect = [login_resp, list_resp, revoke_resp, create_resp]

        km = SyncKeyManager("a@b.com", "p")
        km._client = mock_client
        tokens = km.manage_keys()
        assert tokens == ["fresh-token"]
        assert mock_client.post.call_count == 4  # login, list, revoke, create
        km.close()

    @patch("cocapi.key_manager.httpx.Client")
    def test_manage_keys_multiple_keys(self, mock_client_cls: Mock) -> None:
        """Request 2 keys, 0 exist → create 2."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        login_resp = _mock_response(
            200, {"status": {"message": "ok"}, "ip": "1.2.3.4"}
        )
        list_resp = _mock_response(200, {"keys": []})
        create_resp_1 = _mock_response(
            200, {"key": _make_key(key="token-1", cidr_ranges=["1.2.3.4"])}
        )
        create_resp_2 = _mock_response(
            200, {"key": _make_key(key="token-2", cidr_ranges=["1.2.3.4"])}
        )

        mock_client.post.side_effect = [login_resp, list_resp, create_resp_1, create_resp_2]

        km = SyncKeyManager("a@b.com", "p", key_count=2)
        km._client = mock_client
        tokens = km.manage_keys()
        assert len(tokens) == 2
        assert tokens == ["token-1", "token-2"]
        km.close()

    @patch("cocapi.key_manager.httpx.Client")
    def test_manage_keys_respects_account_limit(self, mock_client_cls: Mock) -> None:
        """Account at 9 unmanaged keys + 0 ours → can only create 1 even if key_count=3."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        unmanaged_keys = [
            _make_key(key_id=f"other-{i}", name="other_app") for i in range(9)
        ]

        login_resp = _mock_response(
            200, {"status": {"message": "ok"}, "ip": "1.2.3.4"}
        )
        list_resp = _mock_response(200, {"keys": unmanaged_keys})
        create_resp = _mock_response(
            200, {"key": _make_key(key="only-token", cidr_ranges=["1.2.3.4"])}
        )

        mock_client.post.side_effect = [login_resp, list_resp, create_resp]

        km = SyncKeyManager("a@b.com", "p", key_count=3)
        km._client = mock_client
        tokens = km.manage_keys()
        assert len(tokens) == 1  # Only 1 slot available
        km.close()

    @patch("cocapi.key_manager.httpx.Client")
    def test_refresh_keys(self, mock_client_cls: Mock) -> None:
        """refresh_keys resets state and re-manages."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        login_resp = _mock_response(
            200, {"status": {"message": "ok"}, "ip": "2.2.2.2"}
        )
        list_resp = _mock_response(200, {"keys": []})
        create_resp = _mock_response(
            200, {"key": _make_key(key="refreshed-token", cidr_ranges=["2.2.2.2"])}
        )

        mock_client.post.side_effect = [login_resp, list_resp, create_resp]

        km = SyncKeyManager("a@b.com", "p")
        km._client = mock_client
        km._current_ip = "1.1.1.1"  # Old IP
        km._logged_in = True

        tokens = km.refresh_keys()
        assert tokens == ["refreshed-token"]
        assert km._current_ip == "2.2.2.2"
        km.close()


# ===========================================================================
# AsyncKeyManager tests
# ===========================================================================


class TestAsyncKeyManager:
    def test_init_defaults(self) -> None:
        km = AsyncKeyManager("test@example.com", "password123")
        assert km.email == "test@example.com"
        assert km.key_name == "cocapi_auto"

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        with patch("cocapi.key_manager.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value = mock_client
            async with AsyncKeyManager("a@b.com", "p") as km:
                assert km._client is not None

    @pytest.mark.asyncio
    async def test_login_success(self) -> None:
        km = AsyncKeyManager("a@b.com", "p")
        mock_client = AsyncMock()

        resp = _mock_response(200, {"status": {"message": "ok"}})
        mock_client.post.return_value = resp

        km._client = mock_client
        await km._login()
        assert km._logged_in is True

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self) -> None:
        km = AsyncKeyManager("a@b.com", "wrong")
        mock_client = AsyncMock()

        resp = _mock_response(403)
        mock_client.post.return_value = resp

        km._client = mock_client
        with pytest.raises(InvalidCredentials):
            await km._login()

    @pytest.mark.asyncio
    async def test_manage_keys_fresh(self) -> None:
        km = AsyncKeyManager("a@b.com", "p")
        mock_client = AsyncMock()

        login_resp = _mock_response(200, {"status": {"message": "ok"}, "ip": "1.2.3.4"})
        list_resp = _mock_response(200, {"keys": []})
        create_resp = _mock_response(
            200, {"key": _make_key(key="async-token", cidr_ranges=["1.2.3.4"])}
        )

        mock_client.post.side_effect = [login_resp, list_resp, create_resp]
        km._client = mock_client

        tokens = await km.manage_keys()
        assert tokens == ["async-token"]

    @pytest.mark.asyncio
    async def test_manage_keys_existing_valid(self) -> None:
        km = AsyncKeyManager("a@b.com", "p")
        mock_client = AsyncMock()

        login_resp = _mock_response(
            200, {"status": {"message": "ok"}, "ip": "1.2.3.4"}
        )
        list_resp = _mock_response(
            200,
            {"keys": [_make_key(key="existing", cidr_ranges=["1.2.3.4"])]},
        )

        mock_client.post.side_effect = [login_resp, list_resp]
        km._client = mock_client

        tokens = await km.manage_keys()
        assert tokens == ["existing"]
        assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_manage_keys_revoke_and_create(self) -> None:
        km = AsyncKeyManager("a@b.com", "p")
        mock_client = AsyncMock()

        login_resp = _mock_response(
            200, {"status": {"message": "ok"}, "ip": "1.2.3.4"}
        )
        list_resp = _mock_response(
            200,
            {"keys": [_make_key(key_id="old", key="old-t", cidr_ranges=["9.9.9.9"])]},
        )
        revoke_resp = _mock_response(200)
        create_resp = _mock_response(
            200, {"key": _make_key(key="new-t", cidr_ranges=["1.2.3.4"])}
        )

        mock_client.post.side_effect = [login_resp, list_resp, revoke_resp, create_resp]
        km._client = mock_client

        tokens = await km.manage_keys()
        assert tokens == ["new-t"]

    @pytest.mark.asyncio
    async def test_refresh_keys(self) -> None:
        km = AsyncKeyManager("a@b.com", "p")
        mock_client = AsyncMock()

        login_resp = _mock_response(
            200, {"status": {"message": "ok"}, "ip": "3.3.3.3"}
        )
        list_resp = _mock_response(200, {"keys": []})
        create_resp = _mock_response(
            200, {"key": _make_key(key="refreshed", cidr_ranges=["3.3.3.3"])}
        )

        mock_client.post.side_effect = [login_resp, list_resp, create_resp]
        km._client = mock_client
        km._current_ip = "1.1.1.1"
        km._logged_in = True

        tokens = await km.refresh_keys()
        assert tokens == ["refreshed"]
        assert km._current_ip == "3.3.3.3"


# ===========================================================================
# CocApi.from_credentials integration test
# ===========================================================================


class TestFromCredentials:
    @patch("cocapi.key_manager.httpx.Client")
    @patch.object(
        __import__("cocapi.client", fromlist=["CocApi"]).CocApi,
        "test",
        return_value={"result": "success"},
    )
    def test_from_credentials_creates_api(
        self, mock_test: Mock, mock_client_cls: Mock
    ) -> None:
        from cocapi import CocApi

        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        login_resp = _mock_response(
            200, {"status": {"message": "ok"}, "ip": "1.2.3.4"}
        )
        list_resp = _mock_response(200, {"keys": []})
        create_resp = _mock_response(
            200, {"key": _make_key(key="my-token", cidr_ranges=["1.2.3.4"])}
        )

        mock_client.post.side_effect = [login_resp, list_resp, create_resp]

        api = CocApi.from_credentials("a@b.com", "p")
        assert api.token == "my-token"
        assert api._km_email == "a@b.com"
        assert api._km_password == "p"
        assert api._km_tokens == ["my-token"]


# ===========================================================================
# Key persistence tests
# ===========================================================================


class TestKeyPersistence:
    def test_save_and_load_round_trip(self, tmp_path) -> None:
        cache_file = tmp_path / "keys.json"
        _save_cached_keys(cache_file, "my_key", ["token-1", "token-2"], "1.2.3.4")

        result = _load_cached_keys(cache_file, "my_key")
        assert result is not None
        tokens, ip = result
        assert tokens == ["token-1", "token-2"]
        assert ip == "1.2.3.4"

    def test_load_missing_file(self, tmp_path) -> None:
        cache_file = tmp_path / "nonexistent.json"
        assert _load_cached_keys(cache_file, "my_key") is None

    def test_load_missing_key_name(self, tmp_path) -> None:
        cache_file = tmp_path / "keys.json"
        _save_cached_keys(cache_file, "other_key", ["t"], "1.1.1.1")
        assert _load_cached_keys(cache_file, "my_key") is None

    def test_load_corrupt_file(self, tmp_path) -> None:
        cache_file = tmp_path / "keys.json"
        cache_file.write_text("not valid json{{{")
        assert _load_cached_keys(cache_file, "my_key") is None

    def test_save_merges_with_existing(self, tmp_path) -> None:
        cache_file = tmp_path / "keys.json"
        _save_cached_keys(cache_file, "app1", ["t1"], "1.1.1.1")
        _save_cached_keys(cache_file, "app2", ["t2"], "2.2.2.2")

        # Both entries should exist
        assert _load_cached_keys(cache_file, "app1") is not None
        assert _load_cached_keys(cache_file, "app2") is not None

    def test_save_creates_parent_dirs(self, tmp_path) -> None:
        cache_file = tmp_path / "deep" / "nested" / "keys.json"
        _save_cached_keys(cache_file, "k", ["t"], "1.1.1.1")
        assert cache_file.is_file()

    def test_invalidate_removes_entry(self, tmp_path) -> None:
        cache_file = tmp_path / "keys.json"
        _save_cached_keys(cache_file, "my_key", ["t"], "1.1.1.1")
        _invalidate_cached_keys(cache_file, "my_key")
        assert _load_cached_keys(cache_file, "my_key") is None

    def test_invalidate_preserves_other_entries(self, tmp_path) -> None:
        cache_file = tmp_path / "keys.json"
        _save_cached_keys(cache_file, "keep_me", ["t1"], "1.1.1.1")
        _save_cached_keys(cache_file, "delete_me", ["t2"], "2.2.2.2")
        _invalidate_cached_keys(cache_file, "delete_me")
        assert _load_cached_keys(cache_file, "keep_me") is not None
        assert _load_cached_keys(cache_file, "delete_me") is None

    def test_invalidate_missing_file_no_error(self, tmp_path) -> None:
        cache_file = tmp_path / "nope.json"
        _invalidate_cached_keys(cache_file, "k")  # Should not raise

    def test_persist_disabled_by_default(self, tmp_path) -> None:
        """Default SyncKeyManager does not create any cache file."""
        km = SyncKeyManager("a@b.com", "p")
        assert km.persist_keys is False
        km.close()

    @patch("cocapi.key_manager.httpx.Client")
    def test_manage_keys_uses_cache_on_ip_match(
        self, mock_client_cls: Mock, tmp_path
    ) -> None:
        """When persist_keys=True and cached IP matches, skip login."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        cache_file = tmp_path / "keys.json"
        # Pre-populate cache
        _save_cached_keys(cache_file, "cocapi_auto", ["cached-token"], "1.2.3.4")

        # IP detection returns matching IP
        ip_resp = _mock_response(200)
        ip_resp.text = "1.2.3.4"
        mock_client.get.return_value = ip_resp

        km = SyncKeyManager(
            "a@b.com", "p", persist_keys=True, key_storage_path=str(cache_file)
        )
        km._client = mock_client
        tokens = km.manage_keys()

        assert tokens == ["cached-token"]
        # Should NOT have called post (no login, no list, no create)
        mock_client.post.assert_not_called()
        km.close()

    @patch("cocapi.key_manager.httpx.Client")
    def test_manage_keys_falls_through_on_ip_change(
        self, mock_client_cls: Mock, tmp_path
    ) -> None:
        """When cached IP differs from current, fall through to full flow."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        cache_file = tmp_path / "keys.json"
        _save_cached_keys(cache_file, "cocapi_auto", ["old-token"], "9.9.9.9")

        # IP detection returns different IP
        ip_resp = _mock_response(200)
        ip_resp.text = "1.2.3.4"
        mock_client.get.return_value = ip_resp

        # Full flow responses (login, list, create)
        login_resp = _mock_response(
            200, {"status": {"message": "ok"}, "ip": "1.2.3.4"}
        )
        list_resp = _mock_response(200, {"keys": []})
        create_resp = _mock_response(
            200, {"key": _make_key(key="new-token", cidr_ranges=["1.2.3.4"])}
        )
        mock_client.post.side_effect = [login_resp, list_resp, create_resp]

        km = SyncKeyManager(
            "a@b.com", "p", persist_keys=True, key_storage_path=str(cache_file)
        )
        km._client = mock_client
        tokens = km.manage_keys()

        assert tokens == ["new-token"]
        # Should have called login + list + create
        assert mock_client.post.call_count == 3

        # Cache should be updated with new token
        cached = _load_cached_keys(cache_file, "cocapi_auto")
        assert cached is not None
        assert cached[0] == ["new-token"]
        assert cached[1] == "1.2.3.4"
        km.close()

    @patch("cocapi.key_manager.httpx.Client")
    def test_manage_keys_saves_to_cache(
        self, mock_client_cls: Mock, tmp_path
    ) -> None:
        """After full flow, tokens are saved when persist_keys=True."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        cache_file = tmp_path / "keys.json"

        login_resp = _mock_response(
            200, {"status": {"message": "ok"}, "ip": "5.5.5.5"}
        )
        list_resp = _mock_response(200, {"keys": []})
        create_resp = _mock_response(
            200, {"key": _make_key(key="saved-token", cidr_ranges=["5.5.5.5"])}
        )
        mock_client.post.side_effect = [login_resp, list_resp, create_resp]

        km = SyncKeyManager(
            "a@b.com", "p", persist_keys=True, key_storage_path=str(cache_file)
        )
        km._client = mock_client
        tokens = km.manage_keys()

        assert tokens == ["saved-token"]
        assert cache_file.is_file()

        data = json.loads(cache_file.read_text())
        assert data["cocapi_auto"]["tokens"] == ["saved-token"]
        assert data["cocapi_auto"]["ip"] == "5.5.5.5"
        km.close()

    @patch("cocapi.key_manager.httpx.Client")
    def test_refresh_keys_invalidates_cache(
        self, mock_client_cls: Mock, tmp_path
    ) -> None:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        cache_file = tmp_path / "keys.json"
        _save_cached_keys(cache_file, "cocapi_auto", ["old"], "1.1.1.1")

        login_resp = _mock_response(
            200, {"status": {"message": "ok"}, "ip": "2.2.2.2"}
        )
        list_resp = _mock_response(200, {"keys": []})
        create_resp = _mock_response(
            200, {"key": _make_key(key="fresh", cidr_ranges=["2.2.2.2"])}
        )
        mock_client.post.side_effect = [login_resp, list_resp, create_resp]

        km = SyncKeyManager(
            "a@b.com", "p", persist_keys=True, key_storage_path=str(cache_file)
        )
        km._client = mock_client
        km._current_ip = "1.1.1.1"
        km._logged_in = True

        tokens = km.refresh_keys()
        assert tokens == ["fresh"]

        # Cache should now have the new token
        cached = _load_cached_keys(cache_file, "cocapi_auto")
        assert cached is not None
        assert cached[0] == ["fresh"]
        assert cached[1] == "2.2.2.2"
        km.close()
