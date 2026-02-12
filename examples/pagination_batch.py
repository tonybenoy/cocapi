"""Pagination and batch fetching.

Demonstrates:
- paginate() for auto-following cursors through list endpoints
- batch() for fetching multiple resources in one call
- Both sync and async patterns
"""

import asyncio

from cocapi import CocApi

api = CocApi("YOUR_API_TOKEN")

# --- Pagination (sync) ---
# Automatically follows cursors, yields items one by one
print("=== Clan Members (paginated) ===")
for i, member in enumerate(api.paginate(api.clan_members, "#2PP", limit=10)):
    print(f"  {member['name']} - {member['trophies']} trophies")
    if i >= 19:  # Stop after 20
        break

# Works with any list endpoint
print("\n=== Top Clans in Finland (paginated) ===")
for i, clan in enumerate(api.paginate(api.location_id_clan_rank, "32000087", limit=5)):
    print(f"  #{clan['rank']} {clan['name']} - {clan['clanPoints']} pts")
    if i >= 9:
        break

# --- Batch fetch (sync — sequential) ---
print("\n=== Batch Player Fetch ===")
tags = ["#900PUCPV", "#J2CP8U0", "#L2VVRU0"]
results = api.batch(api.players, tags)
for player in results:
    if player.get("result") != "error":
        print(f"  {player['name']} - TH{player['townHallLevel']}")


# --- Async pagination + batch ---
async def async_examples() -> None:
    async with CocApi("YOUR_API_TOKEN") as api:
        # Async pagination
        print("\n=== Async Pagination ===")
        count = 0
        async for member in api.paginate(api.clan_members, "#2PP"):
            print(f"  {member['name']}")
            count += 1
            if count >= 5:
                break

        # Async batch — runs concurrently with asyncio.gather
        print("\n=== Async Batch (concurrent) ===")
        results = await api.batch(api.players, tags, max_concurrent=5)
        for player in results:
            if player.get("result") != "error":
                print(f"  {player['name']} - {player['trophies']} trophies")


# Uncomment to run async examples:
# asyncio.run(async_examples())
