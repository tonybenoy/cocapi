"""Basic synchronous usage of cocapi.

Demonstrates:
- Initializing CocApi with a token
- Fetching clan info, player info, and war data
- Searching for clans with filters
- Error handling
"""

from cocapi import CocApi

# Replace with your API token from https://developer.clashofclans.com/
api = CocApi("YOUR_API_TOKEN")

# --- Clan info ---
clan = api.clan_tag("#2PP")
print(f"Clan: {clan['name']} (Level {clan['clanLevel']})")
print(f"Members: {clan['members']}, Points: {clan['clanPoints']}")

# --- Player info ---
player = api.players("#900PUCPV")
print(f"\nPlayer: {player['name']} (TH{player['townHallLevel']})")
print(f"Trophies: {player['trophies']}, War Stars: {player['warStars']}")

# --- Current war ---
war = api.clan_current_war("#2PP")
if war.get("result") == "error":
    print(f"\nWar: {war['message']}")  # e.g. private war log
else:
    print(f"\nWar state: {war['state']}")

# --- Search clans ---
results = api.clan("clash", 5, min_clan_level=10, min_members=30)
print("\nSearch results:")
for c in results.get("items", []):
    print(f"  {c['name']} ({c['tag']}) - Level {c['clanLevel']}")

# --- Error handling ---
bad = api.clan_tag("#INVALID_TAG_THAT_DOES_NOT_EXIST")
if bad.get("result") == "error":
    print(f"\nExpected error: {bad['message']} ({bad['error_type']})")
