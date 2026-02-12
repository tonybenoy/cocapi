"""War state machine for tracking war transitions."""

from __future__ import annotations

from ._types import WarState


class WarStateMachine:
    """Tracks war state transitions for a single clan.

    The CoC API returns war state as a string in ``clan_current_war()``.
    This FSM detects when the state actually changes (vs. the same state
    being reported on consecutive polls).
    """

    def __init__(self, initial_state: WarState = WarState.NOT_IN_WAR) -> None:
        self.state = initial_state

    def transition(self, raw_state: str) -> WarState | None:
        """Attempt a state transition.

        Args:
            raw_state: The ``state`` field from ``clan_current_war()`` response.

        Returns:
            The new WarState if a transition occurred, or None if the state
            is unchanged or the raw_state is unrecognized.
        """
        try:
            new_state = WarState(raw_state)
        except ValueError:
            return None

        if new_state == self.state:
            return None

        self.state = new_state
        return new_state
