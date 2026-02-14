"""EventStream — main entry point for the event polling system."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Callable, Coroutine
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._state import PollingState
from ._types import Event, EventType
from ._watchers import ClanWatcher, MaintenanceWatcher, PlayerWatcher, WarWatcher

if TYPE_CHECKING:
    from cocapi import CocApi

logger = logging.getLogger(__name__)

EventCallback = Callable[[Event], Coroutine[Any, Any, None]]


class EventStream:
    """Real-time event stream for Clash of Clans resources.

    Usage as async generator::

        async with CocApi("token") as api:
            stream = EventStream(api)
            stream.watch_clans(["#ABC"], interval=60)

            async with stream:
                async for event in stream:
                    print(event.event_type, event.changes)

    Usage with callbacks::

        @stream.on(EventType.MEMBER_JOINED)
        async def on_join(event):
            print(f"{event.metadata['member_name']} joined!")

        await stream.run()

    Args:
        api: A CocApi instance in async mode (inside ``async with``).
        queue_size: Max events buffered before backpressure (0 = unlimited).
        persist_path: Optional path for state persistence across restarts.
    """

    def __init__(
        self,
        api: CocApi,
        queue_size: int = 1000,
        persist_path: Path | str | None = None,
    ) -> None:
        """Initialize the event stream.

        Args:
            api: A CocApi instance in async mode (inside ``async with``).
            queue_size: Max events buffered before backpressure (0 = unlimited).
            persist_path: Optional path for state persistence across restarts.

        Raises:
            RuntimeError: If the CocApi instance is not in async mode.
        """
        if not api.async_mode:
            raise RuntimeError(
                "EventStream requires CocApi in async mode. "
                "Use 'async with CocApi(token) as api:'"
            )
        self._api = api
        self._state = PollingState()
        self._queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=queue_size)
        self._watchers: list[
            ClanWatcher | WarWatcher | PlayerWatcher | MaintenanceWatcher
        ] = []
        self._callbacks: dict[EventType | None, list[EventCallback]] = {}
        self._running = False
        self._persist_path = Path(persist_path) if persist_path else None

        if self._persist_path:
            self._state.load(self._persist_path)

    # --- Watcher registration ---

    def watch_clans(
        self,
        tags: list[str],
        interval: float = 60.0,
        track_members: bool = True,
    ) -> EventStream:
        """Register clans for polling.

        Args:
            tags: Clan tags to watch.
            interval: Seconds between polls (default 60).
            track_members: Track member joins/leaves/updates (default True).
        """
        watcher = ClanWatcher(
            api=self._api,
            state=self._state,
            queue=self._queue,
            clan_tags=tags,
            interval=interval,
            track_members=track_members,
        )
        self._watchers.append(watcher)
        return self

    def watch_wars(
        self,
        tags: list[str],
        interval: float = 30.0,
    ) -> EventStream:
        """Register clans for war state polling.

        Args:
            tags: Clan tags to watch for war updates.
            interval: Seconds between polls (default 30).
        """
        watcher = WarWatcher(
            api=self._api,
            state=self._state,
            queue=self._queue,
            clan_tags=tags,
            interval=interval,
        )
        self._watchers.append(watcher)
        return self

    def watch_players(
        self,
        tags: list[str],
        interval: float = 120.0,
        include_fields: frozenset[str] | None = None,
        exclude_fields: frozenset[str] | None = None,
    ) -> EventStream:
        """Register players for polling.

        Args:
            tags: Player tags to watch.
            interval: Seconds between polls (default 120).
            include_fields: Only report changes to these fields.
            exclude_fields: Ignore changes to these fields.
        """
        watcher = PlayerWatcher(
            api=self._api,
            state=self._state,
            queue=self._queue,
            player_tags=tags,
            interval=interval,
            include_fields=include_fields,
            exclude_fields=exclude_fields,
        )
        self._watchers.append(watcher)
        return self

    def watch_maintenance(
        self,
        interval: float = 30.0,
        probe_tag: str = "#JY9J2Y99",
    ) -> EventStream:
        """Enable API maintenance detection.

        Polls a known player endpoint to detect 503 maintenance responses.
        Emits ``MAINTENANCE_START`` and ``MAINTENANCE_END`` events.

        Args:
            interval: Seconds between probes (default 30).
            probe_tag: Player tag to probe (default ``#JY9J2Y99``).
        """
        watcher = MaintenanceWatcher(
            api=self._api,
            state=self._state,
            queue=self._queue,
            interval=interval,
            probe_tag=probe_tag,
        )
        self._watchers.append(watcher)
        return self

    # --- Callback registration ---

    def on(
        self,
        event_type: EventType | None = None,
    ) -> Callable[[EventCallback], EventCallback]:
        """Decorator to register an event callback.

        Args:
            event_type: Filter for specific event type. None matches all.
        """

        def decorator(func: EventCallback) -> EventCallback:
            self._callbacks.setdefault(event_type, []).append(func)
            return func

        return decorator

    def add_callback(
        self,
        callback: EventCallback,
        event_type: EventType | None = None,
    ) -> None:
        """Register an event callback programmatically."""
        self._callbacks.setdefault(event_type, []).append(callback)

    # --- Async context manager ---

    async def __aenter__(self) -> EventStream:
        await self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.stop()

    # --- Lifecycle ---

    async def start(self) -> None:
        """Start all registered watchers."""
        self._running = True
        for watcher in self._watchers:
            watcher.start()

    async def stop(self) -> None:
        """Stop all watchers and persist state if configured."""
        self._running = False
        for watcher in self._watchers:
            await watcher.stop()
        if self._persist_path:
            self._state.save(self._persist_path)

    async def run(self) -> None:
        """Run the stream with callback dispatch until stopped.

        Call ``stream.stop()`` from a callback or signal handler to exit.
        """
        async with self:
            async for event in self:
                await self._dispatch(event)

    # --- Async iteration ---

    def __aiter__(self) -> AsyncIterator[Event]:
        return self

    async def __anext__(self) -> Event:
        if not self._running and self._queue.empty():
            raise StopAsyncIteration

        while self._running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                return event
            except asyncio.TimeoutError:
                continue

        # Drain remaining events after stop
        if not self._queue.empty():
            return self._queue.get_nowait()

        raise StopAsyncIteration

    # --- Internal ---

    async def _dispatch(self, event: Event) -> None:
        """Dispatch event to registered callbacks."""
        for cb in self._callbacks.get(event.event_type, []):
            try:
                await cb(event)
            except Exception as e:
                logger.error("Callback error for %s: %s", event.event_type, e)

        for cb in self._callbacks.get(None, []):
            try:
                await cb(event)
            except Exception as e:
                logger.error("Wildcard callback error: %s", e)
