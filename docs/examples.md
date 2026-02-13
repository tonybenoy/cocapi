# Examples

Runnable scripts are available in the [`examples/`](https://github.com/tonybenoy/cocapi/tree/main/examples) folder.

| Script | What it covers |
|---|---|
| `basic_usage.py` | Sync: clan info, player info, search, error handling |
| `async_usage.py` | Async with context manager, concurrent requests |
| `credential_auth.py` | Email/password login, key persistence, auto-refresh |
| `configuration.py` | ApiConfig, caching, metrics, middleware |
| `pagination_batch.py` | `paginate()` and `batch()` in sync and async |
| `event_polling.py` | `EventStream` with `async for` — real-time monitoring |
| `event_callbacks.py` | `@stream.on()` decorators and `stream.run()` |

## Basic Usage

```python
from cocapi import CocApi

api = CocApi("YOUR_API_TOKEN")

# Clan info
clan = api.clan_tag("#2PP")
print(f"Clan: {clan['name']} (Level {clan['clanLevel']})")

# Player info
player = api.players("#900PUCPV")
print(f"Player: {player['name']} (TH{player['townHallLevel']})")

# Search clans
results = api.clan("clash", 5, min_clan_level=10, min_members=30)
for c in results.get("items", []):
    print(f"  {c['name']} ({c['tag']})")

# Error handling
bad = api.clan_tag("#INVALID_TAG")
if bad.get("result") == "error":
    print(f"Error: {bad['message']} ({bad['error_type']})")
```

## Async Usage

```python
import asyncio
from cocapi import CocApi

async def main():
    async with CocApi("YOUR_API_TOKEN") as api:
        clan = await api.clan_tag("#2PP")
        print(f"Clan: {clan['name']}")

        # Concurrent requests
        tags = ["#900PUCPV", "#J2CP8U0", "#L2VVRU0"]
        players = await asyncio.gather(*[api.players(t) for t in tags])
        for p in players:
            if p.get("result") != "error":
                print(f"  {p['name']} - {p['trophies']} trophies")

asyncio.run(main())
```

## Event Polling

```python
import asyncio
from cocapi import CocApi, ApiConfig
from cocapi.events import EventStream, EventType

async def main():
    config = ApiConfig(enable_caching=False)

    async with CocApi("YOUR_API_TOKEN", config=config) as api:
        stream = EventStream(api, queue_size=1000, persist_path="state.json")
        stream.watch_clans(["#2PP"], interval=60)
        stream.watch_wars(["#2PP"], interval=30)
        stream.watch_players(["#900PUCPV"], interval=120)
        stream.watch_maintenance(interval=30)

        async with stream:
            async for event in stream:
                print(f"[{event.event_type.value}] {event.tag}")
                for change in event.changes:
                    print(f"  {change.field}: {change.old_value} -> {change.new_value}")

asyncio.run(main())
```

## Event Callbacks

```python
import asyncio
from cocapi import CocApi, ApiConfig
from cocapi.events import EventStream, EventType

async def main():
    config = ApiConfig(enable_caching=False)

    async with CocApi("YOUR_API_TOKEN", config=config) as api:
        stream = EventStream(api)
        stream.watch_clans(["#2PP"])

        @stream.on(EventType.MEMBER_JOINED)
        async def on_join(event):
            print(f"{event.metadata['member_name']} joined!")

        @stream.on(EventType.CLAN_UPDATED)
        async def on_clan(event):
            for change in event.changes:
                print(f"{change.field}: {change.old_value} -> {change.new_value}")

        await stream.run()

asyncio.run(main())
```

## Running Examples

```bash
# Replace the token in the script first, then:
python examples/basic_usage.py
python examples/async_usage.py
python examples/event_polling.py
```
