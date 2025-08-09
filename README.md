<p>
    <a href="https://github.com/tonybenoy/cocapi/actions">
        <img src="https://github.com/tonybenoy/cocapi/workflows/CI/badge.svg" alt="CI Status" height="20">
    </a>
    <a href="https://pypi.org/project/cocapi/"><img src="https://img.shields.io/pypi/v/cocapi" alt="Pypi version" height="21"></a>
</p>
<p>
    <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.7+-blue.svg" alt="Python version" height="17"></a>
    <a href="https://github.com/tonybenoy/cocapi/blob/master/LICENSE"><img src="https://img.shields.io/github/license/tonybenoy/cocapi" alt="License" height="17"></a>
    <a href="https://github.com/astral-sh/ruff">
        <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff" height="17">
    </a>
</p>

# ClashOfClansAPI

A high-performance Python wrapper for SuperCell's Clash of Clans API with enterprise-grade features including async support, response caching, retry logic, and configurable settings.

**🎯 Complete API Coverage**: All 22 official endpoints implemented  
**⚡ High Performance**: Async support with intelligent caching  
**🔄 100% Backward Compatible**: Drop-in replacement for existing code  
**🛡️ Production Ready**: Retry logic, rate limiting, and comprehensive error handling

Get Token from [https://developer.clashofclans.com/](https://developer.clashofclans.com/)

## Features

- **Synchronous and Asynchronous API support**
- **Intelligent response caching with TTL**
- **Automatic retry logic with exponential backoff**
- **Rate limiting protection**
- **Comprehensive error handling**
- **Type hints for better development experience**
- **Optional Pydantic models for structured data validation**
- **100% backward compatible**
- **Configurable settings**

# Install

```bash
# Standard installation (dict responses)
pip install cocapi

# With optional Pydantic models support
pip install 'cocapi[pydantic]'
```


# Usage Examples

## Basic Synchronous Usage (Backward Compatible)

```python
from cocapi import CocApi

token = 'YOUR_API_TOKEN'
timeout = 60  # requests timeout

# Basic initialization (same as before)
api = CocApi(token, timeout)

# With status codes (same as before)
api = CocApi(token, timeout, status_code=True)
```

## Advanced Configuration

```python
from cocapi import CocApi, ApiConfig

# Custom configuration
config = ApiConfig(
    timeout=30,
    max_retries=5,
    cache_ttl=600,  # Cache for 10 minutes
    enable_caching=True,
    retry_delay=2  # Initial retry delay in seconds
)

api = CocApi('YOUR_API_TOKEN', config=config)

# Cache management
stats = api.get_cache_stats()
api.clear_cache()  # Clear all cached responses
```

## Asynchronous Usage

```python
import asyncio
from cocapi import CocApi, ApiConfig

async def main():
    # Method 1: Automatic async mode with context manager (recommended)
    async with CocApi('YOUR_API_TOKEN') as api:
        clan = await api.clan_tag('#CLAN_TAG')
        player = await api.players('#PLAYER_TAG')
    
    # Method 2: Explicit async mode
    api = CocApi('YOUR_API_TOKEN', async_mode=True)
    async with api:
        clan = await api.clan_tag('#CLAN_TAG')
    
    # Method 3: With custom configuration
    config = ApiConfig(timeout=30, enable_caching=True)
    async with CocApi('YOUR_API_TOKEN', config=config) as api:
        clan = await api.clan_tag('#CLAN_TAG')

# Run async code
asyncio.run(main())
```

## Pydantic Models (Optional)

For enhanced type safety and structured data validation, cocapi supports optional Pydantic models:

```python
from cocapi import CocApi, ApiConfig, Clan, Player

# Enable Pydantic models
config = ApiConfig(use_pydantic_models=True)
api = CocApi('YOUR_API_TOKEN', config=config)

# Get structured clan data
clan = api.clan_tag('#2PP')  # Returns Clan model instead of dict
print(clan.name)             # Type-safe attribute access
print(clan.clan_level)       # IDE autocompletion support
print(clan.members)          # Validated data structure

# Get structured player data  
player = api.players('#PLAYER_TAG')  # Returns Player model
print(player.town_hall_level)        # Type-safe attributes
print(player.trophies)
print(player.clan.name if player.clan else "No clan")

# Works with async too
async def get_data():
    config = ApiConfig(use_pydantic_models=True)
    async with CocApi('YOUR_TOKEN', config=config) as api:
        clan = await api.clan_tag('#TAG')  # Returns Clan model
        return clan.name

# Available models: Clan, Player, ClanMember, League, Achievement, etc.
# Import them: from cocapi import Clan, Player, ClanMember
```

### Benefits of Pydantic Models

- **Type Safety**: Catch errors at development time
- **IDE Support**: Full autocompletion and type hints
- **Data Validation**: Automatic validation of API responses  
- **Clean Interface**: Object-oriented access to data
- **Documentation**: Self-documenting code with model schemas
- **Optional**: Zero impact if not used (lazy imports)

## Performance Comparison

The new features provide significant performance improvements:

- **Caching**: Up to 100% faster for repeated requests
- **Async**: Handle multiple requests concurrently
- **Retry Logic**: Automatic handling of temporary failures
- **Rate Limiting**: Built-in protection against API limits

## Migration Guide

### For Existing Users

**No breaking changes!** Your existing code will continue to work exactly as before:

```python
# This still works exactly the same
from cocapi import CocApi
api = CocApi('YOUR_TOKEN', 60, status_code=True)
clan = api.clan_tag('#CLAN_TAG')
```

### Upgrading to New Features

To take advantage of new features:

```python
from cocapi import CocApi, ApiConfig

# 1. Add caching to existing code (no changes needed!)
config = ApiConfig(enable_caching=True, cache_ttl=300)
api = CocApi('YOUR_TOKEN', config=config)

# 2. Use async for better performance (same class!)
async with CocApi('YOUR_TOKEN') as api:
    clan = await api.clan_tag('#CLAN_TAG')

# 3. Enhanced error handling is automatic
result = api.clan_tag('#INVALID_TAG')
if result.get('result') == 'error':
    print(f"Error: {result.get('message')}")
```

---

## What's New in v2.2.0+

🆕 **Latest in v2.2.0:**
- **Optional Pydantic Models**: Type-safe, validated data structures with IDE support
- **Enhanced Type Safety**: Full Pydantic model support for `Clan`, `Player`, and all API responses
- **Flexible Configuration**: Enable/disable Pydantic models via `ApiConfig.use_pydantic_models`
- **Lazy Loading**: Zero impact when not using models (automatic imports)
- **Async + Pydantic**: Full async support with Pydantic model validation
- **Comprehensive Models**: 15+ Pydantic models covering all API response types

## What's New in v2.1.0+

✨ **Major New Features:**
- **Unified Async Support**: Same `CocApi` class works for both sync and async!
- **Intelligent Caching**: Automatic response caching with configurable TTL
- **Retry Logic**: Exponential backoff for handling temporary API failures
- **Enhanced Configuration**: Flexible settings via ApiConfig class
- **Better Error Handling**: Comprehensive error messages and types
- **Type Hints**: Complete type annotations for better IDE support
- **Rate Limiting Protection**: Built-in handling of API rate limits
- **🆕 Optional Pydantic Models**: Type-safe, validated data structures with IDE support

🔧 **Code Quality Improvements:**
- Fixed all mutable default arguments
- Added comprehensive logging
- Improved test coverage
- Enhanced documentation

📚 **Full API Reference**

The following sections document all available API methods. All methods work identically in both sync and async modes - just use `await` when in async context!

---

## Clans

### Information about a Clan
```python
api.clan_tag(tag) #example tag "#9UOVJJ9J"
```
<details>
 <summary>Click to view output</summary>

```text
{
  "warLeague": {
    "name": {},
    "id": 0
  },
  "memberList": [
    {
      "league": {
        "name": {},
        "id": 0,
        "iconUrls": {}
      },
      "tag": "string",
      "name": "string",
      "role": "string",
      "expLevel": 0,
      "clanRank": 0,
      "previousClanRank": 0,
      "donations": 0,
      "donationsReceived": 0,
      "trophies": 0,
      "versusTrophies": 0
    }
  ],
  "isWarLogPublic": true,
  "tag": "string",
  "warFrequency": "string",
  "clanLevel": 0,
  "warWinStreak": 0,
  "warWins": 0,
  "warTies": 0,
  "warLosses": 0,
  "clanPoints": 0,
  "clanVersusPoints": 0,
  "requiredTrophies": 0,
  "name": "string",
  "location": {
    "localizedName": "string",
    "id": 0,
    "name": "string",
    "isCountry": true,
    "countryCode": "string"
  },
  "type": "string",
  "members": 0,
  "labels": [
    {
      "name": {},
      "id": 0,
      "iconUrls": {}
    }
  ],
  "description": "string",
  "badgeUrls": {}
}
```
</details>

#### Members Only
```python
api.clan_members(tag)
```
returns membersList information from api.clan_tag(tag) under "items" in dict

### War Log Information
```python
api.clan_war_log(tag)
```
<details>
 <summary>Click to view output</summary>

```text
{items:
[
  {
    "clan": {
      "destructionPercentage": {},
      "tag": "string",
      "name": "string",
      "badgeUrls": {},
      "clanLevel": 0,
      "attacks": 0,
      "stars": 0,
      "expEarned": 0,
      "members": [
        {
          "tag": "string",
          "name": "string",
          "mapPosition": 0,
          "townhallLevel": 0,
          "opponentAttacks": 0,
          "bestOpponentAttack": {
            "order": 0,
            "attackerTag": "string",
            "defenderTag": "string",
            "stars": 0,
            "destructionPercentage": 0
          },
          "attacks": [
            {
              "order": 0,
              "attackerTag": "string",
              "defenderTag": "string",
              "stars": 0,
              "destructionPercentage": 0
            }
          ]
        }
      ]
    },
    "teamSize": 0,
    "opponent": {
      "destructionPercentage": {},
      "tag": "string",
      "name": "string",
      "badgeUrls": {},
      "clanLevel": 0,
      "attacks": 0,
      "stars": 0,
      "expEarned": 0,
      "members": [
        {
          "tag": "string",
          "name": "string",
          "mapPosition": 0,
          "townhallLevel": 0,
          "opponentAttacks": 0,
          "bestOpponentAttack": {
            "order": 0,
            "attackerTag": "string",
            "defenderTag": "string",
            "stars": 0,
            "destructionPercentage": 0
          },
          "attacks": [
            {
              "order": 0,
              "attackerTag": "string",
              "defenderTag": "string",
              "stars": 0,
              "destructionPercentage": 0
            }
          ]
        }
      ]
    },
    "endTime": "string",
    "result": "string"
  }
],
"paging": {'cursors': {}}
}
```
</details>

### Current War Information
```python
api.clan_current_war(tag)
```
<details>
 <summary>Click to view output</summary>

```text
{
  "clan": {
    "destructionPercentage": {},
    "tag": "string",
    "name": "string",
    "badgeUrls": {},
    "clanLevel": 0,
    "attacks": 0,
    "stars": 0,
    "expEarned": 0,
    "members": [
      {
        "tag": "string",
        "name": "string",
        "mapPosition": 0,
        "townhallLevel": 0,
        "opponentAttacks": 0,
        "bestOpponentAttack": {
          "order": 0,
          "attackerTag": "string",
          "defenderTag": "string",
          "stars": 0,
          "destructionPercentage": 0
        },
        "attacks": [
          {
            "order": 0,
            "attackerTag": "string",
            "defenderTag": "string",
            "stars": 0,
            "destructionPercentage": 0
          }
        ]
      }
    ]
  },
  "teamSize": 0,
  "opponent": {
    "destructionPercentage": {},
    "tag": "string",
    "name": "string",
    "badgeUrls": {},
    "clanLevel": 0,
    "attacks": 0,
    "stars": 0,
    "expEarned": 0,
    "members": [
      {
        "tag": "string",
        "name": "string",
        "mapPosition": 0,
        "townhallLevel": 0,
        "opponentAttacks": 0,
        "bestOpponentAttack": {
          "order": 0,
          "attackerTag": "string",
          "defenderTag": "string",
          "stars": 0,
          "destructionPercentage": 0
        },
        "attacks": [
          {
            "order": 0,
            "attackerTag": "string",
            "defenderTag": "string",
            "stars": 0,
            "destructionPercentage": 0
          }
        ]
      }
    ]
  },
  "startTime": "string",
  "state": "string",
  "endTime": "string",
  "preparationStartTime": "string"
}
```
</details>

### Clan League Group Information
```python
api.clan_leaguegroup(tag)
```
<details>
 <summary>Click to view output</summary>

```text
{
  "tag": "string",
  "state": "string",
  "season": "string",
  "clans": [
    {
      "tag": "string",
      "clanLevel": 0,
      "name": "string",
      "members": [
        {
          "tag": "string",
          "townHallLevel": 0,
          "name": "string"
        }
      ],
      "badgeUrls": {}
    }
  ],
  "rounds": [
    {
      "warTags": [
        "string"
      ]
    }
  ]
}
```
</details>

### Clan Capital Raid Seasons
```python
api.clan_capitalraidseasons(tag)
```
Retrieve clan's capital raid seasons information
<details>
 <summary>Click to view output</summary>

```text
{"items":
[
  {
    "state": "string",
    "startTime": "string", 
    "endTime": "string",
    "capitalTotalLoot": 0,
    "raidsCompleted": 0,
    "totalAttacks": 0,
    "enemyDistrictsDestroyed": 0,
    "offensiveReward": 0,
    "defensiveReward": 0,
    "members": [
      {
        "tag": "string",
        "name": "string",
        "attacks": 0,
        "attackLimit": 0,
        "bonusAttackLimit": 0,
        "capitalResourcesLooted": 0
      }
    ]
  }
],
"paging": {'cursors': {}}
}
```
</details>

### Warleague Information
```python
api.warleague(war_tag)
```
<details>
 <summary>Click to view output</summary>

```text
{
  "tag": "string",
  "state": "string",
  "season": "string",
  "clans": [
    {
      "tag": "string",
      "clanLevel": 0,
      "name": "string",
      "members": [
        {
          "tag": "string",
          "townHallLevel": 0,
          "name": "string"
        }
      ],
      "badgeUrls": {}
    }
  ],
  "rounds": [
    {
      "warTags": [
        "string"
      ]
    }
  ]
}
```
</details>




## Player

### Player information
```python
api.players(player_tag) #for example "#900PUCPV"
```
<details>
 <summary>Click to view output</summary>

```text
{
  "clan": {
    "tag": "string",
    "clanLevel": 0,
    "name": "string",
    "badgeUrls": {}
  },
  "league": {
    "name": {},
    "id": 0,
    "iconUrls": {}
  },
  "townHallWeaponLevel": 0,
  "versusBattleWins": 0,
  "legendStatistics": {
    "previousSeason": {
      "trophies": 0,
      "id": "string",
      "rank": 0
    },
    "previousVersusSeason": {
      "trophies": 0,
      "id": "string",
      "rank": 0
    },
    "bestVersusSeason": {
      "trophies": 0,
      "id": "string",
      "rank": 0
    },
    "legendTrophies": 0,
    "currentSeason": {
      "trophies": 0,
      "id": "string",
      "rank": 0
    },
    "bestSeason": {
      "trophies": 0,
      "id": "string",
      "rank": 0
    }
  },
  "troops": [
    {
      "level": 0,
      "name": {},
      "maxLevel": 0,
      "village": "string"
    }
  ],
  "heroes": [
    {
      "level": 0,
      "name": {},
      "maxLevel": 0,
      "village": "string"
    }
  ],
  "spells": [
    {
      "level": 0,
      "name": {},
      "maxLevel": 0,
      "village": "string"
    }
  ],
  "role": "string",
  "attackWins": 0,
  "defenseWins": 0,
  "townHallLevel": 0,
  "labels": [
    {
      "name": {},
      "id": 0,
      "iconUrls": {}
    }
  ],
  "tag": "string",
  "name": "string",
  "expLevel": 0,
  "trophies": 0,
  "bestTrophies": 0,
  "donations": 0,
  "donationsReceived": 0,
  "builderHallLevel": 0,
  "versusTrophies": 0,
  "bestVersusTrophies": 0,
  "warStars": 0,
  "achievements": [
    {
      "stars": 0,
      "value": 0,
      "name": {},
      "target": 0,
      "info": {},
      "completionInfo": {},
      "village": "string"
    }
  ],
  "versusBattleWinCount": 0
}
```
</details>




## Locations

### All Locations Information
```python
api.location()
```
<details>
 <summary>Click to view output</summary>

```text
{"items":
[
  {
    "localizedName": "string",
    "id": 0,
    "name": "string",
    "isCountry": true,
    "countryCode": "string"
  }
],
"paging": {'cursors': {}}
}
```
</details>

### Information for a Single Location
```python
api.location_id(location_tag) #for example "32000047"
```

returns the above information for a single location

### Top Clans in a Location
```python
api.location_id_clan_rank(location_tag)
```
Top 200 clans in a given location
<details>
 <summary>Click to view output</summary>

```text
{"items":
[
  {
    "clanLevel": 0,
    "clanPoints": 0,
    "location": {
      "localizedName": "string",
      "id": 0,
      "name": "string",
      "isCountry": true,
      "countryCode": "string"
    },
    "members": 0,
    "tag": "string",
    "name": "string",
    "rank": 0,
    "previousRank": 0,
    "badgeUrls": {}
  }
],
"paging": {'cursors': {}}
}
```
</details>

### Top Players in a Location
```python
api.clan_leaguegroup(location_tag)
```
Top 200 players in a given location
<details>
 <summary>Click to view output</summary>

```text
{"items":
[
  {
    "clan": {
      "tag": "string",
      "name": "string",
      "badgeUrls": {}
    },
    "league": {
      "name": {},
      "id": 0,
      "iconUrls": {}
    },
    "attackWins": 0,
    "defenseWins": 0,
    "tag": "string",
    "name": "string",
    "expLevel": 0,
    "rank": 0,
    "previousRank": 0,
    "trophies": 0
  }
],
"paging": {'cursors': {}}
}
```
</details>


### Top Versus Clans in a Location
```python
api.location_clan_versus(location_tag)
```
Top 200 versus clans in a given location
<details>
 <summary>Click to view output</summary>

```text
{"items":
[
  {
    "clanPoints": 0,
    "clanVersusPoints": 0
  }
],
"paging": {'cursors': {}}
}
```
</details>


### Top Versus Players in a Location
```python
api.location_player_versus(location_tag)
```
Top 200 versus players in a given location
<details>
 <summary>Click to view output</summary>

```text
{"items":
[
  {
    "clan": {
      "tag": "string",
      "name": "string",
      "badgeUrls": {}
    },
    "versusBattleWins": 0,
    "tag": "string",
    "name": "string",
    "expLevel": 0,
    "rank": 0,
    "previousRank": 0,
    "versusTrophies": 0
  }
],
"paging": {'cursors': {}}
}
```
</details>




## Leagues

### List leagues
```python
api.league()
```
<details>
 <summary>Click to view output</summary>

```text
{"items":
[
  {
    "name": {},
    "id": 0,
    "iconUrls": {}
  }
],
"paging": {'cursors': {}}
}
```
</details>


### League Information
```python
api.league_id(league_tag)
```
<details>
 <summary>Click to view output</summary>

```text
{
  "name": {},
  "id": 0,
  "iconUrls": {}
}
```
</details>


### List Season Leagues
```python
api.league_season(league_tag)
```
Information is available only for Legend League
<details>
 <summary>Click to view output</summary>

```text
{"items":
[
  {
    "id": "string"
  }
],
"paging": {'cursors': {}}
}
```
</details>


### League Season Ranking
```python
api.league_season_id(league_tag, season_tag)
```
Information is available only for Legend League
<details>
 <summary>Click to view output</summary>

```text
{"items":
[
  {
    "clan": {
      "tag": "string",
      "name": "string",
      "badgeUrls": {}
    },
    "league": {
      "name": {},
      "id": 0,
      "iconUrls": {}
    },
    "attackWins": 0,
    "defenseWins": 0,
    "tag": "string",
    "name": "string",
    "expLevel": 0,
    "rank": 0,
    "previousRank": 0,
    "trophies": 0
  }
],
"paging": {'cursors': {}}
}
```
</details>

### List Capital Leagues
```python
api.capitalleagues()
```
<details>
 <summary>Click to view output</summary>

```text
{"items":
[
  {
    "name": {},
    "id": 0,
    "iconUrls": {}
  }
],
"paging": {'cursors': {}}
}
```
</details>

### Capital League Information
```python
api.capitalleagues_id(league_id)
```
<details>
 <summary>Click to view output</summary>

```text
{
  "name": {},
  "id": 0,
  "iconUrls": {}
}
```
</details>

### List Builder Base Leagues
```python
api.builderbaseleagues()
```
<details>
 <summary>Click to view output</summary>

```text
{"items":
[
  {
    "name": {},
    "id": 0,
    "iconUrls": {}
  }
],
"paging": {'cursors': {}}
}
```
</details>

### Builder Base League Information
```python
api.builderbaseleagues_id(league_id)
```
<details>
 <summary>Click to view output</summary>

```text
{
  "name": {},
  "id": 0,
  "iconUrls": {}
}
```
</details>

### List War Leagues
```python
api.warleagues()
```
<details>
 <summary>Click to view output</summary>

```text
{"items":
[
  {
    "name": {},
    "id": 0,
    "iconUrls": {}
  }
],
"paging": {'cursors': {}}
}
```
</details>

### War League Information
```python
api.warleagues_id(league_id)
```
<details>
 <summary>Click to view output</summary>

```text
{
  "name": {},
  "id": 0,
  "iconUrls": {}
}
```
</details>




## Gold Pass

### Current Gold Pass Season
```python
api.goldpass_seasons_current()
```
Get information about the current gold pass season
<details>
 <summary>Click to view output</summary>

```text
{
  "startTime": "string",
  "endTime": "string" 
}
```
</details>


## Labels

### List Clan Labels
```python
api.labels_clans()
```
<details>
 <summary>Click to view output</summary>

```text
{"items":
[
  {
    "name": {},
    "id": 0,
    "iconUrls": {}
  }
],
"paging": {'cursors': {}}
}
```
</details>


### List Player Labels
```python
api.labels_players()
```
<details>
 <summary>Click to view output</summary>

```text
{"items":
[
  {
    "name": {},
    "id": 0,
    "iconUrls": {}
  }
],
"paging": {'cursors': {}}
}
```
</details>


## Credits
- [All Contributors](../../contributors)

*Note versions below 2.0.0 are not supported anymore*

*DISCLAIMER: cocapi is not affiliated with SuperCell©.
