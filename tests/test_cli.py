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
