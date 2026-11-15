from datetime import datetime, timezone

import pytest

from cocapi import (
    PrivateWarLogError,
    StaticData,
    build_army_link,
    cache_control,
    clan_games_window,
    parse_army_link,
    raid_weekend_window,
    raise_for_error,
)
from cocapi.client import _cwl_candidate_tags, _pick_cwl_war
from cocapi.errors import classify_http_error

UTC = timezone.utc


def test_classify():
    assert classify_http_error(503, {"reason": "inMaintenance"})[0] == "maintenance"
    assert classify_http_error(403, {"reason": "accessDenied.invalidIp"})[0] == "invalid_ip"
    assert classify_http_error(403, {"reason": "accessDenied"}, "/clans/%23A/currentwar")[0] == "private_war_log"
    assert classify_http_error(403, {"reason": "accessDenied"}, "/players/%23A")[0] == "access_denied"
    assert classify_http_error(404)[0] == "not_found"


def test_raise_for_error():
    ok = {"tag": "#A"}
    assert raise_for_error(ok) is ok
    with pytest.raises(PrivateWarLogError):
        raise_for_error({"result": "error", "error_kind": "private_war_log"})


def test_army_roundtrip():
    link = "https://link.clashofclans.com/en?action=CopyArmy&army=u10x0-2x3s1x9-3x2"
    army = parse_army_link(link)
    assert [(u.count, u.id) for u in army.troops] == [(10, 0), (2, 3)]
    assert [(u.count, u.id) for u in army.spells] == [(1, 9), (3, 2)]
    assert build_army_link(army).endswith("army=u10x0-2x3s1x9-3x2")
    assert parse_army_link("u5x1").troops[0].count == 5
    with pytest.raises(ValueError):
        parse_army_link("not a link!")


def test_static_data_and_army_names():
    sd = StaticData(
        {
            "troops": [{"_id": 4000000, "name": "Barbarian", "levels": [
                {"level": 1, "required_townhall": 1}, {"level": 2, "required_townhall": 3}]}],
            "spells": [{"_id": 26000001, "name": "Healing Spell"}],
        }
    )
    assert sd.troop("barbarian")["_id"] == 4000000
    assert sd.max_level("troops", "Barbarian", townhall=2) == 1
    army = parse_army_link("u1x0s2x1", sd)
    assert army.troops[0].name == "Barbarian"
    assert army.spells[0].name == "Healing Spell"


def test_event_windows():
    s, e = raid_weekend_window(datetime(2026, 11, 15, 12, tzinfo=UTC))
    assert (s.weekday(), s.hour, e.weekday(), e.hour) == (4, 7, 0, 7)
    s, e = clan_games_window(datetime(2026, 12, 29, tzinfo=UTC))
    assert (s.year, s.month, s.day) == (2027, 1, 22)


def test_cwl_pick():
    group = {"rounds": [{"warTags": ["#1", "#2"]}, {"warTags": ["#3"]}, {"warTags": ["#0"]}]}
    assert _cwl_candidate_tags(group) == ["#1", "#2", "#3"]
    wars = [
        ("#1", {"state": "warEnded", "clan": {"tag": "#X"}, "opponent": {"tag": "#Y"}}),
        ("#3", {"state": "inWar", "clan": {"tag": "#Z"}, "opponent": {"tag": "#X"}}),
    ]
    war = _pick_cwl_war(wars, "#x")
    assert war and war["war_tag"] == "#3" and war["clan"]["tag"] == "#X" and war["is_cwl"]


def test_cwl_fallback_sync(monkeypatch, basic_api):
    api = basic_api
    calls = []

    def fake(uri, params=None, use_dynamic_model=False):
        calls.append(uri)
        if uri.endswith("/currentwar"):
            return {"state": "notInWar"}
        if uri.endswith("/leaguegroup"):
            return {"state": "inWar", "rounds": [{"warTags": ["#W1"]}]}
        return {"state": "inWar", "clan": {"tag": "#X"}, "opponent": {"tag": "#Y"}}

    monkeypatch.setattr(api, "_api_response", fake)
    war = api.clan_current_war_auto("#X")
    assert war["is_cwl"] and war["war_tag"] == "#W1"


def test_cache_control(monkeypatch, basic_api):
    import httpx

    api = basic_api
    n = {"c": 0}

    class R:
        status_code = 200

        def json(self):
            n["c"] += 1
            return {"tag": "#A"}

    monkeypatch.setattr(httpx, "get", lambda *a, **k: R())
    api.clan_tag("#A")
    api.clan_tag("#A")
    assert n["c"] == 1
    with cache_control(lookup=False):
        api.clan_tag("#A")
    assert n["c"] == 2
    api.clear_cache()
    with cache_control(update=False):
        api.clan_tag("#B")
    api.clan_tag("#B")
    assert n["c"] == 4


def test_http_error_has_kind(monkeypatch, basic_api):
    import httpx

    api = basic_api
    api.config.max_retries = 1

    class R:
        status_code = 403

        def json(self):
            return {"reason": "accessDenied"}

    monkeypatch.setattr(httpx, "get", lambda *a, **k: R())
    res = api.clan_current_war("#A")
    assert res["error_kind"] == "private_war_log" and res["reason"] == "accessDenied"
    assert res["error_type"] == "http"


async def test_async_client_without_h2(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *a, **k):
        if name == "h2":
            raise ImportError
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    from cocapi.async_client import _http2_available

    assert _http2_available() is False
