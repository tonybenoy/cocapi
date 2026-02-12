#!/usr/bin/env python3
"""
Test all cocapi endpoints against the live Clash of Clans API.

Usage:
    uv run python scripts/test_all_endpoints.py <API_TOKEN>
    uv run python scripts/test_all_endpoints.py <API_TOKEN> --clan-tag "#2P2G0C0G"

Requires a valid API token from https://developer.clashofclans.com/
"""

import json
import sys
import time
from typing import Any, Dict, Optional

from cocapi import CocApi


def keys_structure(obj: Any, depth: int = 0, max_depth: int = 2) -> Any:
    """Extract key structure from an API response (for documentation)."""
    if depth > max_depth:
        return "..."
    if isinstance(obj, dict):
        return {k: keys_structure(v, depth + 1, max_depth) for k, v in obj.items()}
    elif isinstance(obj, list) and obj:
        return [keys_structure(obj[0], depth + 1, max_depth)]
    elif isinstance(obj, list):
        return []
    elif isinstance(obj, bool):
        return True
    elif isinstance(obj, int):
        return 0
    elif isinstance(obj, float):
        return 0.0
    elif isinstance(obj, str):
        return "string"
    return obj


class EndpointTester:
    def __init__(self, token: str, clan_tag: str, player_tag: str):
        self.api = CocApi(token, timeout=30)
        self.clan_tag = clan_tag
        self.player_tag = player_tag
        self.results: Dict[str, Any] = {}
        self.ok = 0
        self.errors = 0
        self.skipped = 0

    def test(
        self,
        name: str,
        func: Any,
        *args: Any,
        expected_error: bool = False,
        **kwargs: Any,
    ) -> Optional[Dict[str, Any]]:
        """Test a single endpoint."""
        try:
            time.sleep(0.15)  # avoid rate limiting
            result = func(*args, **kwargs)
            is_error = isinstance(result, dict) and result.get("result") == "error"
            error_type = result.get("error_type", "") if isinstance(result, dict) else ""

            if is_error:
                if expected_error:
                    print(f"  [EXPECTED] {name}: {result.get('message', '')}")
                    self.ok += 1
                else:
                    print(f"  [ERROR]    {name}: {result.get('message', '')}")
                    self.errors += 1
            else:
                print(f"  [OK]       {name}")
                self.ok += 1

            self.results[name] = result
            return result
        except Exception as e:
            print(f"  [EXCEPTION] {name}: {e}")
            self.errors += 1
            self.results[name] = {"exception": str(e)}
            return None

    def skip(self, name: str, reason: str) -> None:
        print(f"  [SKIP]     {name}: {reason}")
        self.skipped += 1

    def run_all(self) -> None:
        print("=" * 65)
        print("  COCAPI ENDPOINT VERIFICATION")
        print("=" * 65)

        # --- CLANS ---
        print("\n--- Clans ---")
        self.test("clan_tag", self.api.clan_tag, self.clan_tag)
        self.test("clan_members", self.api.clan_members, self.clan_tag, {"limit": 2})
        self.test("clan_war_log", self.api.clan_war_log, self.clan_tag, {"limit": 1})
        self.test("clan_current_war", self.api.clan_current_war, self.clan_tag)
        self.test("clan_leaguegroup", self.api.clan_leaguegroup, self.clan_tag)
        self.test(
            "clan_capitalraidseasons",
            self.api.clan_capitalraidseasons,
            self.clan_tag,
            {"limit": 1},
        )
        self.test("clan_search", self.api.clan, "clash", 2)
        self.test(
            "clan_search_advanced",
            self.api.clan,
            "war",
            2,
            min_clan_level=10,
            war_frequency="always",
        )

        # --- PLAYERS ---
        print("\n--- Players ---")
        self.test("players", self.api.players, self.player_tag)
        self.test(
            "verify_player_token",
            self.api.verify_player_token,
            self.player_tag,
            "test_token",
        )

        # --- LOCATIONS ---
        print("\n--- Locations ---")
        self.test("location", self.api.location, {"limit": 2})
        self.test("location_id", self.api.location_id, "32000006")

        # Use International (32000087) for rankings — works reliably
        loc = "32000087"
        self.test(
            "location_id_clan_rank",
            self.api.location_id_clan_rank,
            loc,
            {"limit": 2},
        )
        self.test(
            "location_id_player_rank",
            self.api.location_id_player_rank,
            loc,
            {"limit": 2},
        )
        self.test(
            "location_clans_builder_base",
            self.api.location_clans_builder_base,
            loc,
            {"limit": 2},
        )
        self.test(
            "location_players_builder_base",
            self.api.location_players_builder_base,
            loc,
            {"limit": 2},
        )
        self.test(
            "location_capital_rankings",
            self.api.location_capital_rankings,
            loc,
            {"limit": 2},
        )

        # Deprecated endpoints
        self.test(
            "location_clan_versus",
            self.api.location_clan_versus,
            loc,
            {"limit": 2},
            expected_error=True,
        )
        self.test(
            "location_player_versus",
            self.api.location_player_versus,
            loc,
            {"limit": 2},
            expected_error=True,
        )

        # --- LEAGUES ---
        print("\n--- Leagues ---")
        self.test("league", self.api.league, {"limit": 2})
        self.test("league_id", self.api.league_id, "29000022")
        self.test("league_season", self.api.league_season, "29000022", {"limit": 2})
        self.test(
            "league_season_id",
            self.api.league_season_id,
            "29000022",
            "2025-01",
            {"limit": 100},
        )

        # --- CAPITAL LEAGUES ---
        print("\n--- Capital Leagues ---")
        self.test("capitalleagues", self.api.capitalleagues, {"limit": 2})
        self.test("capitalleagues_id", self.api.capitalleagues_id, "85000000")

        # --- BUILDER BASE LEAGUES ---
        print("\n--- Builder Base Leagues ---")
        self.test("builderbaseleagues", self.api.builderbaseleagues, {"limit": 2})
        self.test("builderbaseleagues_id", self.api.builderbaseleagues_id, "44000000")

        # --- LEAGUE TIERS ---
        print("\n--- League Tiers ---")
        self.test("leaguetiers", self.api.leaguetiers, {"limit": 2})
        self.test("leaguetiers_id", self.api.leaguetiers_id, "105000001")

        # --- WAR LEAGUES ---
        print("\n--- War Leagues ---")
        self.test("warleagues", self.api.warleagues)
        self.test("warleagues_id", self.api.warleagues_id, "48000000")

        # --- CLAN WAR LEAGUE WAR ---
        print("\n--- Clan War League War ---")
        lg = self.results.get("clan_leaguegroup")
        if lg and isinstance(lg, dict) and lg.get("rounds"):
            war_tag = None
            for r in lg["rounds"]:
                for wt in r.get("warTags", []):
                    if wt != "#0":
                        war_tag = wt
                        break
                if war_tag:
                    break
            if war_tag:
                self.test("warleague", self.api.warleague, war_tag)
            else:
                self.skip("warleague", "no valid war tags in league group")
        else:
            self.skip("warleague", "clan not in CWL this season")

        # --- GOLD PASS ---
        print("\n--- Gold Pass ---")
        self.test("goldpass", self.api.goldpass)

        # --- LABELS ---
        print("\n--- Labels ---")
        self.test("labels_clans", self.api.labels_clans)
        self.test("labels_players", self.api.labels_players)

        # --- SUMMARY ---
        total = self.ok + self.errors + self.skipped
        print()
        print("=" * 65)
        print(f"  RESULTS: {self.ok} OK / {self.errors} ERRORS / {self.skipped} SKIPPED  (total: {total})")
        print("=" * 65)

        if self.errors > 0:
            print("\n  Failed endpoints:")
            for name, result in self.results.items():
                if isinstance(result, dict) and result.get("result") == "error":
                    etype = result.get("error_type", "")
                    if etype not in ("deprecated",):
                        print(f"    - {name}: {result.get('message')}")

    def dump_structures(self, path: str = "scripts/response_structures.json") -> None:
        """Write response key structures to a JSON file for documentation reference."""
        structures = {}
        for name, result in self.results.items():
            if isinstance(result, dict) and result.get("result") != "error":
                structures[name] = keys_structure(result)
        with open(path, "w") as f:
            json.dump(structures, f, indent=2, default=str)
        print(f"\n  Response structures written to {path}")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    token = sys.argv[1]
    clan_tag = "#2P2G0C0G"  # default: public war log
    player_tag = "#900PUCPV"

    # Parse optional args
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--clan-tag" and i + 1 < len(args):
            clan_tag = args[i + 1]
            i += 2
        elif args[i] == "--player-tag" and i + 1 < len(args):
            player_tag = args[i + 1]
            i += 2
        elif args[i] == "--dump":
            # handled after run
            i += 1
        else:
            print(f"Unknown argument: {args[i]}")
            sys.exit(1)

    tester = EndpointTester(token, clan_tag, player_tag)
    tester.run_all()

    if "--dump" in sys.argv:
        tester.dump_structures()


if __name__ == "__main__":
    main()
