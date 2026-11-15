"""
Army link parsing and building.

Army links look like
``https://link.clashofclans.com/en?action=CopyArmy&army=u10x0-2x3s1x9``
where ``u`` introduces troops and ``s`` spells as ``-``-separated ``{count}x{id}``
pairs. Any other sections (e.g. heroes, pets, equipment) are kept verbatim in
:attr:`Army.extra` so nothing is lost.
"""

import re
import urllib.parse
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .static_data import StaticData

TROOP_ID_BASE = 4_000_000
SPELL_ID_BASE = 26_000_000

_SECTION = re.compile(r"([a-z])((?:\d+x\d+(?:-\d+x\d+)*)|[\d\-x]*)")
_PAIR = re.compile(r"(\d+)x(\d+)")


@dataclass
class ArmyUnit:
    id: int  # short id as used in the link
    count: int
    name: str | None = None  # resolved when StaticData is supplied


@dataclass
class Army:
    troops: list[ArmyUnit] = field(default_factory=list)
    spells: list[ArmyUnit] = field(default_factory=list)
    extra: dict[str, str] = field(default_factory=dict)

    def to_link(self, lang: str = "en") -> str:
        return build_army_link(self, lang)


def parse_army_link(link: str, static_data: "StaticData | None" = None) -> Army:
    """Parse an army link (or just its ``army=`` value) into an :class:`Army`."""
    link = link.strip()
    if "army=" in link:
        query = urllib.parse.urlparse(link).query or link
        values = urllib.parse.parse_qs(query).get("army")
        if not values:
            raise ValueError(f"No army parameter in link: {link!r}")
        code = values[0]
    else:
        code = link
    if not code or not re.fullmatch(r"(?:[a-z][\d\-x]*)+", code):
        raise ValueError(f"Invalid army code: {code!r}")

    army = Army()
    for letter, body in _SECTION.findall(code):
        if letter in ("u", "s"):
            units = [ArmyUnit(id=int(i), count=int(c)) for c, i in _PAIR.findall(body)]
            if static_data is not None:
                category, base = (
                    ("troops", TROOP_ID_BASE)
                    if letter == "u"
                    else ("spells", SPELL_ID_BASE)
                )
                for u in units:
                    item = static_data.by_id(category, base + u.id)
                    u.name = item["name"] if item else None
            (army.troops if letter == "u" else army.spells).extend(units)
        else:
            army.extra[letter] = body
    return army


def build_army_link(army: Army, lang: str = "en") -> str:
    """Build an army link from an :class:`Army`."""

    def fmt(units: list[ArmyUnit]) -> str:
        return "-".join(f"{u.count}x{u.id}" for u in units)

    code = ""
    if army.troops:
        code += "u" + fmt(army.troops)
    if army.spells:
        code += "s" + fmt(army.spells)
    for letter, body in army.extra.items():
        code += letter + body
    return f"https://link.clashofclans.com/{lang}?action=CopyArmy&army={code}"
