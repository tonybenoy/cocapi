"""
Tests for the paginate() helper on CocApi.
"""

import pytest
from unittest.mock import patch

from cocapi import CocApi
from cocapi.utils import extract_after_cursor, extract_items


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _page(items, after=None):
    """Build a fake paginated API response dict."""
    cursors = {}
    if after is not None:
        cursors["after"] = after
    return {
        "items": items,
        "paging": {"cursors": cursors},
    }


def _error():
    return {"result": "error", "message": "Something went wrong", "status_code": 500}


# ---------------------------------------------------------------------------
# extract_items / extract_after_cursor  (unit tests on utils helpers)
# ---------------------------------------------------------------------------

class TestExtractItems:
    def test_dict_with_items(self):
        assert extract_items({"items": [1, 2, 3]}) == [1, 2, 3]

    def test_dict_without_items(self):
        assert extract_items({"tag": "#ABC"}) == []

    def test_empty_dict(self):
        assert extract_items({}) == []

    def test_pydantic_model(self):
        class FakeModel:
            items = [{"a": 1}]
        assert extract_items(FakeModel()) == [{"a": 1}]

    def test_pydantic_model_no_items(self):
        class FakeModel:
            pass
        assert extract_items(FakeModel()) == []


class TestExtractAfterCursor:
    def test_dict_with_cursor(self):
        resp = _page([], after="abc123")
        assert extract_after_cursor(resp) == "abc123"

    def test_dict_no_cursor(self):
        resp = _page([])
        assert extract_after_cursor(resp) is None

    def test_dict_no_paging(self):
        assert extract_after_cursor({"items": []}) is None

    def test_dict_paging_none_cursors(self):
        assert extract_after_cursor({"items": [], "paging": {"cursors": None}}) is None

    def test_dict_paging_none(self):
        assert extract_after_cursor({"items": [], "paging": None}) is None

    def test_pydantic_model(self):
        class Cursors:
            after = "xyz"
            before = None

        class Paging:
            cursors = Cursors()

        class Resp:
            items = []
            paging = Paging()

        assert extract_after_cursor(Resp()) == "xyz"

    def test_pydantic_model_no_paging(self):
        class Resp:
            items = []
        assert extract_after_cursor(Resp()) is None


# ---------------------------------------------------------------------------
# Sync paginate tests
# ---------------------------------------------------------------------------

class TestSyncPaginate:
    @pytest.fixture()
    def api(self):
        with patch.object(CocApi, "test", return_value={"result": "success"}):
            return CocApi("fake_token")

    def test_multiple_pages(self, api):
        page1 = _page([{"name": "a"}, {"name": "b"}], after="cur1")
        page2 = _page([{"name": "c"}], after=None)

        calls = iter([page1, page2])

        def fake_method(tag, params=None):
            return next(calls)

        items = list(api.paginate(fake_method, "#TAG", limit=2))
        assert items == [{"name": "a"}, {"name": "b"}, {"name": "c"}]

    def test_single_page_no_cursor(self, api):
        page1 = _page([{"id": 1}, {"id": 2}])

        def fake_method(params=None):
            return page1

        items = list(api.paginate(fake_method, limit=10))
        assert items == [{"id": 1}, {"id": 2}]

    def test_empty_first_page(self, api):
        def fake_method(tag, params=None):
            return _page([])

        items = list(api.paginate(fake_method, "#TAG"))
        assert items == []

    def test_error_on_first_page(self, api):
        def fake_method(tag, params=None):
            return _error()

        items = list(api.paginate(fake_method, "#TAG"))
        assert items == []

    def test_error_on_second_page(self, api):
        call_count = 0

        def fake_method(tag, params=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _page([{"id": 1}], after="cur1")
            return _error()

        items = list(api.paginate(fake_method, "#TAG"))
        assert items == [{"id": 1}]

    def test_passes_limit_and_after(self, api):
        """Verify the params dict passed to the method is correct."""
        received_params = []

        def fake_method(tag, params=None):
            received_params.append(params)
            if len(received_params) == 1:
                return _page([{"id": 1}], after="cursor_abc")
            return _page([{"id": 2}])

        list(api.paginate(fake_method, "#TAG", limit=50))
        assert received_params[0] == {"limit": 50}
        assert received_params[1] == {"limit": 50, "after": "cursor_abc"}

    def test_no_args_method(self, api):
        """Methods like league() that take only params."""
        page = _page([{"id": 29000022}])

        def fake_method(params=None):
            return page

        items = list(api.paginate(fake_method, limit=5))
        assert items == [{"id": 29000022}]

    def test_two_args_method(self, api):
        """Methods like league_season_id(id, sid, params)."""
        page = _page([{"rank": 1}])

        def fake_method(lid, sid, params=None):
            return page

        items = list(api.paginate(fake_method, "29000022", "2025-01", limit=100))
        assert items == [{"rank": 1}]


# ---------------------------------------------------------------------------
# Async paginate tests
# ---------------------------------------------------------------------------

class TestAsyncPaginate:
    @pytest.fixture()
    def api(self):
        with patch.object(CocApi, "test", return_value={"result": "success"}):
            api = CocApi("fake_token")
            # Force async mode without full context manager setup
            api.async_mode = True
            return api

    @pytest.mark.asyncio
    async def test_multiple_pages(self, api):
        page1 = _page([{"name": "a"}, {"name": "b"}], after="cur1")
        page2 = _page([{"name": "c"}])

        calls = iter([page1, page2])

        async def fake_method(tag, params=None):
            return next(calls)

        items = [item async for item in api.paginate(fake_method, "#TAG", limit=2)]
        assert items == [{"name": "a"}, {"name": "b"}, {"name": "c"}]

    @pytest.mark.asyncio
    async def test_single_page_no_cursor(self, api):
        page1 = _page([{"id": 1}])

        async def fake_method(params=None):
            return page1

        items = [item async for item in api.paginate(fake_method, limit=10)]
        assert items == [{"id": 1}]

    @pytest.mark.asyncio
    async def test_empty_first_page(self, api):
        async def fake_method(tag, params=None):
            return _page([])

        items = [item async for item in api.paginate(fake_method, "#TAG")]
        assert items == []

    @pytest.mark.asyncio
    async def test_error_on_first_page(self, api):
        async def fake_method(tag, params=None):
            return _error()

        items = [item async for item in api.paginate(fake_method, "#TAG")]
        assert items == []

    @pytest.mark.asyncio
    async def test_error_on_second_page(self, api):
        call_count = 0

        async def fake_method(tag, params=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _page([{"id": 1}], after="cur1")
            return _error()

        items = [item async for item in api.paginate(fake_method, "#TAG")]
        assert items == [{"id": 1}]

    @pytest.mark.asyncio
    async def test_passes_limit_and_after(self, api):
        received_params = []

        async def fake_method(tag, params=None):
            received_params.append(params)
            if len(received_params) == 1:
                return _page([{"id": 1}], after="cursor_abc")
            return _page([{"id": 2}])

        items = [item async for item in api.paginate(fake_method, "#TAG", limit=25)]
        assert received_params[0] == {"limit": 25}
        assert received_params[1] == {"limit": 25, "after": "cursor_abc"}
        assert items == [{"id": 1}, {"id": 2}]


# ---------------------------------------------------------------------------
# Pydantic model response tests
# ---------------------------------------------------------------------------

class TestPaginatePydanticModels:
    @pytest.fixture()
    def api(self):
        with patch.object(CocApi, "test", return_value={"result": "success"}):
            return CocApi("fake_token")

    def test_pydantic_response(self, api):
        """paginate works when the API returns Pydantic model objects."""

        class Cursors:
            def __init__(self, after=None):
                self.after = after
                self.before = None

        class Paging:
            def __init__(self, after=None):
                self.cursors = Cursors(after)

        class PageResp:
            def __init__(self, items, after=None):
                self.items = items
                self.paging = Paging(after)

        calls = iter([
            PageResp([{"name": "a"}], after="c1"),
            PageResp([{"name": "b"}]),
        ])

        def fake_method(tag, params=None):
            return next(calls)

        items = list(api.paginate(fake_method, "#TAG", limit=1))
        assert items == [{"name": "a"}, {"name": "b"}]
