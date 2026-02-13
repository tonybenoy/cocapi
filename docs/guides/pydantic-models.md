# Pydantic Models

When enabled, endpoints return typed Pydantic model objects instead of plain dicts.

## Setup

Install the pydantic extra:

```bash
pip install 'cocapi[pydantic]'
```

Enable in config:

```python
from cocapi import CocApi, ApiConfig

config = ApiConfig(use_pydantic_models=True)
api = CocApi("token", config=config)

clan = api.clan_tag("#2PP")
print(clan.name)        # Attribute access with IDE autocompletion
print(clan.clanLevel)
```

## Available Models

All models are importable from `cocapi`:

| Model | Endpoint |
|---|---|
| `Clan` | `clan_tag()` |
| `Player` | `players()` |
| `ClanMember` | Items in `clan_members()` |
| `ClanWar` | `clan_current_war()` |
| `ClanWarLogEntry` | Items in `clan_war_log()` |
| `ClanWarLeagueGroup` | `clan_leaguegroup()` |
| `ClanCapitalRaidSeason` | Items in `clan_capitalraidseasons()` |
| `GoldPassSeason` | `goldpass()` |
| `League` | `league()`, `league_id()` |
| `LeagueSeason` | Items in `league_season()` |
| `Location` | `location()`, `location_id()` |
| `Label` | `labels_clans()`, `labels_players()` |
| `WarLeague` | `warleagues()`, `warleagues_id()` |
| `CapitalLeague` | `capitalleagues()`, `capitalleagues_id()` |
| `BuilderBaseLeague` | `builderbaseleagues()`, `builderbaseleagues_id()` |
| `LeagueTier` | `leaguetiers()`, `leaguetiers_id()` |
| `PlayerRankingEntry` | Items in ranking endpoints |
| `ClanRankingEntry` | Items in clan ranking endpoints |
| `VerifyTokenResponse` | `verify_player_token()` |

Additional supporting models: `Achievement`, `BadgeUrls`, `ChatLanguage`, `ClanCapital`, `Hero`, `HeroEquipment`, `IconUrls`, `Paging`, `PlayerClan`, `PlayerHouse`, `Spell`, `Troop`, `WarAttack`, `WarClan`, `WarMember`, and more.

## Dynamic Models

For endpoints without a predefined schema, cocapi generates a dynamic Pydantic model:

```python
result = api.custom_endpoint("/new-endpoint", use_dynamic_model=True)
```

## Without Pydantic

When pydantic is not installed or `use_pydantic_models=False` (default), all responses are plain dicts:

```python
clan = api.clan_tag("#2PP")
print(clan["name"])       # Dict access
print(type(clan))         # <class 'dict'>
```
