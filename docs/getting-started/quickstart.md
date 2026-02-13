# Quick Start

## Get an API Token

1. Go to [developer.clashofclans.com](https://developer.clashofclans.com/)
2. Create an account or log in
3. Create a new API key bound to your IP address
4. Copy the token

Alternatively, use [credential-based auth](authentication.md) to skip manual key management.

## Sync Usage

```python
from cocapi import CocApi

api = CocApi("your_api_token")

# Fetch clan info
clan = api.clan_tag("#2PP")
print(f"Clan: {clan['name']} (Level {clan['clanLevel']})")
print(f"Members: {clan['members']}")

# Fetch player info
player = api.players("#900PUCPV")
print(f"Player: {player['name']} (TH{player['townHallLevel']})")
print(f"Trophies: {player['trophies']}")

# Search clans
results = api.clan("clash", 5, min_clan_level=10)
for c in results.get("items", []):
    print(f"  {c['name']} ({c['tag']})")
```

## Async Usage

Use `async with` to enable async mode:

```python
import asyncio
from cocapi import CocApi

async def main():
    async with CocApi("your_token") as api:
        clan = await api.clan_tag("#2PP")
        player = await api.players("#900PUCPV")
        print(clan["name"], player["trophies"])

asyncio.run(main())
```

## Credential-Based Auth

Skip manual key creation — cocapi manages keys for you:

```python
from cocapi import CocApi

api = CocApi.from_credentials("you@example.com", "your_password")
clan = api.clan_tag("#2PP")
```

See [Authentication](authentication.md) for details.

## Error Handling

All endpoints return dicts. Errors never raise exceptions:

```python
result = api.clan_tag("#INVALID")
if result.get("result") == "error":
    print(result["message"])       # Human-readable message
    print(result["error_type"])    # "timeout", "http", "connection", etc.
```

See [Error Handling](../guides/error-handling.md) for the full error reference.
