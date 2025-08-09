"""
Pydantic models for Clash of Clans API responses.

This module provides optional Pydantic models for structured data validation
and IDE support when working with Clash of Clans API responses.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ClanType(str, Enum):
    """Clan recruitment type."""

    OPEN = "open"
    INVITE_ONLY = "inviteOnly"
    CLOSED = "closed"


class WarFrequency(str, Enum):
    """Clan war frequency."""

    ALWAYS = "always"
    MORE_THAN_ONCE_PER_WEEK = "moreThanOncePerWeek"
    ONCE_PER_WEEK = "oncePerWeek"
    LESS_THAN_ONCE_PER_WEEK = "lessThanOncePerWeek"
    NEVER = "never"
    UNKNOWN = "unknown"


class Role(str, Enum):
    """Member role in clan."""

    MEMBER = "member"
    ADMIN = "admin"
    CO_LEADER = "coLeader"
    LEADER = "leader"


class WarPreference(str, Enum):
    """War preference setting."""

    IN = "in"
    OUT = "out"


class Village(str, Enum):
    """Village type for achievements."""

    HOME = "home"
    BUILDER_BASE = "builderBase"
    CLAN_CAPITAL = "clanCapital"


class Location(BaseModel):
    """Geographic location information."""

    id: int
    name: str
    is_country: bool = Field(alias="isCountry")


class BadgeUrls(BaseModel):
    """Badge/icon URLs in different sizes."""

    small: str
    medium: str
    large: str


class IconUrls(BaseModel):
    """Icon URLs in different sizes."""

    small: Optional[str] = None
    tiny: Optional[str] = None
    medium: Optional[str] = None


class League(BaseModel):
    """League information."""

    id: int
    name: str
    icon_urls: Optional[IconUrls] = Field(None, alias="iconUrls")


class CapitalLeague(BaseModel):
    """Capital league information."""

    id: int
    name: str


class WarLeague(BaseModel):
    """War league information."""

    id: int
    name: str


class PlayerHouseElement(BaseModel):
    """Player house decoration element."""

    type: str
    id: int


class PlayerHouse(BaseModel):
    """Player house information."""

    elements: List[PlayerHouseElement]


class ClanInfo(BaseModel):
    """Basic clan information (used in player data)."""

    tag: str
    name: str
    clan_level: int = Field(alias="clanLevel")
    badge_urls: BadgeUrls = Field(alias="badgeUrls")


class Label(BaseModel):
    """Label information."""

    id: int
    name: str
    icon_urls: IconUrls = Field(alias="iconUrls")


class Achievement(BaseModel):
    """Player achievement."""

    name: str
    stars: int
    value: int
    target: int
    info: str
    completion_info: Optional[str] = Field(None, alias="completionInfo")
    village: Village


class Troop(BaseModel):
    """Troop information."""

    name: str
    level: int
    max_level: int = Field(alias="maxLevel")
    village: Village
    super_troop_is_active: Optional[bool] = Field(None, alias="superTroopIsActive")


class Hero(BaseModel):
    """Hero information."""

    name: str
    level: int
    max_level: int = Field(alias="maxLevel")
    village: Village


class HeroEquipment(BaseModel):
    """Hero equipment information."""

    name: str
    level: int
    max_level: int = Field(alias="maxLevel")
    village: Village


class Spell(BaseModel):
    """Spell information."""

    name: str
    level: int
    max_level: int = Field(alias="maxLevel")
    village: Village


class ClanMember(BaseModel):
    """Clan member information."""

    tag: str
    name: str
    role: Role
    town_hall_level: int = Field(alias="townHallLevel")
    exp_level: int = Field(alias="expLevel")
    league: Optional[League] = None
    trophies: int
    builder_base_trophies: int = Field(alias="builderBaseTrophies")
    clan_rank: int = Field(alias="clanRank")
    previous_clan_rank: int = Field(alias="previousClanRank")
    donations: int
    donations_received: int = Field(alias="donationsReceived")
    player_house: Optional[PlayerHouse] = Field(None, alias="playerHouse")


class ClanCapital(BaseModel):
    """Clan capital information."""

    capital_hall_level: int = Field(alias="capitalHallLevel")
    districts: List[Dict[str, Any]]  # Complex nested structure


class Clan(BaseModel):
    """Complete clan information."""

    tag: str
    name: str
    type: ClanType
    description: Optional[str] = None
    location: Optional[Location] = None
    is_family_friendly: bool = Field(alias="isFamilyFriendly")
    badge_urls: BadgeUrls = Field(alias="badgeUrls")
    clan_level: int = Field(alias="clanLevel")
    clan_points: int = Field(alias="clanPoints")
    clan_builder_base_points: int = Field(alias="clanBuilderBasePoints")
    clan_capital_points: int = Field(alias="clanCapitalPoints")
    capital_league: Optional[CapitalLeague] = Field(None, alias="capitalLeague")
    required_trophies: int = Field(alias="requiredTrophies")
    war_frequency: WarFrequency = Field(alias="warFrequency")
    war_win_streak: int = Field(alias="warWinStreak")
    war_wins: int = Field(alias="warWins")
    is_war_log_public: bool = Field(alias="isWarLogPublic")
    war_league: Optional[WarLeague] = Field(None, alias="warLeague")
    members: int
    member_list: Optional[List[ClanMember]] = Field(None, alias="memberList")
    labels: Optional[List[Label]] = None
    required_builder_base_trophies: int = Field(alias="requiredBuilderBaseTrophies")
    required_townhall_level: int = Field(alias="requiredTownhallLevel")
    clan_capital: Optional[ClanCapital] = Field(None, alias="clanCapital")
    chat_language: Optional[Dict[str, Any]] = Field(None, alias="chatLanguage")


class Player(BaseModel):
    """Complete player information."""

    tag: str
    name: str
    town_hall_level: int = Field(alias="townHallLevel")
    town_hall_weapon_level: Optional[int] = Field(None, alias="townHallWeaponLevel")
    exp_level: int = Field(alias="expLevel")
    trophies: int
    best_trophies: int = Field(alias="bestTrophies")
    war_stars: int = Field(alias="warStars")
    attack_wins: int = Field(alias="attackWins")
    defense_wins: int = Field(alias="defenseWins")
    builder_hall_level: Optional[int] = Field(None, alias="builderHallLevel")
    builder_base_trophies: Optional[int] = Field(None, alias="builderBaseTrophies")
    best_builder_base_trophies: Optional[int] = Field(
        None, alias="bestBuilderBaseTrophies"
    )
    role: Optional[Role] = None
    war_preference: Optional[WarPreference] = Field(None, alias="warPreference")
    donations: int
    donations_received: int = Field(alias="donationsReceived")
    clan_capital_contributions: int = Field(alias="clanCapitalContributions")
    clan: Optional[ClanInfo] = None
    builder_base_league: Optional[League] = Field(None, alias="builderBaseLeague")
    achievements: Optional[List[Achievement]] = None
    player_house: Optional[PlayerHouse] = Field(None, alias="playerHouse")
    labels: Optional[List[Label]] = None
    troops: Optional[List[Troop]] = None
    heroes: Optional[List[Hero]] = None
    hero_equipment: Optional[List[HeroEquipment]] = Field(None, alias="heroEquipment")
    spells: Optional[List[Spell]] = None


class ApiResponse(BaseModel):
    """Generic API response wrapper."""

    result: str
    message: str
    status_code: Optional[int] = Field(None, alias="status_code")
    error_type: Optional[str] = Field(None, alias="error_type")


class ClanSearchResult(BaseModel):
    """Clan search results."""

    items: List[Clan]
    paging: Optional[Dict[str, Any]] = None


class LocationRanking(BaseModel):
    """Location ranking entry."""

    tag: str
    name: str
    location: Optional[Location] = None
    badge_urls: Optional[BadgeUrls] = Field(None, alias="badgeUrls")
    clan_level: Optional[int] = Field(None, alias="clanLevel")
    members: Optional[int] = None
    trophies: Optional[int] = None
    rank: int
    previous_rank: int = Field(alias="previousRank")


class LocationRankingList(BaseModel):
    """Location ranking results."""

    items: List[LocationRanking]
    paging: Optional[Dict[str, Any]] = None


# Type aliases for backward compatibility
ClanDict = Dict[str, Any]
PlayerDict = Dict[str, Any]
