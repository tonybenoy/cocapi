"""Tests for EventStream."""

import asyncio

import pytest
from unittest.mock import AsyncMock, patch

from cocapi import CocApi
from cocapi.events._stream import EventStream
from cocapi.events._types import Event, EventType


@pytest.fixture()
def api():
    with patch.object(CocApi, "test", return_value={"result": "success"}):
        api = CocApi("fake_token")
        api.async_mode = True
        return api


class TestEventStreamInit:
    def test_requires_async_mode(self):
        with patch.object(CocApi, "test", return_value={"result": "success"}):
            api = CocApi("fake_token")
            assert api.async_mode is False
            with pytest.raises(RuntimeError, match="async mode"):
                EventStream(api)

    def test_accepts_async_api(self, api):
        stream = EventStream(api)
        assert stream._running is False

    def test_loads_persisted_state(self, api, tmp_path):
        import json

        path = tmp_path / "state.json"
        path.write_text(json.dumps({
            "clans": {"#A": {"tag": "#A"}},
            "members": {},
            "wars": {},
            "war_states": {},
            "players": {},
            "last_poll_times": {},
        }))
        stream = EventStream(api, persist_path=path)
        assert stream._state.get_clan("#A") is not None


class TestEventStreamChaining:
    def test_watch_methods_return_self(self, api):
        stream = EventStream(api)
        result = stream.watch_clans(["#A"]).watch_wars(["#A"]).watch_players(["#P1"])
        assert result is stream
        assert len(stream._watchers) == 3


class TestEventStreamLifecycle:
    @pytest.mark.asyncio
    async def test_start_stop(self, api):
        api.clan_tag = AsyncMock(return_value={"tag": "#A", "memberList": []})
        stream = EventStream(api)
        stream.watch_clans(["#A"], interval=100)

        await stream.start()
        assert stream._running is True
        assert stream._watchers[0]._task is not None

        await stream.stop()
        assert stream._running is False

    @pytest.mark.asyncio
    async def test_context_manager(self, api):
        api.clan_tag = AsyncMock(return_value={"tag": "#A", "memberList": []})
        stream = EventStream(api)
        stream.watch_clans(["#A"], interval=100)

        async with stream:
            assert stream._running is True
        assert stream._running is False

    @pytest.mark.asyncio
    async def test_persists_on_stop(self, api, tmp_path):
        path = tmp_path / "state.json"
        stream = EventStream(api, persist_path=path)
        stream.watch_clans(["#A"], interval=100)
        api.clan_tag = AsyncMock(return_value={"tag": "#A", "memberList": []})

        async with stream:
            pass

        assert path.exists()


class TestEventStreamIteration:
    @pytest.mark.asyncio
    async def test_yields_events(self, api):
        """Manually push events to queue and verify async iteration."""
        stream = EventStream(api)
        stream._running = True

        event = Event(event_type=EventType.CLAN_UPDATED, tag="#A")
        await stream._queue.put(event)

        # Stop after getting the event
        async def stop_soon():
            await asyncio.sleep(0.05)
            stream._running = False

        task = asyncio.create_task(stop_soon())  # noqa: F841

        collected = []
        async for e in stream:
            collected.append(e)
            break  # Just get one event

        assert len(collected) == 1
        assert collected[0].event_type == EventType.CLAN_UPDATED


class TestEventStreamCallbacks:
    @pytest.mark.asyncio
    async def test_callback_dispatch(self, api):
        stream = EventStream(api)
        received = []

        @stream.on(EventType.CLAN_UPDATED)
        async def handler(event: Event) -> None:
            received.append(event)

        event = Event(event_type=EventType.CLAN_UPDATED, tag="#A")
        await stream._dispatch(event)

        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_wildcard_callback(self, api):
        stream = EventStream(api)
        received = []

        @stream.on(None)
        async def handler(event: Event) -> None:
            received.append(event)

        e1 = Event(event_type=EventType.CLAN_UPDATED, tag="#A")
        e2 = Event(event_type=EventType.PLAYER_UPDATED, tag="#P1")
        await stream._dispatch(e1)
        await stream._dispatch(e2)

        assert len(received) == 2

    @pytest.mark.asyncio
    async def test_callback_error_does_not_crash(self, api):
        stream = EventStream(api)

        @stream.on(EventType.CLAN_UPDATED)
        async def bad_handler(event: Event) -> None:
            raise ValueError("oops")

        event = Event(event_type=EventType.CLAN_UPDATED, tag="#A")
        await stream._dispatch(event)  # Should not raise

    @pytest.mark.asyncio
    async def test_add_callback_programmatic(self, api):
        stream = EventStream(api)
        received = []

        async def handler(event: Event) -> None:
            received.append(event)

        stream.add_callback(handler, EventType.MEMBER_JOINED)

        event = Event(event_type=EventType.MEMBER_JOINED, tag="#A")
        await stream._dispatch(event)

        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_specific_and_wildcard_both_fire(self, api):
        stream = EventStream(api)
        specific = []
        wildcard = []

        @stream.on(EventType.CLAN_UPDATED)
        async def on_clan(event: Event) -> None:
            specific.append(event)

        @stream.on(None)
        async def on_any(event: Event) -> None:
            wildcard.append(event)

        event = Event(event_type=EventType.CLAN_UPDATED, tag="#A")
        await stream._dispatch(event)

        assert len(specific) == 1
        assert len(wildcard) == 1
