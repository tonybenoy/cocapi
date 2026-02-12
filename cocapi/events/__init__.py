"""
cocapi.events -- Event polling system for real-time Clash of Clans monitoring.

Async-only. Requires ``CocApi`` in async mode.

Usage::

    from cocapi import CocApi, ApiConfig
    from cocapi.events import EventStream, EventType

    async with CocApi("token", config=ApiConfig(enable_caching=False)) as api:
        stream = EventStream(api)
        stream.watch_clans(["#ABC"], interval=60)
        stream.watch_wars(["#ABC"], interval=30)

        async with stream:
            async for event in stream:
                print(event.event_type, event.tag, event.changes)
"""

from ._diff import diff_dicts, diff_member_tags
from ._state import PollingState
from ._stream import EventStream
from ._types import Change, Event, EventType, WarState
from ._war_fsm import WarStateMachine
from ._watchers import BaseWatcher, ClanWatcher, PlayerWatcher, WarWatcher

__all__ = [
    "EventStream",
    "Event",
    "EventType",
    "Change",
    "WarState",
    "BaseWatcher",
    "ClanWatcher",
    "WarWatcher",
    "PlayerWatcher",
    "PollingState",
    "WarStateMachine",
    "diff_dicts",
    "diff_member_tags",
]
