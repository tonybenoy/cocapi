<p>
    <a href="https://github.com/tonybenoy/cocapi/actions">
        <img src="https://github.com/tonybenoy/cocapi/workflows/mypy/badge.svg" alt="Test Status" height="20">
    </a>
    <a href="https://pypi.org/project/cocapi/"><img src="https://img.shields.io/pypi/v/cocapi" alt="Pypi version" height="21"></a>
</p>
<p>
    <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.6+-blue.svg" alt="Python version" height="17"></a>
    <a href="https://github.com/tonybenoy/cocapi/blob/master/LICENSE"><img src="https://img.shields.io/github/license/tonybenoy/cocapi" alt="License" height="17"></a>
    <a href="https://github.com/psf/black">
        <img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Codestyle Black" height="17">
    </a>
</p>

# ClashOfClansAPI 

Python Wrapper for SuperCells Clash Of Clans API

Get Token from https://developer.clashofclans.com/

# Install

> pip3 install cocapi


# Features and usage examples

### Initialize

Required to set up the class

```python
from cocapi import CocApi

token = 'YOUR_API_TOKEN'
timeout=1 #requests timeout

api=CocApi(token,timeout)
```




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

### Warleague Information
```python
api.clan_warleague(war_tag)
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




## Labels

### List Clan Labels
```python
api.clan_leaguegroup(tag)
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
