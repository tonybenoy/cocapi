"""Tests for the war state machine."""

from cocapi.events._types import WarState
from cocapi.events._war_fsm import WarStateMachine


class TestWarStateMachine:
    def test_initial_state(self):
        fsm = WarStateMachine()
        assert fsm.state == WarState.NOT_IN_WAR

    def test_custom_initial_state(self):
        fsm = WarStateMachine(WarState.IN_WAR)
        assert fsm.state == WarState.IN_WAR

    def test_transition_to_preparation(self):
        fsm = WarStateMachine()
        result = fsm.transition("preparation")
        assert result == WarState.PREPARATION
        assert fsm.state == WarState.PREPARATION

    def test_no_transition_same_state(self):
        fsm = WarStateMachine(WarState.IN_WAR)
        result = fsm.transition("inWar")
        assert result is None
        assert fsm.state == WarState.IN_WAR

    def test_full_war_cycle(self):
        fsm = WarStateMachine()

        result = fsm.transition("preparation")
        assert result == WarState.PREPARATION

        result = fsm.transition("inWar")
        assert result == WarState.IN_WAR

        result = fsm.transition("warEnded")
        assert result == WarState.WAR_ENDED

        result = fsm.transition("notInWar")
        assert result == WarState.NOT_IN_WAR

    def test_skip_state(self):
        """Poll intervals may be long enough to skip intermediate states."""
        fsm = WarStateMachine()
        result = fsm.transition("inWar")
        assert result == WarState.IN_WAR

    def test_unrecognized_state(self):
        fsm = WarStateMachine()
        result = fsm.transition("unknownState")
        assert result is None
        assert fsm.state == WarState.NOT_IN_WAR

    def test_empty_string(self):
        fsm = WarStateMachine()
        result = fsm.transition("")
        assert result is None

    def test_consecutive_same_state(self):
        fsm = WarStateMachine()
        fsm.transition("preparation")
        assert fsm.transition("preparation") is None
        assert fsm.transition("preparation") is None
        assert fsm.state == WarState.PREPARATION
