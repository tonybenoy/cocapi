# Pagination & Batch

## Pagination

Endpoints that return lists use cursor-based pagination. The `paginate()` helper auto-follows cursors and yields items one by one.

### Sync

```python
from cocapi import CocApi

api = CocApi("token")

for member in api.paginate(api.clan_members, "#CLAN_TAG"):
    print(member["name"])
```

### Async

```python
async with CocApi("token") as api:
    async for member in api.paginate(api.clan_members, "#CLAN_TAG"):
        print(member["name"])
```

### Custom Page Size

```python
for clan in api.paginate(api.location_id_clan_rank, "32000087", limit=50):
    print(clan["name"])
```

### How It Works

1. Calls the method with `{"limit": N}`
2. Yields all items from the response
3. Reads the `paging.cursors.after` value
4. Repeats with `{"limit": N, "after": cursor}` until no more pages

### Compatible Endpoints

Works with any list endpoint: `clan_members`, `clan_war_log`, `clan_capitalraidseasons`, `location`, `location_id_clan_rank`, `location_id_player_rank`, `league`, `league_season`, `league_season_id`, `labels_clans`, `labels_players`, `capitalleagues`, `builderbaseleagues`, `leaguetiers`, and all ranking endpoints.

!!! note
    `clan()` search has a special signature and does not work with `paginate()`. Use the `params` dict manually if needed.

## Batch Fetch

Fetch multiple resources in one call. Sync runs sequentially; async runs concurrently with `asyncio.gather`.

### Sync

```python
results = api.batch(api.players, ["#TAG1", "#TAG2", "#TAG3"])
for player in results:
    print(player["name"], player["trophies"])
```

### Async with Concurrency Control

```python
async with CocApi("token") as api:
    results = await api.batch(api.clan_tag, clan_tags, max_concurrent=5)
```

### Methods with Multiple Args

Pass tuples for methods that take multiple positional arguments:

```python
results = api.batch(
    api.league_season_id,
    [("29000022", "2025-01"), ("29000022", "2025-02")],
)
```

### Error Handling

If one call fails, its position in the result list gets the error dict. Other calls are unaffected:

```python
results = api.batch(api.players, ["#VALID", "#INVALID", "#VALID2"])
for r in results:
    if r.get("result") == "error":
        print(f"Failed: {r['message']}")
    else:
        print(r["name"])
```
