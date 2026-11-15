"""
Static game data (troops, spells, heroes, pets, equipment, leagues, ...).

The official API serves no static game data, so this module loads a JSON file in
the format published by the ClashKing project
(https://github.com/ClashKingInc/clashy.py, ``coc/static/static_data.json``, MIT).
Nothing is bundled: pass a path, or call :meth:`StaticData.download` to fetch and
cache it (explicit opt-in network access).

Example::

    from cocapi import StaticData

    sd = StaticData.download()            # cached at ~/.cocapi/static_data.json
    sd.by_name("troops", "Barbarian")
    sd.by_id("heroes", 28000000)
    sd.names("equipment")
"""

import json
from pathlib import Path
from typing import Any

DEFAULT_URL = (
    "https://raw.githubusercontent.com/ClashKingInc/clashy.py/main/"
    "coc/static/static_data.json"
)
DEFAULT_PATH = Path.home() / ".cocapi" / "static_data.json"


class StaticData:
    """Name/ID lookups over a static game data JSON document."""

    def __init__(self, data: dict[str, Any]):
        self.data = data
        self._by_name: dict[str, dict[str, dict[str, Any]]] = {}
        self._by_id: dict[str, dict[int, dict[str, Any]]] = {}

    @classmethod
    def load(cls, path: str | Path | None = None) -> "StaticData":
        """Load from a local JSON file (default ``~/.cocapi/static_data.json``)."""
        p = Path(path) if path else DEFAULT_PATH
        with open(p, encoding="utf-8") as f:
            return cls(json.load(f))

    @classmethod
    def download(
        cls,
        path: str | Path | None = None,
        url: str = DEFAULT_URL,
        refresh: bool = False,
        timeout: float = 60.0,
    ) -> "StaticData":
        """Download the data (unless already cached) and load it.

        Args:
            path: Where to cache the file (default ``~/.cocapi/static_data.json``).
            url: Source URL.
            refresh: Re-download even if the cache file exists.
        """
        import httpx

        p = Path(path) if path else DEFAULT_PATH
        if refresh or not p.exists():
            resp = httpx.get(url, timeout=timeout, follow_redirects=True)
            resp.raise_for_status()
            json.loads(resp.content)  # validate before writing
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(resp.content)
        return cls.load(p)

    def categories(self) -> list[str]:
        return [k for k, v in self.data.items() if isinstance(v, list)]

    def items(self, category: str) -> list[dict[str, Any]]:
        value = self.data.get(category, [])
        return value if isinstance(value, list) else []

    def names(self, category: str) -> list[str]:
        return [i["name"] for i in self.items(category) if "name" in i]

    def by_name(self, category: str, name: str) -> dict[str, Any] | None:
        """Case-insensitive lookup by name."""
        index = self._by_name.get(category)
        if index is None:
            index = {i["name"].lower(): i for i in self.items(category) if "name" in i}
            self._by_name[category] = index
        return index.get(name.lower())

    def by_id(self, category: str, item_id: int) -> dict[str, Any] | None:
        index = self._by_id.get(category)
        if index is None:
            index = {i["_id"]: i for i in self.items(category) if "_id" in i}
            self._by_id[category] = index
        return index.get(item_id)

    # Convenience accessors
    def troop(self, name: str) -> dict[str, Any] | None:
        return self.by_name("troops", name)

    def spell(self, name: str) -> dict[str, Any] | None:
        return self.by_name("spells", name)

    def hero(self, name: str) -> dict[str, Any] | None:
        return self.by_name("heroes", name)

    def pet(self, name: str) -> dict[str, Any] | None:
        return self.by_name("pets", name)

    def equipment(self, name: str) -> dict[str, Any] | None:
        return self.by_name("equipment", name)

    def max_level(
        self, category: str, name: str, townhall: int | None = None
    ) -> int | None:
        """Highest level of an item (optionally limited by Town Hall level)."""
        item = self.by_name(category, name)
        if not item:
            return None
        levels = item.get("levels", [])
        if townhall is not None:
            levels = [
                lv for lv in levels if (lv.get("required_townhall") or 0) <= townhall
            ]
        return max((lv["level"] for lv in levels), default=None)
