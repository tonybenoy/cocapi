# Game Data, Army Links & Event Windows

## Static Game Data

The official API serves no static game data, so `StaticData` loads a JSON file in the [ClashKing](https://github.com/ClashKingInc/clashy.py) `static_data.json` format. Nothing is bundled; `download()` is an explicit opt-in network call that caches to `~/.cocapi/static_data.json`.

```python
from cocapi import StaticData

sd = StaticData.download()          # or StaticData.load("path/to/static_data.json")
sd.troop("Barbarian")
sd.by_id("heroes", 28000000)
sd.names("equipment")
sd.max_level("troops", "Giant", townhall=12)
```

## Army Links

```python
from cocapi import parse_army_link, build_army_link

army = parse_army_link(
    "https://link.clashofclans.com/en?action=CopyArmy&army=u10x0-2x3s1x9",
    static_data=sd,                 # optional: resolves names
)
army.troops[0]                      # ArmyUnit(id=0, count=10, name='Barbarian')
build_army_link(army)
```

Unknown sections (heroes, pets, ...) are kept in `army.extra`.

## Event Windows (UTC)

```python
from cocapi import clan_games_window, raid_weekend_window, legend_day_window

start, end = raid_weekend_window()
```

Windows assume the current game schedule (Clan Games 22nd–28th 08:00, Raid Weekend Fri 07:00–Mon 07:00, Legend day reset 05:00). League season dates are not computed; use `api.league_season()`.
