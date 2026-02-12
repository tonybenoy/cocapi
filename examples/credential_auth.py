"""Credential-based authentication.

Demonstrates:
- Logging in with developer portal email/password
- Automatic key creation and IP detection
- Key persistence across runs
- The API auto-refreshes keys if your IP changes mid-session
"""

from cocapi import ApiConfig, CocApi

# --- Basic credential auth ---
# cocapi logs into the developer portal, detects your IP, and creates API keys.
api = CocApi.from_credentials("you@example.com", "your_password")
clan = api.clan_tag("#2PP")
print(f"Clan: {clan['name']}")

# --- With key persistence ---
# On first run: logs in, creates key, saves to ~/.cocapi/keys.json
# On subsequent runs: loads cached key (skips login if IP hasn't changed)
config = ApiConfig(
    persist_keys=True,
    key_name="my-bot",  # Key name on the developer portal
    key_count=2,  # Number of keys to maintain
)
api = CocApi.from_credentials("you@example.com", "your_password", config=config)
print(f"Token: {api.token[:20]}...")

# --- Async with credentials ---
# import asyncio
#
# async def main():
#     config = ApiConfig(persist_keys=True)
#     api = CocApi.from_credentials("you@example.com", "your_password", config=config)
#     async with api:
#         clan = await api.clan_tag("#2PP")
#         print(clan["name"])
#
# asyncio.run(main())
