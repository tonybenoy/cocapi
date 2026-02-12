"""Tests for event watchers."""

import asyncio

import pytest
from unittest.mock import AsyncMock, patch

from cocapi import CocApi
from cocapi.events._state import PollingState
from cocapi.events._types import Event, EventType
from cocapi.events._watchers import (
    ClanWatcher,
    MaintenanceWatcher,
    PlayerWatcher,
    WarWatcher,
)


@pytest.fixture()
def api():
    with patch.object(CocApi, "test", return_value={"result": "success"}):
        api = CocApi("fake_token")
        api.async_mode = True
        return api


@pytest.fixture()
def state():
    return PollingState()


@pytest.fixture()
def queue():
    return asyncio.Queue()


# ---------------------------------------------------------------------------
# ClanWatcher
# ---------------------------------------------------------------------------


class TestClanWatcher:
    @pytest.mark.asyncio
    async def test_first_poll_no_diff_events(self, api, state, queue):
        clan_data = {
            "tag": "#A",
            "name": "TestClan",
            "clanLevel": 10,
            "memberList": [{"tag": "#M1", "name": "Alice"}],
        }
        api.clan_tag = AsyncMock(return_value=clan_data)

        watcher = ClanWatcher(api, state, queue, ["#A"], interval=1.0)
        events = await watcher._poll_once()

        assert len(events) == 0
        assert state.get_clan("#A") is not None

    @pytest.mark.asyncio
    async def test_clan_level_change(self, api, state, queue):
        old = {"tag": "#A", "name": "Test", "clanLevel": 10, "memberList": []}
        new = {"tag": "#A", "name": "Test", "clanLevel": 11, "memberList": []}

        state.set_clan("#A", old)
        state.set_members("#A", [])
        api.clan_tag = AsyncMock(return_value=new)

        watcher = ClanWatcher(api, state, queue, ["#A"], interval=1.0)
        events = await watcher._poll_once()

        clan_events = [e for e in events if e.event_type == EventType.CLAN_UPDATED]
        assert len(clan_events) == 1
        changes = {c.field: (c.old_value, c.new_value) for c in clan_events[0].changes}
        assert changes["clanLevel"] == (10, 11)

    @pytest.mark.asyncio
    async def test_member_join(self, api, state, queue):
        old_data = {"tag": "#A", "name": "Test", "memberList": [{"tag": "#M1", "name": "Alice"}]}
        new_data = {
            "tag": "#A",
            "name": "Test",
            "memberList": [
                {"tag": "#M1", "name": "Alice"},
                {"tag": "#M2", "name": "Bob"},
            ],
        }
        state.set_clan("#A", old_data)
        state.set_members("#A", old_data["memberList"])
        api.clan_tag = AsyncMock(return_value=new_data)

        watcher = ClanWatcher(api, state, queue, ["#A"], interval=1.0)
        events = await watcher._poll_once()

        joins = [e for e in events if e.event_type == EventType.MEMBER_JOINED]
        assert len(joins) == 1
        assert joins[0].metadata["member_tag"] == "#M2"

    @pytest.mark.asyncio
    async def test_member_leave(self, api, state, queue):
        old_data = {
            "tag": "#A",
            "name": "Test",
            "memberList": [
                {"tag": "#M1", "name": "Alice"},
                {"tag": "#M2", "name": "Bob"},
            ],
        }
        new_data = {"tag": "#A", "name": "Test", "memberList": [{"tag": "#M1", "name": "Alice"}]}
        state.set_clan("#A", old_data)
        state.set_members("#A", old_data["memberList"])
        api.clan_tag = AsyncMock(return_value=new_data)

        watcher = ClanWatcher(api, state, queue, ["#A"], interval=1.0)
        events = await watcher._poll_once()

        leaves = [e for e in events if e.event_type == EventType.MEMBER_LEFT]
        assert len(leaves) == 1
        assert leaves[0].metadata["member_tag"] == "#M2"

    @pytest.mark.asyncio
    async def test_member_update(self, api, state, queue):
        old_data = {
            "tag": "#A",
            "name": "Test",
            "memberList": [{"tag": "#M1", "name": "Alice", "trophies": 100}],
        }
        new_data = {
            "tag": "#A",
            "name": "Test",
            "memberList": [{"tag": "#M1", "name": "Alice", "trophies": 200}],
        }
        state.set_clan("#A", old_data)
        state.set_members("#A", old_data["memberList"])
        api.clan_tag = AsyncMock(return_value=new_data)

        watcher = ClanWatcher(api, state, queue, ["#A"], interval=1.0)
        events = await watcher._poll_once()

        updates = [e for e in events if e.event_type == EventType.MEMBER_UPDATED]
        assert len(updates) == 1
        assert updates[0].metadata["member_tag"] == "#M1"

    @pytest.mark.asyncio
    async def test_api_error(self, api, state, queue):
        api.clan_tag = AsyncMock(
            return_value={"result": "error", "message": "Not found"}
        )

        watcher = ClanWatcher(api, state, queue, ["#A"], interval=1.0)
        events = await watcher._poll_once()

        assert len(events) == 1
        assert events[0].event_type == EventType.POLL_ERROR
        assert events[0].tag == "#A"

    @pytest.mark.asyncio
    async def test_no_member_tracking(self, api, state, queue):
        data = {"tag": "#A", "name": "Test", "memberList": [{"tag": "#M1"}]}
        state.set_clan("#A", data)
        api.clan_tag = AsyncMock(return_value=data)

        watcher = ClanWatcher(
            api, state, queue, ["#A"], interval=1.0, track_members=False
        )
        events = await watcher._poll_once()
        assert len(events) == 0
        assert state.get_members("#A") is None

    @pytest.mark.asyncio
    async def test_member_role_changed(self, api, state, queue):
        old_data = {
            "tag": "#A",
            "name": "Test",
            "memberList": [{"tag": "#M1", "name": "Alice", "role": "member"}],
        }
        new_data = {
            "tag": "#A",
            "name": "Test",
            "memberList": [{"tag": "#M1", "name": "Alice", "role": "elder"}],
        }
        state.set_clan("#A", old_data)
        state.set_members("#A", old_data["memberList"])
        api.clan_tag = AsyncMock(return_value=new_data)

        watcher = ClanWatcher(api, state, queue, ["#A"], interval=1.0)
        events = await watcher._poll_once()

        role_events = [e for e in events if e.event_type == EventType.MEMBER_ROLE_CHANGED]
        assert len(role_events) == 1
        assert role_events[0].metadata["old_role"] == "member"
        assert role_events[0].metadata["new_role"] == "elder"
        # Should also have MEMBER_UPDATED
        assert any(e.event_type == EventType.MEMBER_UPDATED for e in events)

    @pytest.mark.asyncio
    async def test_member_donations_changed(self, api, state, queue):
        old_data = {
            "tag": "#A",
            "name": "Test",
            "memberList": [{"tag": "#M1", "name": "Alice", "donations": 50}],
        }
        new_data = {
            "tag": "#A",
            "name": "Test",
            "memberList": [{"tag": "#M1", "name": "Alice", "donations": 100}],
        }
        state.set_clan("#A", old_data)
        state.set_members("#A", old_data["memberList"])
        api.clan_tag = AsyncMock(return_value=new_data)

        watcher = ClanWatcher(api, state, queue, ["#A"], interval=1.0)
        events = await watcher._poll_once()

        don_events = [e for e in events if e.event_type == EventType.MEMBER_DONATIONS]
        assert len(don_events) == 1
        assert don_events[0].metadata["donations"] == 100
        assert any(e.event_type == EventType.MEMBER_UPDATED for e in events)


# ---------------------------------------------------------------------------
# WarWatcher
# ---------------------------------------------------------------------------


class TestWarWatcher:
    @pytest.mark.asyncio
    async def test_war_state_transition(self, api, state, queue):
        state.set_war("#A", {"state": "notInWar"})
        api.clan_current_war = AsyncMock(
            return_value={"state": "preparation", "teamSize": 15}
        )

        watcher = WarWatcher(api, state, queue, ["#A"], interval=1.0)
        events = await watcher._poll_once()

        state_events = [e for e in events if e.event_type == EventType.WAR_STATE_CHANGED]
        assert len(state_events) == 1
        assert state_events[0].metadata["war_state_from"] == "notInWar"
        assert state_events[0].metadata["war_state_to"] == "preparation"

    @pytest.mark.asyncio
    async def test_no_event_same_state(self, api, state, queue):
        state.set_war("#A", {"state": "inWar"})
        fsm = state.get_war_fsm("#A")
        fsm.transition("inWar")

        api.clan_current_war = AsyncMock(return_value={"state": "inWar"})

        watcher = WarWatcher(api, state, queue, ["#A"], interval=1.0)
        events = await watcher._poll_once()

        state_events = [e for e in events if e.event_type == EventType.WAR_STATE_CHANGED]
        assert len(state_events) == 0

    @pytest.mark.asyncio
    async def test_new_attack_detected(self, api, state, queue):
        old_war = {
            "state": "inWar",
            "clan": {
                "members": [
                    {"tag": "#P1", "attacks": [{"attackerTag": "#P1", "order": 1, "stars": 2, "defenderTag": "#D1"}]}
                ],
            },
            "opponent": {"members": []},
        }
        new_war = {
            "state": "inWar",
            "clan": {
                "members": [
                    {
                        "tag": "#P1",
                        "attacks": [
                            {"attackerTag": "#P1", "order": 1, "stars": 2, "defenderTag": "#D1"},
                            {"attackerTag": "#P1", "order": 2, "stars": 3, "defenderTag": "#D2"},
                        ],
                    }
                ],
            },
            "opponent": {"members": []},
        }
        state.set_war("#A", old_war)
        fsm = state.get_war_fsm("#A")
        fsm.transition("inWar")
        api.clan_current_war = AsyncMock(return_value=new_war)

        watcher = WarWatcher(api, state, queue, ["#A"], interval=1.0)
        events = await watcher._poll_once()

        attacks = [e for e in events if e.event_type == EventType.WAR_ATTACK_NEW]
        assert len(attacks) == 1
        assert attacks[0].metadata["stars"] == 3

    @pytest.mark.asyncio
    async def test_war_api_error(self, api, state, queue):
        api.clan_current_war = AsyncMock(
            return_value={"result": "error", "message": "Access denied"}
        )

        watcher = WarWatcher(api, state, queue, ["#A"], interval=1.0)
        events = await watcher._poll_once()

        assert len(events) == 1
        assert events[0].event_type == EventType.POLL_ERROR


# ---------------------------------------------------------------------------
# PlayerWatcher
# ---------------------------------------------------------------------------


class TestPlayerWatcher:
    @pytest.mark.asyncio
    async def test_first_poll_no_events(self, api, state, queue):
        api.players = AsyncMock(return_value={"tag": "#P1", "trophies": 5000})

        watcher = PlayerWatcher(api, state, queue, ["#P1"], interval=1.0)
        events = await watcher._poll_once()

        assert len(events) == 0
        assert state.get_player("#P1") is not None

    @pytest.mark.asyncio
    async def test_player_change(self, api, state, queue):
        state.set_player("#P1", {"tag": "#P1", "trophies": 5000, "name": "Alice"})
        api.players = AsyncMock(
            return_value={"tag": "#P1", "trophies": 5100, "name": "Alice"}
        )

        watcher = PlayerWatcher(api, state, queue, ["#P1"], interval=1.0)
        events = await watcher._poll_once()

        assert len(events) == 1
        assert events[0].event_type == EventType.PLAYER_UPDATED
        changes = {c.field: c.new_value for c in events[0].changes}
        assert changes["trophies"] == 5100

    @pytest.mark.asyncio
    async def test_include_fields(self, api, state, queue):
        state.set_player("#P1", {"tag": "#P1", "trophies": 5000, "donations": 100})
        api.players = AsyncMock(
            return_value={"tag": "#P1", "trophies": 5100, "donations": 200}
        )

        watcher = PlayerWatcher(
            api, state, queue, ["#P1"],
            interval=1.0,
            include_fields=frozenset({"trophies"}),
        )
        events = await watcher._poll_once()

        assert len(events) == 1
        fields = {c.field for c in events[0].changes}
        assert fields == {"trophies"}

    @pytest.mark.asyncio
    async def test_exclude_fields(self, api, state, queue):
        state.set_player("#P1", {"tag": "#P1", "trophies": 5000, "donations": 100})
        api.players = AsyncMock(
            return_value={"tag": "#P1", "trophies": 5100, "donations": 200}
        )

        watcher = PlayerWatcher(
            api, state, queue, ["#P1"],
            interval=1.0,
            exclude_fields=frozenset({"donations"}),
        )
        events = await watcher._poll_once()

        assert len(events) == 1
        fields = {c.field for c in events[0].changes}
        assert fields == {"trophies"}

    @pytest.mark.asyncio
    async def test_player_api_error(self, api, state, queue):
        api.players = AsyncMock(
            return_value={"result": "error", "message": "Not found"}
        )

        watcher = PlayerWatcher(api, state, queue, ["#P1"], interval=1.0)
        events = await watcher._poll_once()

        assert len(events) == 1
        assert events[0].event_type == EventType.POLL_ERROR

    @pytest.mark.asyncio
    async def test_troop_upgraded(self, api, state, queue):
        old = {
            "tag": "#P1",
            "troops": [{"name": "Barbarian", "level": 10, "village": "home"}],
        }
        new = {
            "tag": "#P1",
            "troops": [{"name": "Barbarian", "level": 11, "village": "home"}],
        }
        state.set_player("#P1", old)
        api.players = AsyncMock(return_value=new)

        watcher = PlayerWatcher(api, state, queue, ["#P1"], interval=1.0)
        events = await watcher._poll_once()

        troop_events = [e for e in events if e.event_type == EventType.TROOP_UPGRADED]
        assert len(troop_events) == 1
        assert troop_events[0].metadata["name"] == "Barbarian"
        assert troop_events[0].metadata["old_level"] == 10
        assert troop_events[0].metadata["new_level"] == 11

    @pytest.mark.asyncio
    async def test_spell_upgraded(self, api, state, queue):
        old = {
            "tag": "#P1",
            "spells": [{"name": "Lightning Spell", "level": 9}],
        }
        new = {
            "tag": "#P1",
            "spells": [{"name": "Lightning Spell", "level": 10}],
        }
        state.set_player("#P1", old)
        api.players = AsyncMock(return_value=new)

        watcher = PlayerWatcher(api, state, queue, ["#P1"], interval=1.0)
        events = await watcher._poll_once()

        spell_events = [e for e in events if e.event_type == EventType.SPELL_UPGRADED]
        assert len(spell_events) == 1
        assert spell_events[0].metadata["name"] == "Lightning Spell"

    @pytest.mark.asyncio
    async def test_hero_upgraded(self, api, state, queue):
        old = {
            "tag": "#P1",
            "heroes": [{"name": "Barbarian King", "level": 80}],
        }
        new = {
            "tag": "#P1",
            "heroes": [{"name": "Barbarian King", "level": 81}],
        }
        state.set_player("#P1", old)
        api.players = AsyncMock(return_value=new)

        watcher = PlayerWatcher(api, state, queue, ["#P1"], interval=1.0)
        events = await watcher._poll_once()

        hero_events = [e for e in events if e.event_type == EventType.HERO_UPGRADED]
        assert len(hero_events) == 1
        assert hero_events[0].metadata["name"] == "Barbarian King"
        assert hero_events[0].metadata["old_level"] == 80
        assert hero_events[0].metadata["new_level"] == 81

    @pytest.mark.asyncio
    async def test_hero_equipment_upgraded(self, api, state, queue):
        old = {
            "tag": "#P1",
            "heroEquipment": [{"name": "Giant Gauntlet", "level": 15}],
        }
        new = {
            "tag": "#P1",
            "heroEquipment": [{"name": "Giant Gauntlet", "level": 16}],
        }
        state.set_player("#P1", old)
        api.players = AsyncMock(return_value=new)

        watcher = PlayerWatcher(api, state, queue, ["#P1"], interval=1.0)
        events = await watcher._poll_once()

        equip_events = [
            e for e in events if e.event_type == EventType.HERO_EQUIPMENT_UPGRADED
        ]
        assert len(equip_events) == 1
        assert equip_events[0].metadata["name"] == "Giant Gauntlet"

    @pytest.mark.asyncio
    async def test_townhall_upgraded(self, api, state, queue):
        old = {"tag": "#P1", "townHallLevel": 14, "name": "Alice"}
        new = {"tag": "#P1", "townHallLevel": 15, "name": "Alice"}
        state.set_player("#P1", old)
        api.players = AsyncMock(return_value=new)

        watcher = PlayerWatcher(api, state, queue, ["#P1"], interval=1.0)
        events = await watcher._poll_once()

        th_events = [e for e in events if e.event_type == EventType.TOWNHALL_UPGRADED]
        assert len(th_events) == 1
        assert th_events[0].metadata["old_value"] == 14
        assert th_events[0].metadata["new_value"] == 15
        # Should also have PLAYER_UPDATED
        assert any(e.event_type == EventType.PLAYER_UPDATED for e in events)

    @pytest.mark.asyncio
    async def test_player_name_changed(self, api, state, queue):
        old = {"tag": "#P1", "name": "OldName"}
        new = {"tag": "#P1", "name": "NewName"}
        state.set_player("#P1", old)
        api.players = AsyncMock(return_value=new)

        watcher = PlayerWatcher(api, state, queue, ["#P1"], interval=1.0)
        events = await watcher._poll_once()

        name_events = [e for e in events if e.event_type == EventType.PLAYER_NAME_CHANGED]
        assert len(name_events) == 1
        assert name_events[0].metadata["old_value"] == "OldName"
        assert name_events[0].metadata["new_value"] == "NewName"

    @pytest.mark.asyncio
    async def test_league_changed(self, api, state, queue):
        old = {"tag": "#P1", "league": {"id": 1, "name": "Silver I"}}
        new = {"tag": "#P1", "league": {"id": 2, "name": "Gold III"}}
        state.set_player("#P1", old)
        api.players = AsyncMock(return_value=new)

        watcher = PlayerWatcher(api, state, queue, ["#P1"], interval=1.0)
        events = await watcher._poll_once()

        league_events = [
            e for e in events if e.event_type == EventType.PLAYER_LEAGUE_CHANGED
        ]
        assert len(league_events) == 1

    @pytest.mark.asyncio
    async def test_label_changed(self, api, state, queue):
        old = {"tag": "#P1", "labels": [{"id": 1, "name": "Farming"}]}
        new = {"tag": "#P1", "labels": [{"id": 2, "name": "Clan Wars"}]}
        state.set_player("#P1", old)
        api.players = AsyncMock(return_value=new)

        watcher = PlayerWatcher(api, state, queue, ["#P1"], interval=1.0)
        events = await watcher._poll_once()

        label_events = [
            e for e in events if e.event_type == EventType.PLAYER_LABEL_CHANGED
        ]
        assert len(label_events) == 1

    @pytest.mark.asyncio
    async def test_troop_excluded_by_filter(self, api, state, queue):
        old = {
            "tag": "#P1",
            "troops": [{"name": "Barbarian", "level": 10}],
            "trophies": 5000,
        }
        new = {
            "tag": "#P1",
            "troops": [{"name": "Barbarian", "level": 11}],
            "trophies": 5100,
        }
        state.set_player("#P1", old)
        api.players = AsyncMock(return_value=new)

        watcher = PlayerWatcher(
            api, state, queue, ["#P1"],
            interval=1.0,
            exclude_fields=frozenset({"troops"}),
        )
        events = await watcher._poll_once()

        # Should NOT have troop events
        troop_events = [e for e in events if e.event_type == EventType.TROOP_UPGRADED]
        assert len(troop_events) == 0
        # Should still have PLAYER_UPDATED for trophies
        assert any(e.event_type == EventType.PLAYER_UPDATED for e in events)

    @pytest.mark.asyncio
    async def test_multiple_upgrades_same_poll(self, api, state, queue):
        old = {
            "tag": "#P1",
            "troops": [
                {"name": "Barbarian", "level": 10},
                {"name": "Archer", "level": 9},
            ],
            "heroes": [{"name": "Barbarian King", "level": 80}],
            "townHallLevel": 14,
        }
        new = {
            "tag": "#P1",
            "troops": [
                {"name": "Barbarian", "level": 11},
                {"name": "Archer", "level": 9},
            ],
            "heroes": [{"name": "Barbarian King", "level": 81}],
            "townHallLevel": 15,
        }
        state.set_player("#P1", old)
        api.players = AsyncMock(return_value=new)

        watcher = PlayerWatcher(api, state, queue, ["#P1"], interval=1.0)
        events = await watcher._poll_once()

        types = [e.event_type for e in events]
        assert EventType.TOWNHALL_UPGRADED in types
        assert EventType.TROOP_UPGRADED in types
        assert EventType.HERO_UPGRADED in types
        assert EventType.PLAYER_UPDATED in types


# ---------------------------------------------------------------------------
# MaintenanceWatcher
# ---------------------------------------------------------------------------


class TestMaintenanceWatcher:
    @pytest.mark.asyncio
    async def test_no_event_when_api_healthy(self, api, state, queue):
        api.players = AsyncMock(return_value={"tag": "#JY9J2Y99", "name": "Probe"})

        watcher = MaintenanceWatcher(api, state, queue, interval=1.0)
        events = await watcher._poll_once()

        assert len(events) == 0
        assert not watcher._in_maintenance

    @pytest.mark.asyncio
    async def test_maintenance_start_on_503(self, api, state, queue):
        api.players = AsyncMock(
            return_value={
                "result": "error",
                "message": "Service Unavailable",
                "status_code": 503,
            }
        )

        watcher = MaintenanceWatcher(api, state, queue, interval=1.0)
        events = await watcher._poll_once()

        assert len(events) == 1
        assert events[0].event_type == EventType.MAINTENANCE_START
        assert watcher._in_maintenance

    @pytest.mark.asyncio
    async def test_no_duplicate_maintenance_start(self, api, state, queue):
        api.players = AsyncMock(
            return_value={
                "result": "error",
                "message": "Service Unavailable",
                "status_code": 503,
            }
        )

        watcher = MaintenanceWatcher(api, state, queue, interval=1.0)
        await watcher._poll_once()  # triggers MAINTENANCE_START
        events = await watcher._poll_once()  # still 503, no new event

        assert len(events) == 0

    @pytest.mark.asyncio
    async def test_maintenance_end_on_recovery(self, api, state, queue):
        # Start in maintenance
        api.players = AsyncMock(
            return_value={
                "result": "error",
                "message": "Service Unavailable",
                "status_code": 503,
            }
        )
        watcher = MaintenanceWatcher(api, state, queue, interval=1.0)
        await watcher._poll_once()

        # API recovers
        api.players = AsyncMock(return_value={"tag": "#JY9J2Y99", "name": "Probe"})
        events = await watcher._poll_once()

        assert len(events) == 1
        assert events[0].event_type == EventType.MAINTENANCE_END
        assert "duration_seconds" in events[0].metadata
        assert not watcher._in_maintenance

    @pytest.mark.asyncio
    async def test_non_503_error_not_maintenance(self, api, state, queue):
        api.players = AsyncMock(
            return_value={
                "result": "error",
                "message": "Not found",
                "status_code": 404,
            }
        )

        watcher = MaintenanceWatcher(api, state, queue, interval=1.0)
        events = await watcher._poll_once()

        assert len(events) == 0
        assert not watcher._in_maintenance

    @pytest.mark.asyncio
    async def test_custom_probe_tag(self, api, state, queue):
        api.players = AsyncMock(return_value={"tag": "#CUSTOM", "name": "Test"})

        watcher = MaintenanceWatcher(
            api, state, queue, interval=1.0, probe_tag="#CUSTOM"
        )
        await watcher._poll_once()

        api.players.assert_called_once_with("#CUSTOM")
