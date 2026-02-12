"""Polling watchers that detect changes and produce events."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable
from typing import TYPE_CHECKING, Any, cast

from ._diff import diff_dicts, diff_member_tags, diff_named_list
from ._state import PollingState
from ._types import Change, Event, EventType

if TYPE_CHECKING:
    from cocapi import CocApi

logger = logging.getLogger(__name__)

_CLAN_EXCLUDE_FIELDS = frozenset({"memberList"})


def _poll_error(tag: str, result: dict[str, Any], endpoint: str) -> Event:
    """Create a POLL_ERROR event from an error response."""
    return Event(
        event_type=EventType.POLL_ERROR,
        tag=tag,
        metadata={
            "error": result.get("message", "Unknown"),
            "endpoint": endpoint,
        },
    )


def _member_meta(member: dict[str, Any]) -> dict[str, Any]:
    """Extract standard member metadata."""
    return {"member_tag": member.get("tag"), "member_name": member.get("name")}


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
                pass  # Expected: we just cancelled this task
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
                events.append(_poll_error(tag, result, "clan_tag"))
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
                self._diff_members(tag, result, events)

            self._state.set_clan(tag, result)
        return events

    def _diff_members(
        self,
        tag: str,
        result: dict[str, Any],
        events: list[Event],
    ) -> None:
        """Diff member lists and append join/leave/update events."""
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
                        metadata=_member_meta(m),
                    )
                )
            for m in left:
                events.append(
                    Event(
                        event_type=EventType.MEMBER_LEFT,
                        tag=tag,
                        old_data=m,
                        metadata=_member_meta(m),
                    )
                )
            for old_m, new_m in updated:
                self._diff_single_member(tag, old_m, new_m, events)

        self._state.set_members(tag, new_members)

    @staticmethod
    def _diff_single_member(
        tag: str,
        old_m: dict[str, Any],
        new_m: dict[str, Any],
        events: list[Event],
    ) -> None:
        """Diff one member and emit update / role / donation events."""
        member_changes = diff_dicts(old_m, new_m)
        if not member_changes:
            return

        m_meta = _member_meta(new_m)
        events.append(
            Event(
                event_type=EventType.MEMBER_UPDATED,
                tag=tag,
                old_data=old_m,
                new_data=new_m,
                changes=tuple(member_changes),
                metadata=m_meta,
            )
        )
        change_fields = {c.field for c in member_changes}
        if "role" in change_fields:
            events.append(
                Event(
                    event_type=EventType.MEMBER_ROLE_CHANGED,
                    tag=tag,
                    old_data=old_m,
                    new_data=new_m,
                    changes=tuple(c for c in member_changes if c.field == "role"),
                    metadata={
                        **m_meta,
                        "old_role": old_m.get("role"),
                        "new_role": new_m.get("role"),
                    },
                )
            )
        if change_fields & {"donations", "donationsReceived"}:
            events.append(
                Event(
                    event_type=EventType.MEMBER_DONATIONS,
                    tag=tag,
                    old_data=old_m,
                    new_data=new_m,
                    changes=tuple(
                        c
                        for c in member_changes
                        if c.field in ("donations", "donationsReceived")
                    ),
                    metadata={
                        **m_meta,
                        "donations": new_m.get("donations"),
                        "donationsReceived": new_m.get("donationsReceived"),
                    },
                )
            )


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
                events.append(_poll_error(tag, result, "clan_current_war"))
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
    """Polls player data and detects field changes.

    Emits granular events for upgrades (troops, spells, heroes, equipment,
    townhall, builder hall) as well as the generic ``PLAYER_UPDATED`` event
    for any other top-level field change.
    """

    # Fields that get their own event type instead of generic PLAYER_UPDATED
    _NESTED_LIST_FIELDS = frozenset({"troops", "spells", "heroes", "heroEquipment"})
    _SPECIAL_FIELDS: dict[str, EventType] = {
        "townHallLevel": EventType.TOWNHALL_UPGRADED,
        "builderHallLevel": EventType.BUILDERHALL_UPGRADED,
        "name": EventType.PLAYER_NAME_CHANGED,
        "league": EventType.PLAYER_LEAGUE_CHANGED,
        "labels": EventType.PLAYER_LABEL_CHANGED,
    }
    _LIST_EVENT_MAP: dict[str, EventType] = {
        "troops": EventType.TROOP_UPGRADED,
        "spells": EventType.SPELL_UPGRADED,
        "heroes": EventType.HERO_UPGRADED,
        "heroEquipment": EventType.HERO_EQUIPMENT_UPGRADED,
    }

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

    def _field_enabled(self, field: str) -> bool:
        """Check if a field passes include/exclude filters."""
        if self._include_fields is not None and field not in self._include_fields:
            return False
        if self._exclude_fields is not None and field in self._exclude_fields:
            return False
        return True

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
                events.append(_poll_error(tag, result, "players"))
                continue

            old = self._state.get_player(tag)
            if old is not None:
                self._diff_player(tag, old, result, events)

            self._state.set_player(tag, result)
        return events

    def _diff_player(
        self,
        tag: str,
        old: dict[str, Any],
        new: dict[str, Any],
        events: list[Event],
    ) -> None:
        """Diff old vs new player data and append events."""
        generic_changes = diff_dicts(
            old,
            new,
            include_fields=self._include_fields,
            exclude_fields=self._generic_exclude(),
        )
        self._emit_special_field_events(tag, old, new, generic_changes, events)
        if generic_changes:
            events.append(
                Event(
                    event_type=EventType.PLAYER_UPDATED,
                    tag=tag,
                    old_data=old,
                    new_data=new,
                    changes=tuple(generic_changes),
                )
            )
        self._diff_nested_lists(tag, old, new, events)

    def _generic_exclude(self) -> frozenset[str]:
        """Build the exclude set for the top-level diff."""
        base = self._exclude_fields or frozenset()
        if self._include_fields is not None:
            return base | (self._NESTED_LIST_FIELDS - self._include_fields)
        return base | self._NESTED_LIST_FIELDS

    def _emit_special_field_events(
        self,
        tag: str,
        old: dict[str, Any],
        new: dict[str, Any],
        changes: list[Change],
        events: list[Event],
    ) -> None:
        """Emit typed events for special top-level fields."""
        for change in changes:
            if change.field in self._SPECIAL_FIELDS:
                events.append(
                    Event(
                        event_type=self._SPECIAL_FIELDS[change.field],
                        tag=tag,
                        old_data=old,
                        new_data=new,
                        changes=(change,),
                        metadata={
                            "old_value": change.old_value,
                            "new_value": change.new_value,
                        },
                    )
                )

    def _diff_nested_lists(
        self,
        tag: str,
        old: dict[str, Any],
        new: dict[str, Any],
        events: list[Event],
    ) -> None:
        """Diff nested lists (troops, spells, heroes, equipment)."""
        for list_field, event_type in self._LIST_EVENT_MAP.items():
            if not self._field_enabled(list_field):
                continue
            upgraded = diff_named_list(old.get(list_field, []), new.get(list_field, []))
            for name, old_level, new_level in upgraded:
                events.append(
                    Event(
                        event_type=event_type,
                        tag=tag,
                        changes=(
                            Change(
                                field=name, old_value=old_level, new_value=new_level
                            ),
                        ),
                        metadata={
                            "name": name,
                            "old_level": old_level,
                            "new_level": new_level,
                        },
                    )
                )


class MaintenanceWatcher(BaseWatcher):
    """Detects API maintenance windows by polling a known endpoint.

    Emits ``MAINTENANCE_START`` when the API starts returning errors
    (HTTP 503 or connection failures) and ``MAINTENANCE_END`` when it
    recovers.  Uses a configurable probe tag (defaults to a well-known
    player ``#JY9J2Y99``).
    """

    def __init__(
        self,
        api: CocApi,
        state: PollingState,
        queue: asyncio.Queue[Event],
        interval: float = 30.0,
        probe_tag: str = "#JY9J2Y99",
    ) -> None:
        super().__init__(api, state, queue, interval)
        self._probe_tag = probe_tag
        self._in_maintenance = False
        self._maintenance_start_time: float | None = None

    async def _poll_once(self) -> list[Event]:
        result: dict[str, Any] = await cast(
            Awaitable[dict[str, Any]], self._api.players(self._probe_tag)
        )

        is_error = result.get("result") == "error" and result.get("status_code") == 503

        events: list[Event] = []

        if is_error and not self._in_maintenance:
            self._in_maintenance = True
            self._maintenance_start_time = time.time()
            events.append(
                Event(
                    event_type=EventType.MAINTENANCE_START,
                    tag="",
                    metadata={
                        "message": result.get("message", "Service Unavailable"),
                    },
                )
            )
        elif not is_error and self._in_maintenance:
            self._in_maintenance = False
            duration = (
                time.time() - self._maintenance_start_time
                if self._maintenance_start_time is not None
                else 0.0
            )
            self._maintenance_start_time = None
            events.append(
                Event(
                    event_type=EventType.MAINTENANCE_END,
                    tag="",
                    metadata={
                        "duration_seconds": round(duration, 1),
                    },
                )
            )

        return events
