"""Polling state storage for the event system."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from ._types import WarState
from ._war_fsm import WarStateMachine

logger = logging.getLogger(__name__)


def _safe_resolve(path: Path) -> Path:
    """Resolve *path* to an absolute path, rejecting traversal components."""
    resolved = path.resolve()
    if ".." in resolved.parts:
        raise ValueError(f"Path traversal detected: {path}")
    return resolved


class PollingState:
    """In-memory state for polled resources with optional JSON persistence."""

    def __init__(self) -> None:
        self._clan_snapshots: dict[str, dict[str, Any]] = {}
        self._member_snapshots: dict[str, list[dict[str, Any]]] = {}
        self._war_snapshots: dict[str, dict[str, Any]] = {}
        self._war_fsms: dict[str, WarStateMachine] = {}
        self._player_snapshots: dict[str, dict[str, Any]] = {}
        self._last_poll_times: dict[str, float] = {}

    # --- Clan ---

    def get_clan(self, tag: str) -> dict[str, Any] | None:
        """Return the last-polled clan snapshot, or None if not yet polled."""
        return self._clan_snapshots.get(tag)

    def set_clan(self, tag: str, data: dict[str, Any]) -> None:
        """Store the latest clan snapshot for diffing on the next poll."""
        self._clan_snapshots[tag] = data

    # --- Members ---

    def get_members(self, tag: str) -> list[dict[str, Any]] | None:
        """Return the last-polled member list for a clan, or None."""
        return self._member_snapshots.get(tag)

    def set_members(self, tag: str, members: list[dict[str, Any]]) -> None:
        """Store the latest member list snapshot for a clan."""
        self._member_snapshots[tag] = members

    # --- War ---

    def get_war(self, tag: str) -> dict[str, Any] | None:
        """Return the last-polled war snapshot, or None if not yet polled."""
        return self._war_snapshots.get(tag)

    def set_war(self, tag: str, data: dict[str, Any]) -> None:
        """Store the latest war snapshot for diffing on the next poll."""
        self._war_snapshots[tag] = data

    def get_war_fsm(self, tag: str) -> WarStateMachine:
        """Return the war state machine for a clan, creating one if needed."""
        if tag not in self._war_fsms:
            self._war_fsms[tag] = WarStateMachine()
        return self._war_fsms[tag]

    # --- Player ---

    def get_player(self, tag: str) -> dict[str, Any] | None:
        """Return the last-polled player snapshot, or None if not yet polled."""
        return self._player_snapshots.get(tag)

    def set_player(self, tag: str, data: dict[str, Any]) -> None:
        """Store the latest player snapshot for diffing on the next poll."""
        self._player_snapshots[tag] = data

    # --- Poll timing ---

    def should_poll(self, resource_key: str, interval: float) -> bool:
        """Check if enough time has passed since the last poll."""
        last = self._last_poll_times.get(resource_key, 0.0)
        return (time.time() - last) >= interval

    def mark_polled(self, resource_key: str) -> None:
        """Record the current time as the last poll time for a resource."""
        self._last_poll_times[resource_key] = time.time()

    # --- Persistence ---

    def save(self, path: Path) -> None:
        """Persist state to JSON file for restart recovery."""
        path = _safe_resolve(path)
        data = {
            "clans": self._clan_snapshots,
            "members": self._member_snapshots,
            "wars": self._war_snapshots,
            "war_states": {t: fsm.state.value for t, fsm in self._war_fsms.items()},
            "players": self._player_snapshots,
            "last_poll_times": self._last_poll_times,
            "saved_at": time.time(),
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, default=str), encoding="utf-8")

    def load(self, path: Path) -> bool:
        """Load state from JSON file. Returns True if loaded successfully."""
        path = _safe_resolve(path)
        if not path.exists():
            return False
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            self._clan_snapshots = data.get("clans", {})
            self._member_snapshots = data.get("members", {})
            self._war_snapshots = data.get("wars", {})
            for tag, state_str in data.get("war_states", {}).items():
                try:
                    self._war_fsms[tag] = WarStateMachine(WarState(state_str))
                except ValueError:
                    self._war_fsms[tag] = WarStateMachine()
            self._player_snapshots = data.get("players", {})
            self._last_poll_times = data.get("last_poll_times", {})
            return True
        except Exception as e:
            logger.warning("Failed to load polling state: %s", e)
            return False
