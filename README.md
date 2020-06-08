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

# ClashOfClansAPI </br>
Python Wrapper for SuperCells Clash Of Clans API </br>
Get Token from https://developer.clashofclans.com/</br>

# Install

> pip3 install cocapi


# Usage </br>

## Features and usage examples

### Initialize

Required to set up the class

```python
from cocapi import CocApi

token = 'YOUR_API_TOKEN'
timeout=1 #requests timeout

api=CocApi(token,timeout)
```

### Get all information about a clan
```python
api.clan_tag(tag) #example tag "#9UOVJJ9J"
```
returns various clan information

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
#### Members only
```python
api.clan_members(tag)
```
returns membersList information from api.clan_tag(tag) under "items" in dict

### War Log
```python
api.clan_war_log(tag)
```
returns clan war log under "items" in dict

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
### Get best move
```python
api.clan_current_war(tag)
```
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

*Note versions below 2.0.0 are not supported anymore*
