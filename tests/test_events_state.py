"""Tests for polling state storage."""

import json
import time

from cocapi.events._state import PollingState
from cocapi.events._types import WarState


class TestPollingStateSnapshots:
    def test_clan_get_set(self):
        state = PollingState()
        assert state.get_clan("#A") is None
        state.set_clan("#A", {"tag": "#A", "name": "Test"})
        assert state.get_clan("#A")["name"] == "Test"

    def test_members_get_set(self):
        state = PollingState()
        assert state.get_members("#A") is None
        members = [{"tag": "#M1"}]
        state.set_members("#A", members)
        assert state.get_members("#A") == members

    def test_war_get_set(self):
        state = PollingState()
        assert state.get_war("#A") is None
        state.set_war("#A", {"state": "inWar"})
        assert state.get_war("#A")["state"] == "inWar"

    def test_player_get_set(self):
        state = PollingState()
        assert state.get_player("#P1") is None
        state.set_player("#P1", {"tag": "#P1", "trophies": 5000})
        assert state.get_player("#P1")["trophies"] == 5000

    def test_war_fsm_auto_created(self):
        state = PollingState()
        fsm = state.get_war_fsm("#A")
        assert fsm.state == WarState.NOT_IN_WAR
        # Same instance returned on second call
        assert state.get_war_fsm("#A") is fsm


class TestPollingStateTiming:
    def test_should_poll_first_time(self):
        state = PollingState()
        assert state.should_poll("clan:#A", 60.0) is True

    def test_should_not_poll_too_soon(self):
        state = PollingState()
        state.mark_polled("clan:#A")
        assert state.should_poll("clan:#A", 60.0) is False

    def test_should_poll_after_interval(self):
        state = PollingState()
        state._last_poll_times["clan:#A"] = time.time() - 61.0
        assert state.should_poll("clan:#A", 60.0) is True


class TestPollingStatePersistence:
    def test_save_and_load(self, tmp_path):
        state = PollingState()
        state.set_clan("#A", {"tag": "#A", "name": "TestClan"})
        state.set_members("#A", [{"tag": "#M1"}])
        state.set_war("#A", {"state": "inWar"})
        state.set_player("#P1", {"tag": "#P1"})
        fsm = state.get_war_fsm("#A")
        fsm.transition("inWar")

        path = tmp_path / "state.json"
        state.save(path)

        new_state = PollingState()
        assert new_state.load(path) is True
        assert new_state.get_clan("#A")["name"] == "TestClan"
        assert len(new_state.get_members("#A")) == 1
        assert new_state.get_war("#A")["state"] == "inWar"
        assert new_state.get_player("#P1")["tag"] == "#P1"
        assert new_state.get_war_fsm("#A").state == WarState.IN_WAR

    def test_load_missing_file(self, tmp_path):
        state = PollingState()
        assert state.load(tmp_path / "nonexistent.json") is False

    def test_load_corrupt_file(self, tmp_path):
        path = tmp_path / "corrupt.json"
        path.write_text("not valid json{{{")
        state = PollingState()
        assert state.load(path) is False

    def test_load_invalid_war_state(self, tmp_path):
        path = tmp_path / "state.json"
        data = {
            "clans": {},
            "members": {},
            "wars": {},
            "war_states": {"#A": "badState"},
            "players": {},
            "last_poll_times": {},
        }
        path.write_text(json.dumps(data))
        state = PollingState()
        assert state.load(path) is True
        assert state.get_war_fsm("#A").state == WarState.NOT_IN_WAR

    def test_save_creates_parent_dirs(self, tmp_path):
        state = PollingState()
        path = tmp_path / "sub" / "dir" / "state.json"
        state.save(path)
        assert path.exists()
