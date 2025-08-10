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

A high-performance Python wrapper for SuperCell's Clash of Clans API with enterprise-grade features including async support, response caching, retry logic, middleware system, and comprehensive metrics.

**🎯 Complete API Coverage**: All 22 official endpoints implemented  
**⚡ High Performance**: Async support with intelligent caching and rate limiting  
**🔄 100% Backward Compatible**: Drop-in replacement for existing code  
**🛡️ Production Ready**: Retry logic, middleware pipeline, metrics tracking, and comprehensive error handling  
**🚀 Future-Proof**: Custom endpoint support and dynamic Pydantic models

Get Token from [https://developer.clashofclans.com/](https://developer.clashofclans.com/)

## ✨ Key Features

- **🔄 Sync & Async Support**: Same API works for both sync and async
- **🚀 Custom Endpoints**: Future-proof with any new SuperCell endpoints  
- **💾 Intelligent Caching**: Response caching with configurable TTL and statistics
- **🔁 Smart Retry Logic**: Exponential backoff with configurable retry policies
- **⚡ Rate Limiting**: Built-in protection against API rate limits (async mode)
- **🛡️ Comprehensive Error Handling**: Detailed error messages and types
- **📊 Metrics & Analytics**: Request performance tracking and insights
- **🔌 Middleware System**: Pluggable request/response processing pipeline
- **🎯 Type Safety**: Complete type hints and optional Pydantic models
- **🌐 Base URL Configuration**: Support for proxies and testing environments
- **🔄 100% Backward Compatible**: Drop-in replacement for existing code

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

# Enterprise-grade configuration
config = ApiConfig(
    # Performance settings
    timeout=30,
    max_retries=5,
    retry_delay=1.5,  # Base delay for exponential backoff
    
    # Caching configuration  
    enable_caching=True,
    cache_ttl=600,  # Cache responses for 10 minutes
    
    # Async rate limiting (async mode only)
    enable_rate_limiting=True,
    requests_per_second=10.0,
    burst_limit=20,
    
    # Advanced features
    enable_metrics=True,
    metrics_window_size=1000,  # Track last 1000 requests
    use_pydantic_models=False  # Enable for type-safe models
)

api = CocApi('YOUR_API_TOKEN', config=config)

# Management methods
cache_stats = api.get_cache_stats()
metrics = api.get_metrics()
api.clear_cache()
api.clear_metrics()
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

## 🚀 Enterprise Features

### 📊 Metrics & Analytics

```python
from cocapi import CocApi, ApiConfig

# Enable metrics tracking
config = ApiConfig(enable_metrics=True, metrics_window_size=1000)
api = CocApi('YOUR_TOKEN', config=config)

# Get comprehensive metrics after API calls
metrics = api.get_metrics()
print(f"Total requests: {metrics['total_requests']}")
print(f"Average response time: {metrics['avg_response_time']:.2f}ms")
print(f"Cache hit rate: {metrics['cache_hit_rate']:.1%}")
print(f"Error rate: {metrics['error_rate']:.1%}")
```

### 🔌 Middleware System

```python
from cocapi import CocApi
from cocapi.middleware import add_user_agent_middleware, add_request_id_middleware

api = CocApi('YOUR_TOKEN')

# Add built-in middleware
api.add_request_middleware(add_user_agent_middleware("MyApp/1.0"))
api.add_request_middleware(add_request_id_middleware())

# Custom middleware
def add_custom_headers(url, headers, params):
    headers['X-Client-Version'] = '3.0.0'
    return url, headers, params

api.add_request_middleware(add_custom_headers)
```

### 🎯 Enhanced Caching

```python
from cocapi import CocApi, ApiConfig

config = ApiConfig(enable_caching=True, cache_ttl=900)  # 15 minutes
api = CocApi('YOUR_TOKEN', config=config)

# Requests are cached automatically
clan1 = api.clan_tag('#CLAN_TAG')  # Cache miss
clan2 = api.clan_tag('#CLAN_TAG')  # Cache hit

# Cache statistics and management
stats = api.get_cache_stats()
api.clear_cache()
```

### ⚡ Async Rate Limiting

```python
from cocapi import CocApi, ApiConfig
import asyncio

async def high_throughput_example():
    config = ApiConfig(
        enable_rate_limiting=True,
        requests_per_second=10.0,
        burst_limit=20
    )
    
    async with CocApi('YOUR_TOKEN', config=config) as api:
        # Concurrent requests with automatic rate limiting
        clan_tags = ['#CLAN1', '#CLAN2', '#CLAN3']
        tasks = [api.clan_tag(tag) for tag in clan_tags]
        results = await asyncio.gather(*tasks)

asyncio.run(high_throughput_example())
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

## Custom Endpoints 🚀

Use any new SuperCell endpoints immediately without waiting for library updates:

```python
from cocapi import CocApi

api = CocApi('YOUR_API_TOKEN')

# Call new endpoints directly
result = api.custom_endpoint('/new-endpoint')
result = api.custom_endpoint('/clans/search', {'name': 'my clan', 'limit': 10})

# With dynamic Pydantic models
result = api.custom_endpoint('/new-endpoint', use_dynamic_model=True)
print(result.some_field)  # Type-safe access

# Async support
async with CocApi('YOUR_TOKEN') as api:
    result = await api.custom_endpoint('/new-endpoint')
```

## Base URL Configuration 🌐

Modify base URL for testing, proxying, or adapting to API changes:

```python
from cocapi import CocApi, ApiConfig

api = CocApi('YOUR_TOKEN')

# Change base URL (requires force=True for safety)
api.set_base_url("https://api-staging.example.com/v1", force=True)

# Or set during initialization
config = ApiConfig(base_url="https://my-proxy.com/clash/v1")
api = CocApi('YOUR_TOKEN', config=config)

# Reset to official endpoint
api.reset_base_url()
```

## 📈 Performance Benefits

### Key Improvements
- **⚡ Intelligent Caching**: Up to 100% faster for repeated requests
- **🚀 Async Operations**: Handle dozens of concurrent requests efficiently
- **🔁 Smart Retry Logic**: Exponential backoff with configurable policies
- **📈 Monitoring**: Track error rates, response times, and cache performance

### Example Setup
```python
# High-performance configuration
config = ApiConfig(
    enable_caching=True,
    enable_metrics=True,
    max_retries=3
)

api = CocApi('token', config=config)

# Async mode with concurrency
async with CocApi('token', config=config) as api:
    clans = await asyncio.gather(*[
        api.clan_tag(tag) for tag in clan_tags
    ])
```

## Migration Guide 

### 🔄 Upgrading to v3.0.0 - Zero Breaking Changes!

cocapi 3.0.0 maintains 100% backward compatibility. Your existing code continues to work unchanged:

```python
# All existing patterns still work
from cocapi import CocApi

api = CocApi('YOUR_TOKEN')  # ✅ Works
api = CocApi('YOUR_TOKEN', 60, True)  # ✅ Works
clan = api.clan_tag('#CLAN_TAG')  # ✅ Works

# To use new features, just add configuration:
config = ApiConfig(enable_caching=True, cache_ttl=300)
api = CocApi('YOUR_TOKEN', config=config)
```

## 🚀 What's New in v3.0.0

**Major enterprise features** while maintaining 100% backward compatibility:

- **📊 Enterprise Metrics**: Comprehensive API performance monitoring
- **🔌 Middleware System**: Pluggable request/response processing  
- **⚡ Enhanced Async**: Rate limiting and improved concurrency
- **🚀 Custom Endpoints**: Future-proof support for new SuperCell endpoints
- **🎯 Type Safety**: Enhanced type hints and Pydantic model integration
- **🌐 Base URL Config**: Support for staging environments and proxies

### Installation
```bash
pip install --upgrade cocapi
# Or with Pydantic support:
pip install --upgrade 'cocapi[pydantic]'
```

## Previous Releases

**v2.2.x**: Pydantic models, enhanced type safety, async + Pydantic support  
**v2.1.x**: Unified async support, intelligent caching, retry logic, enhanced configuration

## Full API Reference

All methods work identically in both sync and async modes - just use `await` when in async context!

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
