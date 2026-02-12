"""Event data model for the cocapi event polling system."""

from __future__ import annotations

import enum
import time
from dataclasses import dataclass, field
from typing import Any


class EventType(enum.Enum):
    """All event types produced by the polling system."""

    CLAN_UPDATED = "clan_updated"
    MEMBER_JOINED = "member_joined"
    MEMBER_LEFT = "member_left"
    MEMBER_UPDATED = "member_updated"
    MEMBER_ROLE_CHANGED = "member_role_changed"
    MEMBER_DONATIONS = "member_donations"
    WAR_STATE_CHANGED = "war_state_changed"
    WAR_ATTACK_NEW = "war_attack_new"
    PLAYER_UPDATED = "player_updated"
    TROOP_UPGRADED = "troop_upgraded"
    SPELL_UPGRADED = "spell_upgraded"
    HERO_UPGRADED = "hero_upgraded"
    HERO_EQUIPMENT_UPGRADED = "hero_equipment_upgraded"
    TOWNHALL_UPGRADED = "townhall_upgraded"
    BUILDERHALL_UPGRADED = "builderhall_upgraded"
    PLAYER_NAME_CHANGED = "player_name_changed"
    PLAYER_LEAGUE_CHANGED = "player_league_changed"
    PLAYER_LABEL_CHANGED = "player_label_changed"
    MAINTENANCE_START = "maintenance_start"
    MAINTENANCE_END = "maintenance_end"
    POLL_ERROR = "poll_error"


class WarState(enum.Enum):
    """War state machine states matching the CoC API."""

    NOT_IN_WAR = "notInWar"
    PREPARATION = "preparation"
    IN_WAR = "inWar"
    WAR_ENDED = "warEnded"


@dataclass(frozen=True, slots=True)
class Change:
    """A single field-level change between two snapshots."""

    field: str
    old_value: Any
    new_value: Any


@dataclass(frozen=True)
class Event:
    """An event produced by the polling system.

    Attributes:
        event_type: The type of event.
        tag: The clan or player tag this event relates to.
        timestamp: Unix timestamp when the event was created.
        old_data: Full previous snapshot (None on first poll).
        new_data: Full current snapshot (None for MEMBER_LEFT).
        changes: Tuple of field-level changes detected.
        metadata: Extra context (member_tag, war_state_from, etc.).
    """

    event_type: EventType
    tag: str
    timestamp: float = field(default_factory=time.time)
    old_data: dict[str, Any] | None = None
    new_data: dict[str, Any] | None = None
    changes: tuple[Change, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
