"""
Tests for the cocapi CLI.
"""

import json
import os

import pytest
from unittest.mock import patch

from cocapi import CocApi

# Only run CLI tests if typer is installed
typer = pytest.importorskip("typer")
from typer.testing import CliRunner

from cocapi.cli import app

runner = CliRunner()

FAKE_TOKEN = "fake_test_token"


@pytest.fixture(autouse=True)
def _mock_api_init():
    with patch.object(CocApi, "test", return_value={"result": "success"}):
        yield


# ---------------------------------------------------------------------------
# Clan
# ---------------------------------------------------------------------------


class TestClanCommand:
    def test_clan_json(self):
        data = {"tag": "#2PP", "name": "Test Clan", "clanLevel": 10}
        with patch.object(CocApi, "clan_tag", return_value=data):
            result = runner.invoke(app, ["clan", "#2PP", "-t", FAKE_TOKEN, "--json"])
        assert result.exit_code == 0
        assert json.loads(result.output) == data

    def test_clan_formatted(self):
        data = {"tag": "#2PP", "name": "Test Clan", "clanLevel": 10}
        with patch.object(CocApi, "clan_tag", return_value=data):
            result = runner.invoke(app, ["clan", "#2PP", "-t", FAKE_TOKEN])
        assert result.exit_code == 0
        assert "name: Test Clan" in result.output

    def test_clan_error(self):
        data = {"result": "error", "message": "Not found"}
        with patch.object(CocApi, "clan_tag", return_value=data):
            result = runner.invoke(app, ["clan", "#BAD", "-t", FAKE_TOKEN])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# Player
# ---------------------------------------------------------------------------


class TestPlayerCommand:
    def test_player_json(self):
        data = {"tag": "#P1", "name": "Player1", "trophies": 5000}
        with patch.object(CocApi, "players", return_value=data):
            result = runner.invoke(app, ["player", "#P1", "-t", FAKE_TOKEN, "--json"])
        assert result.exit_code == 0
        assert json.loads(result.output)["trophies"] == 5000


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------


class TestMembersCommand:
    def test_members_json(self):
        data = {"items": [{"tag": "#M1", "name": "A"}], "paging": {"cursors": {}}}
        with patch.object(CocApi, "clan_members", return_value=data):
            result = runner.invoke(
                app, ["members", "#CLAN", "-t", FAKE_TOKEN, "--json"]
            )
        assert result.exit_code == 0
        assert len(json.loads(result.output)["items"]) == 1

    def test_members_formatted(self):
        data = {"items": [{"tag": "#M1", "name": "Alice", "trophies": 3000}], "paging": {"cursors": {}}}
        with patch.object(CocApi, "clan_members", return_value=data):
            result = runner.invoke(app, ["members", "#CLAN", "-t", FAKE_TOKEN])
        assert result.exit_code == 0
        assert "tag=#M1" in result.output


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


class TestSearchCommand:
    def test_search_json(self):
        data = {"items": [{"tag": "#C1", "name": "Clan1"}], "paging": {"cursors": {}}}
        with patch.object(CocApi, "clan", return_value=data):
            result = runner.invoke(
                app, ["search", "clash", "-t", FAKE_TOKEN, "--json"]
            )
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Token from env
# ---------------------------------------------------------------------------


class TestTokenFromEnv:
    def test_env_var(self):
        data = {"startTime": "2025-01-01T00:00:00.000Z", "endTime": "2025-02-01T00:00:00.000Z"}
        with patch.object(CocApi, "goldpass", return_value=data):
            result = runner.invoke(
                app, ["goldpass", "--json"], env={"COCAPI_TOKEN": FAKE_TOKEN}
            )
        assert result.exit_code == 0

    def test_no_token_fails(self):
        env = {k: v for k, v in os.environ.items() if k != "COCAPI_TOKEN"}
        with patch("cocapi.cli._load_cached_keys", return_value=None):
            result = runner.invoke(app, ["goldpass"], env=env)
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# Leagues, goldpass, locations
# ---------------------------------------------------------------------------


class TestSimpleCommands:
    def test_leagues(self):
        data = {"items": [{"id": 1, "name": "Legend"}], "paging": {"cursors": {}}}
        with patch.object(CocApi, "league", return_value=data):
            result = runner.invoke(app, ["leagues", "-t", FAKE_TOKEN, "--json"])
        assert result.exit_code == 0

    def test_goldpass(self):
        data = {"startTime": "2025-01-01", "endTime": "2025-02-01"}
        with patch.object(CocApi, "goldpass", return_value=data):
            result = runner.invoke(app, ["goldpass", "-t", FAKE_TOKEN, "--json"])
        assert result.exit_code == 0

    def test_locations(self):
        data = {"items": [{"id": 32000006, "name": "International"}], "paging": {"cursors": {}}}
        with patch.object(CocApi, "location", return_value=data):
            result = runner.invoke(
                app, ["locations", "-t", FAKE_TOKEN, "--json"]
            )
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Warlog
# ---------------------------------------------------------------------------


class TestWarlogCommand:
    def test_warlog_json(self):
        data = {"items": [{"result": "win", "endTime": "2025-01-01"}], "paging": {"cursors": {}}}
        with patch.object(CocApi, "clan_war_log", return_value=data):
            result = runner.invoke(app, ["warlog", "#CLAN", "-t", FAKE_TOKEN, "--json"])
        assert result.exit_code == 0
        assert "items" in json.loads(result.output)


# ---------------------------------------------------------------------------
# CWL
# ---------------------------------------------------------------------------


class TestCwlCommand:
    def test_cwl_json(self):
        data = {"state": "inWar", "season": "2025-01", "clans": []}
        with patch.object(CocApi, "clan_leaguegroup", return_value=data):
            result = runner.invoke(app, ["cwl", "#CLAN", "-t", FAKE_TOKEN, "--json"])
        assert result.exit_code == 0
        assert json.loads(result.output)["state"] == "inWar"


# ---------------------------------------------------------------------------
# Raids
# ---------------------------------------------------------------------------


class TestRaidsCommand:
    def test_raids_json(self):
        data = {"items": [{"state": "ended"}], "paging": {"cursors": {}}}
        with patch.object(CocApi, "clan_capitalraidseasons", return_value=data):
            result = runner.invoke(app, ["raids", "#CLAN", "-t", FAKE_TOKEN, "--json"])
        assert result.exit_code == 0
        assert len(json.loads(result.output)["items"]) == 1


# ---------------------------------------------------------------------------
# CWL War
# ---------------------------------------------------------------------------


class TestCwlWarCommand:
    def test_cwl_war_json(self):
        data = {"state": "warEnded", "teamSize": 15}
        with patch.object(CocApi, "warleague", return_value=data):
            result = runner.invoke(app, ["cwl-war", "#WAR", "-t", FAKE_TOKEN, "--json"])
        assert result.exit_code == 0
        assert json.loads(result.output)["state"] == "warEnded"


# ---------------------------------------------------------------------------
# Location info
# ---------------------------------------------------------------------------


class TestLocationInfoCommand:
    def test_location_info_json(self):
        data = {"id": 32000006, "name": "International", "isCountry": False}
        with patch.object(CocApi, "location_id", return_value=data):
            result = runner.invoke(
                app, ["location", "32000006", "-t", FAKE_TOKEN, "--json"]
            )
        assert result.exit_code == 0
        assert json.loads(result.output)["name"] == "International"


# ---------------------------------------------------------------------------
# Rankings
# ---------------------------------------------------------------------------


class TestRankingsCommand:
    def test_rankings_clans(self):
        data = {"items": [{"tag": "#C1", "name": "TopClan", "rank": 1}], "paging": {"cursors": {}}}
        with patch.object(CocApi, "location_id_clan_rank", return_value=data):
            result = runner.invoke(
                app, ["rankings", "32000087", "clans", "-t", FAKE_TOKEN, "--json"]
            )
        assert result.exit_code == 0

    def test_rankings_players(self):
        data = {"items": [{"tag": "#P1", "name": "TopPlayer", "rank": 1}], "paging": {"cursors": {}}}
        with patch.object(CocApi, "location_id_player_rank", return_value=data):
            result = runner.invoke(
                app, ["rankings", "32000087", "players", "-t", FAKE_TOKEN, "--json"]
            )
        assert result.exit_code == 0

    def test_rankings_capitals(self):
        data = {"items": [{"tag": "#C1", "name": "CapClan"}], "paging": {"cursors": {}}}
        with patch.object(CocApi, "location_capital_rankings", return_value=data):
            result = runner.invoke(
                app, ["rankings", "32000087", "capitals", "-t", FAKE_TOKEN, "--json"]
            )
        assert result.exit_code == 0

    def test_rankings_builder_base(self):
        data = {"items": [{"tag": "#C1"}], "paging": {"cursors": {}}}
        with patch.object(CocApi, "location_clans_builder_base", return_value=data):
            result = runner.invoke(
                app,
                ["rankings", "32000087", "clans-builder-base", "-t", FAKE_TOKEN, "--json"],
            )
        assert result.exit_code == 0

    def test_rankings_invalid_type(self):
        result = runner.invoke(
            app, ["rankings", "32000087", "bad-type", "-t", FAKE_TOKEN]
        )
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# League info
# ---------------------------------------------------------------------------


class TestLeagueInfoCommand:
    def test_league_info_json(self):
        data = {"id": "29000022", "name": "Legend League"}
        with patch.object(CocApi, "league_id", return_value=data):
            result = runner.invoke(
                app, ["league", "29000022", "-t", FAKE_TOKEN, "--json"]
            )
        assert result.exit_code == 0
        assert json.loads(result.output)["name"] == "Legend League"


# ---------------------------------------------------------------------------
# League seasons
# ---------------------------------------------------------------------------


class TestLeagueSeasonsCommand:
    def test_list_seasons(self):
        data = {"items": [{"id": "2025-01"}], "paging": {"cursors": {}}}
        with patch.object(CocApi, "league_season", return_value=data):
            result = runner.invoke(
                app, ["league-seasons", "29000022", "-t", FAKE_TOKEN, "--json"]
            )
        assert result.exit_code == 0

    def test_season_rankings(self):
        data = {"items": [{"tag": "#P1", "rank": 1}], "paging": {"cursors": {}}}
        with patch.object(CocApi, "league_season_id", return_value=data):
            result = runner.invoke(
                app, ["league-seasons", "29000022", "2025-01", "-t", FAKE_TOKEN, "--json"]
            )
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# War leagues
# ---------------------------------------------------------------------------


class TestWarLeaguesCommand:
    def test_list_war_leagues(self):
        data = {"items": [{"id": "48000000", "name": "Champion I"}], "paging": {"cursors": {}}}
        with patch.object(CocApi, "warleagues", return_value=data):
            result = runner.invoke(
                app, ["war-leagues", "-t", FAKE_TOKEN, "--json"]
            )
        assert result.exit_code == 0

    def test_war_league_by_id(self):
        data = {"id": "48000000", "name": "Champion I"}
        with patch.object(CocApi, "warleagues_id", return_value=data):
            result = runner.invoke(
                app, ["war-leagues", "48000000", "-t", FAKE_TOKEN, "--json"]
            )
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Capital leagues
# ---------------------------------------------------------------------------


class TestCapitalLeaguesCommand:
    def test_list_capital_leagues(self):
        data = {"items": [{"id": "85000000", "name": "Capital I"}], "paging": {"cursors": {}}}
        with patch.object(CocApi, "capitalleagues", return_value=data):
            result = runner.invoke(
                app, ["capital-leagues", "-t", FAKE_TOKEN, "--json"]
            )
        assert result.exit_code == 0

    def test_capital_league_by_id(self):
        data = {"id": "85000000", "name": "Capital I"}
        with patch.object(CocApi, "capitalleagues_id", return_value=data):
            result = runner.invoke(
                app, ["capital-leagues", "85000000", "-t", FAKE_TOKEN, "--json"]
            )
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Builder base leagues
# ---------------------------------------------------------------------------


class TestBuilderBaseLeaguesCommand:
    def test_list_builder_base_leagues(self):
        data = {"items": [{"id": "44000000", "name": "Builder I"}], "paging": {"cursors": {}}}
        with patch.object(CocApi, "builderbaseleagues", return_value=data):
            result = runner.invoke(
                app, ["builder-base-leagues", "-t", FAKE_TOKEN, "--json"]
            )
        assert result.exit_code == 0

    def test_builder_base_league_by_id(self):
        data = {"id": "44000000", "name": "Builder I"}
        with patch.object(CocApi, "builderbaseleagues_id", return_value=data):
            result = runner.invoke(
                app, ["builder-base-leagues", "44000000", "-t", FAKE_TOKEN, "--json"]
            )
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# League tiers
# ---------------------------------------------------------------------------


class TestLeagueTiersCommand:
    def test_list_league_tiers(self):
        data = {"items": [{"id": "105000001", "name": "Tier 1"}], "paging": {"cursors": {}}}
        with patch.object(CocApi, "leaguetiers", return_value=data):
            result = runner.invoke(
                app, ["league-tiers", "-t", FAKE_TOKEN, "--json"]
            )
        assert result.exit_code == 0

    def test_league_tier_by_id(self):
        data = {"id": "105000001", "name": "Tier 1"}
        with patch.object(CocApi, "leaguetiers_id", return_value=data):
            result = runner.invoke(
                app, ["league-tiers", "105000001", "-t", FAKE_TOKEN, "--json"]
            )
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------


class TestLabelsCommand:
    def test_clan_labels(self):
        data = {"items": [{"id": 1, "name": "Clan Wars"}], "paging": {"cursors": {}}}
        with patch.object(CocApi, "labels_clans", return_value=data):
            result = runner.invoke(
                app, ["labels", "clans", "-t", FAKE_TOKEN, "--json"]
            )
        assert result.exit_code == 0

    def test_player_labels(self):
        data = {"items": [{"id": 2, "name": "Veteran"}], "paging": {"cursors": {}}}
        with patch.object(CocApi, "labels_players", return_value=data):
            result = runner.invoke(
                app, ["labels", "players", "-t", FAKE_TOKEN, "--json"]
            )
        assert result.exit_code == 0

    def test_invalid_label_type(self):
        result = runner.invoke(
            app, ["labels", "bad", "-t", FAKE_TOKEN]
        )
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# Verify token
# ---------------------------------------------------------------------------


class TestVerifyTokenCommand:
    def test_verify_token_json(self):
        data = {"tag": "#P1", "token": "abc", "status": "ok"}
        with patch.object(CocApi, "verify_player_token", return_value=data):
            result = runner.invoke(
                app, ["verify-token", "#P1", "abc", "-t", FAKE_TOKEN, "--json"]
            )
        assert result.exit_code == 0
        assert json.loads(result.output)["status"] == "ok"


# ---------------------------------------------------------------------------
# Search with filters
# ---------------------------------------------------------------------------


class TestSearchFilters:
    def test_search_with_filters(self):
        data = {"items": [{"tag": "#C1", "name": "WarClan"}], "paging": {"cursors": {}}}
        with patch.object(CocApi, "clan", return_value=data):
            result = runner.invoke(
                app,
                [
                    "search", "war", "-t", FAKE_TOKEN, "--json",
                    "--min-level", "10",
                    "--war-frequency", "always",
                ],
            )
        assert result.exit_code == 0
