"""Async usage of cocapi.

Demonstrates:
- Async context manager (async with)
- Awaiting API calls
- Concurrent requests with asyncio.gather
"""

import asyncio

from cocapi import CocApi


async def main() -> None:
    # Use async with — this enables async mode and manages the HTTP client
    async with CocApi("YOUR_API_TOKEN") as api:
        # Single request
        clan = await api.clan_tag("#2PP")
        print(f"Clan: {clan['name']}")

        # Multiple requests concurrently
        player_tags = ["#900PUCPV", "#J2CP8U0", "#L2VVRU0"]
        tasks = [api.players(tag) for tag in player_tags]
        players = await asyncio.gather(*tasks)

        print("\nPlayers:")
        for p in players:
            if p.get("result") != "error":
                print(f"  {p['name']} - TH{p['townHallLevel']}, {p['trophies']} trophies")

        # War log
        log = await api.clan_war_log("#2PP")
        for entry in log.get("items", [])[:3]:
            result = entry.get("result", "?")
            opponent = entry.get("opponent", {}).get("name", "?")
            print(f"\nWar vs {opponent}: {result}")


asyncio.run(main())
