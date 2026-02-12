"""
Tests for the batch() helper on CocApi.
"""

import pytest
from unittest.mock import patch

from cocapi import CocApi


# ---------------------------------------------------------------------------
# Sync batch tests
# ---------------------------------------------------------------------------


class TestSyncBatch:
    @pytest.fixture()
    def api(self):
        with patch.object(CocApi, "test", return_value={"result": "success"}):
            return CocApi("fake_token")

    def test_single_arg_calls(self, api):
        def fake_players(tag):
            return {"tag": tag, "name": f"Player {tag}"}

        results = api.batch(fake_players, ["#A", "#B", "#C"])
        assert len(results) == 3
        assert results[0] == {"tag": "#A", "name": "Player #A"}
        assert results[2] == {"tag": "#C", "name": "Player #C"}

    def test_tuple_arg_calls(self, api):
        def fake_season(lid, sid):
            return {"league": lid, "season": sid}

        results = api.batch(fake_season, [("29000022", "2025-01"), ("29000022", "2025-02")])
        assert len(results) == 2
        assert results[0]["season"] == "2025-01"
        assert results[1]["season"] == "2025-02"

    def test_error_in_one_call(self, api):
        call_count = 0

        def fake_method(tag):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                return {"result": "error", "message": "Not found"}
            return {"tag": tag}

        results = api.batch(fake_method, ["#A", "#B", "#C"])
        assert len(results) == 3
        assert results[0] == {"tag": "#A"}
        assert results[1]["result"] == "error"
        assert results[2] == {"tag": "#C"}

    def test_empty_list(self, api):
        def fake_method(tag):
            return {"tag": tag}

        results = api.batch(fake_method, [])
        assert results == []

    def test_list_arg_calls(self, api):
        """Lists should be unpacked just like tuples."""

        def fake_method(a, b):
            return {"a": a, "b": b}

        results = api.batch(fake_method, [["x", "y"]])
        assert results == [{"a": "x", "b": "y"}]


# ---------------------------------------------------------------------------
# Async batch tests
# ---------------------------------------------------------------------------


class TestAsyncBatch:
    @pytest.fixture()
    def api(self):
        with patch.object(CocApi, "test", return_value={"result": "success"}):
            api = CocApi("fake_token")
            api.async_mode = True
            return api

    @pytest.mark.asyncio
    async def test_concurrent_calls(self, api):
        async def fake_players(tag):
            return {"tag": tag}

        results = await api.batch(fake_players, ["#A", "#B", "#C"])
        assert len(results) == 3
        assert {r["tag"] for r in results} == {"#A", "#B", "#C"}

    @pytest.mark.asyncio
    async def test_tuple_arg_calls(self, api):
        async def fake_season(lid, sid):
            return {"league": lid, "season": sid}

        results = await api.batch(fake_season, [("29000022", "2025-01"), ("29000022", "2025-02")])
        assert len(results) == 2
        assert results[0]["season"] == "2025-01"

    @pytest.mark.asyncio
    async def test_error_in_one_call(self, api):
        call_count = 0

        async def fake_method(tag):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                return {"result": "error", "message": "Not found"}
            return {"tag": tag}

        results = await api.batch(fake_method, ["#A", "#B", "#C"])
        assert len(results) == 3
        assert results[1]["result"] == "error"

    @pytest.mark.asyncio
    async def test_max_concurrent(self, api):
        """max_concurrent limits parallel requests via semaphore."""
        import asyncio

        running = 0
        max_running = 0

        async def fake_method(tag):
            nonlocal running, max_running
            running += 1
            max_running = max(max_running, running)
            await asyncio.sleep(0.01)
            running -= 1
            return {"tag": tag}

        tags = [f"#{i}" for i in range(10)]
        results = await api.batch(fake_method, tags, max_concurrent=3)
        assert len(results) == 10
        assert max_running <= 3

    @pytest.mark.asyncio
    async def test_empty_list(self, api):
        async def fake_method(tag):
            return {"tag": tag}

        results = await api.batch(fake_method, [])
        assert results == []
