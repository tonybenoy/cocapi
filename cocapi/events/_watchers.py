"""Polling watchers that detect changes and produce events."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable
from typing import TYPE_CHECKING, Any, cast

from ._diff import diff_dicts, diff_member_tags
from ._state import PollingState
from ._types import Event, EventType

if TYPE_CHECKING:
    from cocapi import CocApi

logger = logging.getLogger(__name__)

_CLAN_EXCLUDE_FIELDS = frozenset({"memberList"})


class BaseWatcher:
    """Base class for all watchers.

    Subclasses implement ``_poll_once()`` which fetches data, diffs it,
    and returns a list of events.
    """

    def __init__(
        self,
        api: CocApi,
        state: PollingState,
        queue: asyncio.Queue[Event],
        interval: float,
    ) -> None:
        self._api = api
        self._state = state
        self._queue = queue
        self._interval = interval
        self._task: asyncio.Task[None] | None = None
        self._running = False

    @property
    def interval(self) -> float:
        return self._interval

    @interval.setter
    def interval(self, value: float) -> None:
        if value < 1.0:
            raise ValueError("Poll interval must be >= 1 second")
        self._interval = value

    def start(self) -> None:
        if self._task is not None:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _loop(self) -> None:
        while self._running:
            try:
                events = await self._poll_once()
                for event in events:
                    await self._queue.put(event)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error("Watcher %s error: %s", self.__class__.__name__, e)
                error_event = Event(
                    event_type=EventType.POLL_ERROR,
                    tag="",
                    metadata={"error": str(e), "watcher": self.__class__.__name__},
                )
                await self._queue.put(error_event)
            await asyncio.sleep(self._interval)

    async def _poll_once(self) -> list[Event]:
        raise NotImplementedError


class ClanWatcher(BaseWatcher):
    """Polls clan data and member lists."""

    def __init__(
        self,
        api: CocApi,
        state: PollingState,
        queue: asyncio.Queue[Event],
        clan_tags: list[str],
        interval: float = 60.0,
        track_members: bool = True,
    ) -> None:
        super().__init__(api, state, queue, interval)
        self._clan_tags = list(clan_tags)
        self._track_members = track_members

    async def _poll_once(self) -> list[Event]:
        events: list[Event] = []

        for tag in self._clan_tags:
            resource_key = f"clan:{tag}"
            if not self._state.should_poll(resource_key, self._interval):
                continue

            result: dict[str, Any] = await cast(
                Awaitable[dict[str, Any]], self._api.clan_tag(tag)
            )
            self._state.mark_polled(resource_key)

            if result.get("result") == "error":
                events.append(
                    Event(
                        event_type=EventType.POLL_ERROR,
                        tag=tag,
                        metadata={
                            "error": result.get("message", "Unknown"),
                            "endpoint": "clan_tag",
                        },
                    )
                )
                continue

            old = self._state.get_clan(tag)
            if old is not None:
                changes = diff_dicts(old, result, exclude_fields=_CLAN_EXCLUDE_FIELDS)
                if changes:
                    events.append(
                        Event(
                            event_type=EventType.CLAN_UPDATED,
                            tag=tag,
                            old_data=old,
                            new_data=result,
                            changes=tuple(changes),
                        )
                    )

            if self._track_members:
                new_members = result.get("memberList", [])
                old_members = self._state.get_members(tag)

                if old_members is not None:
                    joined, left, updated = diff_member_tags(old_members, new_members)

                    for m in joined:
                        events.append(
                            Event(
                                event_type=EventType.MEMBER_JOINED,
                                tag=tag,
                                new_data=m,
                                metadata={
                                    "member_tag": m.get("tag"),
                                    "member_name": m.get("name"),
                                },
                            )
                        )

                    for m in left:
                        events.append(
                            Event(
                                event_type=EventType.MEMBER_LEFT,
                                tag=tag,
                                old_data=m,
                                metadata={
                                    "member_tag": m.get("tag"),
                                    "member_name": m.get("name"),
                                },
                            )
                        )

                    for old_m, new_m in updated:
                        member_changes = diff_dicts(old_m, new_m)
                        if member_changes:
                            events.append(
                                Event(
                                    event_type=EventType.MEMBER_UPDATED,
                                    tag=tag,
                                    old_data=old_m,
                                    new_data=new_m,
                                    changes=tuple(member_changes),
                                    metadata={
                                        "member_tag": new_m.get("tag"),
                                        "member_name": new_m.get("name"),
                                    },
                                )
                            )

                self._state.set_members(tag, new_members)

            self._state.set_clan(tag, result)

        return events


class WarWatcher(BaseWatcher):
    """Polls current war and tracks state transitions and new attacks."""

    def __init__(
        self,
        api: CocApi,
        state: PollingState,
        queue: asyncio.Queue[Event],
        clan_tags: list[str],
        interval: float = 30.0,
    ) -> None:
        super().__init__(api, state, queue, interval)
        self._clan_tags = list(clan_tags)

    async def _poll_once(self) -> list[Event]:
        events: list[Event] = []

        for tag in self._clan_tags:
            resource_key = f"war:{tag}"
            if not self._state.should_poll(resource_key, self._interval):
                continue

            result: dict[str, Any] = await cast(
                Awaitable[dict[str, Any]], self._api.clan_current_war(tag)
            )
            self._state.mark_polled(resource_key)

            if result.get("result") == "error":
                events.append(
                    Event(
                        event_type=EventType.POLL_ERROR,
                        tag=tag,
                        metadata={
                            "error": result.get("message", "Unknown"),
                            "endpoint": "clan_current_war",
                        },
                    )
                )
                continue

            raw_state = result.get("state", "notInWar")
            fsm = self._state.get_war_fsm(tag)
            old_state = fsm.state
            new_state = fsm.transition(raw_state)

            if new_state is not None:
                events.append(
                    Event(
                        event_type=EventType.WAR_STATE_CHANGED,
                        tag=tag,
                        old_data=self._state.get_war(tag),
                        new_data=result,
                        metadata={
                            "war_state_from": old_state.value,
                            "war_state_to": new_state.value,
                        },
                    )
                )

            old_war = self._state.get_war(tag)
            if old_war is not None and raw_state in ("inWar", "warEnded"):
                new_attacks = self._find_new_attacks(old_war, result)
                for attack in new_attacks:
                    events.append(
                        Event(
                            event_type=EventType.WAR_ATTACK_NEW,
                            tag=tag,
                            new_data=attack,
                            metadata={
                                "attacker_tag": attack.get("attackerTag"),
                                "defender_tag": attack.get("defenderTag"),
                                "stars": attack.get("stars"),
                            },
                        )
                    )

            self._state.set_war(tag, result)

        return events

    @staticmethod
    def _find_new_attacks(
        old_war: dict[str, Any], new_war: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Find attacks in new_war that don't exist in old_war."""

        def _collect_attack_keys(
            war_data: dict[str, Any],
        ) -> set[tuple[str, int]]:
            keys: set[tuple[str, int]] = set()
            for side in ("clan", "opponent"):
                clan_data = war_data.get(side, {})
                for member in clan_data.get("members", []):
                    for atk in member.get("attacks", []):
                        keys.add((atk.get("attackerTag", ""), atk.get("order", 0)))
            return keys

        def _collect_attack_dicts(
            war_data: dict[str, Any],
        ) -> dict[tuple[str, int], dict[str, Any]]:
            result: dict[tuple[str, int], dict[str, Any]] = {}
            for side in ("clan", "opponent"):
                clan_data = war_data.get(side, {})
                for member in clan_data.get("members", []):
                    for atk in member.get("attacks", []):
                        key = (atk.get("attackerTag", ""), atk.get("order", 0))
                        result[key] = atk
            return result

        old_keys = _collect_attack_keys(old_war)
        new_dicts = _collect_attack_dicts(new_war)

        return [atk for key, atk in new_dicts.items() if key not in old_keys]


class PlayerWatcher(BaseWatcher):
    """Polls player data and detects field changes."""

    def __init__(
        self,
        api: CocApi,
        state: PollingState,
        queue: asyncio.Queue[Event],
        player_tags: list[str],
        interval: float = 120.0,
        include_fields: frozenset[str] | None = None,
        exclude_fields: frozenset[str] | None = None,
    ) -> None:
        super().__init__(api, state, queue, interval)
        self._player_tags = list(player_tags)
        self._include_fields = include_fields
        self._exclude_fields = exclude_fields

    async def _poll_once(self) -> list[Event]:
        events: list[Event] = []

        for tag in self._player_tags:
            resource_key = f"player:{tag}"
            if not self._state.should_poll(resource_key, self._interval):
                continue

            result: dict[str, Any] = await cast(
                Awaitable[dict[str, Any]], self._api.players(tag)
            )
            self._state.mark_polled(resource_key)

            if result.get("result") == "error":
                events.append(
                    Event(
                        event_type=EventType.POLL_ERROR,
                        tag=tag,
                        metadata={
                            "error": result.get("message", "Unknown"),
                            "endpoint": "players",
                        },
                    )
                )
                continue

            old = self._state.get_player(tag)
            if old is not None:
                changes = diff_dicts(
                    old,
                    result,
                    include_fields=self._include_fields,
                    exclude_fields=self._exclude_fields,
                )
                if changes:
                    events.append(
                        Event(
                            event_type=EventType.PLAYER_UPDATED,
                            tag=tag,
                            old_data=old,
                            new_data=result,
                            changes=tuple(changes),
                        )
                    )

            self._state.set_player(tag, result)

        return events
