"""
Pydantic response models for the Clash of Clans API.

All fields are Optional with defaults to handle API variations gracefully.
Models are based on real API responses captured February 2026.

Usage:
    from cocapi import CocApi, ApiConfig, Clan, Player

    config = ApiConfig(use_pydantic_models=True)
    api = CocApi("token", config=config)
    clan = api.clan_tag("#2PP")  # Returns Clan model
    print(clan.name, clan.clanLevel)
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

try:
    from pydantic import BaseModel, ConfigDict

    PYDANTIC_AVAILABLE = True
except ImportError as e:
    raise ImportError(
        "Pydantic is required for cocapi schemas. "
        "Install with: pip install 'cocapi[pydantic]'"
    ) from e

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Shared / nested models
# ---------------------------------------------------------------------------


class BadgeUrls(BaseModel):
    """Clan badge image URLs in multiple sizes."""

    model_config = ConfigDict(extra="allow")

    small: str | None = None
    large: str | None = None
    medium: str | None = None


class IconUrls(BaseModel):
    """Icon image URLs for leagues, labels, and other entities."""

    model_config = ConfigDict(extra="allow")

    small: str | None = None
    tiny: str | None = None
    medium: str | None = None
    large: str | None = None


class Cursors(BaseModel):
    """Pagination cursors for traversing list endpoints."""

    model_config = ConfigDict(extra="allow")

    before: str | None = None
    after: str | None = None


class Paging(BaseModel):
    """Paging metadata returned with paginated list responses."""

    model_config = ConfigDict(extra="allow")

    cursors: Cursors | None = None


class PaginatedList(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    model_config = ConfigDict(extra="allow")

    items: list[Any] = []
    paging: Paging | None = None


class Location(BaseModel):
    """A geographic location (country or region) used for rankings."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    name: str | None = None
    isCountry: bool | None = None
    countryCode: str | None = None


class Label(BaseModel):
    """A label that can be assigned to clans or players."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    name: str | None = None
    iconUrls: IconUrls | None = None


# ---------------------------------------------------------------------------
# League models
# ---------------------------------------------------------------------------


class League(BaseModel):
    """A player's trophy league (e.g. Legend League, Titan I)."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    name: str | None = None
    iconUrls: IconUrls | None = None


class LeagueTier(BaseModel):
    """A tier within a league (sub-division)."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    name: str | None = None
    iconUrls: IconUrls | None = None


class CapitalLeague(BaseModel):
    """Clan Capital league ranking."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    name: str | None = None


class BuilderBaseLeague(BaseModel):
    """Builder Base league ranking."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    name: str | None = None


class WarLeague(BaseModel):
    """Clan War League tier (e.g. Champion I, Master II)."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    name: str | None = None


class LeagueSeason(BaseModel):
    """A league season identifier (e.g. ``2026-02``)."""

    model_config = ConfigDict(extra="allow")

    id: str | None = None


class ChatLanguage(BaseModel):
    """A clan's configured chat language."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    name: str | None = None
    languageCode: str | None = None


# ---------------------------------------------------------------------------
# Player models
# ---------------------------------------------------------------------------


class PlayerHouseElement(BaseModel):
    """A single decorative element of a player's house."""

    model_config = ConfigDict(extra="allow")

    type: str | None = None
    id: int | None = None


class PlayerHouse(BaseModel):
    """Player house decoration data."""

    model_config = ConfigDict(extra="allow")

    elements: list[PlayerHouseElement] = []


class Troop(BaseModel):
    """A troop in a player's army (home or builder village)."""

    model_config = ConfigDict(extra="allow")

    name: str | None = None
    level: int | None = None
    maxLevel: int | None = None
    village: str | None = None
    superTroopIsActive: bool | None = None


class Hero(BaseModel):
    """A hero unit (e.g. Barbarian King, Archer Queen)."""

    model_config = ConfigDict(extra="allow")

    name: str | None = None
    level: int | None = None
    maxLevel: int | None = None
    village: str | None = None
    equipment: list[Any] | None = None


class HeroEquipment(BaseModel):
    """Equipment item that can be assigned to a hero."""

    model_config = ConfigDict(extra="allow")

    name: str | None = None
    level: int | None = None
    maxLevel: int | None = None
    village: str | None = None


class Spell(BaseModel):
    """A spell in a player's spell factory."""

    model_config = ConfigDict(extra="allow")

    name: str | None = None
    level: int | None = None
    maxLevel: int | None = None
    village: str | None = None


class Achievement(BaseModel):
    """A player achievement with progress and star count."""

    model_config = ConfigDict(extra="allow")

    name: str | None = None
    stars: int | None = None
    value: int | None = None
    target: int | None = None
    info: str | None = None
    completionInfo: str | None = None
    village: str | None = None


class PlayerClan(BaseModel):
    """Compact clan info embedded in player responses."""

    model_config = ConfigDict(extra="allow")

    tag: str | None = None
    name: str | None = None
    clanLevel: int | None = None
    badgeUrls: BadgeUrls | None = None


class LegendSeason(BaseModel):
    """A single Legend League season result."""

    model_config = ConfigDict(extra="allow")

    trophies: int | None = None
    id: str | None = None
    rank: int | None = None


class LegendStatistics(BaseModel):
    """Legend League statistics including current, previous, and best seasons."""

    model_config = ConfigDict(extra="allow")

    legendTrophies: int | None = None
    currentSeason: LegendSeason | None = None
    previousSeason: LegendSeason | None = None
    bestSeason: LegendSeason | None = None


class Player(BaseModel):
    """Full player profile from the ``/players/{tag}`` endpoint."""

    model_config = ConfigDict(extra="allow")

    tag: str | None = None
    name: str | None = None
    townHallLevel: int | None = None
    expLevel: int | None = None
    trophies: int | None = None
    bestTrophies: int | None = None
    warStars: int | None = None
    attackWins: int | None = None
    defenseWins: int | None = None
    builderHallLevel: int | None = None
    builderBaseTrophies: int | None = None
    bestBuilderBaseTrophies: int | None = None
    role: str | None = None
    warPreference: str | None = None
    donations: int | None = None
    donationsReceived: int | None = None
    clanCapitalContributions: int | None = None
    clan: PlayerClan | None = None
    league: League | None = None
    leagueTier: LeagueTier | None = None
    builderBaseLeague: BuilderBaseLeague | None = None
    legendStatistics: LegendStatistics | None = None
    achievements: list[Achievement] = []
    labels: list[Label] = []
    troops: list[Troop] = []
    heroes: list[Hero] = []
    heroEquipment: list[HeroEquipment] = []
    spells: list[Spell] = []
    playerHouse: PlayerHouse | None = None


class VerifyTokenResponse(BaseModel):
    """Response from the player token verification endpoint."""

    model_config = ConfigDict(extra="allow")

    tag: str | None = None
    token: str | None = None
    status: str | None = None


# ---------------------------------------------------------------------------
# Clan models
# ---------------------------------------------------------------------------


class ClanMember(BaseModel):
    """A member entry within a clan's member list."""

    model_config = ConfigDict(extra="allow")

    tag: str | None = None
    name: str | None = None
    role: str | None = None
    townHallLevel: int | None = None
    expLevel: int | None = None
    league: League | None = None
    leagueTier: LeagueTier | None = None
    trophies: int | None = None
    builderBaseTrophies: int | None = None
    clanRank: int | None = None
    previousClanRank: int | None = None
    donations: int | None = None
    donationsReceived: int | None = None
    playerHouse: PlayerHouse | None = None
    builderBaseLeague: BuilderBaseLeague | None = None


class ClanCapitalDistrict(BaseModel):
    """A district within a clan's Clan Capital."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    name: str | None = None
    districtHallLevel: int | None = None


class ClanCapital(BaseModel):
    """Clan Capital data including hall level and districts."""

    model_config = ConfigDict(extra="allow")

    capitalHallLevel: int | None = None
    districts: list[ClanCapitalDistrict] = []


class Clan(BaseModel):
    """Full clan profile from the ``/clans/{tag}`` endpoint."""

    model_config = ConfigDict(extra="allow")

    tag: str | None = None
    name: str | None = None
    type: str | None = None
    description: str | None = None
    location: Location | None = None
    isFamilyFriendly: bool | None = None
    badgeUrls: BadgeUrls | None = None
    clanLevel: int | None = None
    clanPoints: int | None = None
    clanBuilderBasePoints: int | None = None
    clanCapitalPoints: int | None = None
    capitalLeague: CapitalLeague | None = None
    requiredTrophies: int | None = None
    requiredBuilderBaseTrophies: int | None = None
    requiredTownhallLevel: int | None = None
    warFrequency: str | None = None
    warWinStreak: int | None = None
    warWins: int | None = None
    warTies: int | None = None
    warLosses: int | None = None
    isWarLogPublic: bool | None = None
    warLeague: WarLeague | None = None
    members: int | None = None
    memberList: list[ClanMember] = []
    labels: list[Label] = []
    clanCapital: ClanCapital | None = None
    chatLanguage: ChatLanguage | None = None


class ClanSearchEntry(BaseModel):
    """Clan entry returned from the search endpoint (no memberList)."""

    model_config = ConfigDict(extra="allow")

    tag: str | None = None
    name: str | None = None
    type: str | None = None
    location: Location | None = None
    isFamilyFriendly: bool | None = None
    badgeUrls: BadgeUrls | None = None
    clanLevel: int | None = None
    clanPoints: int | None = None
    clanBuilderBasePoints: int | None = None
    clanCapitalPoints: int | None = None
    capitalLeague: CapitalLeague | None = None
    requiredTrophies: int | None = None
    requiredBuilderBaseTrophies: int | None = None
    requiredTownhallLevel: int | None = None
    warFrequency: str | None = None
    warWinStreak: int | None = None
    warWins: int | None = None
    isWarLogPublic: bool | None = None
    warLeague: WarLeague | None = None
    members: int | None = None
    labels: list[Label] = []
    chatLanguage: ChatLanguage | None = None


# ---------------------------------------------------------------------------
# War models
# ---------------------------------------------------------------------------


class WarAttack(BaseModel):
    """A single attack in a clan war."""

    model_config = ConfigDict(extra="allow")

    order: int | None = None
    attackerTag: str | None = None
    defenderTag: str | None = None
    stars: int | None = None
    destructionPercentage: float | None = None
    duration: int | None = None


class WarMember(BaseModel):
    """A clan member participating in a war."""

    model_config = ConfigDict(extra="allow")

    tag: str | None = None
    name: str | None = None
    townhallLevel: int | None = None
    mapPosition: int | None = None
    opponentAttacks: int | None = None
    bestOpponentAttack: WarAttack | None = None
    attacks: list[WarAttack] = []


class WarClan(BaseModel):
    """A clan's war data including members and attack summary."""

    model_config = ConfigDict(extra="allow")

    tag: str | None = None
    name: str | None = None
    badgeUrls: BadgeUrls | None = None
    clanLevel: int | None = None
    attacks: int | None = None
    stars: int | None = None
    destructionPercentage: float | None = None
    expEarned: int | None = None
    members: list[WarMember] = []


class ClanWar(BaseModel):
    """Current or past clan war from the ``/clans/{tag}/currentwar`` endpoint."""

    model_config = ConfigDict(extra="allow")

    state: str | None = None
    teamSize: int | None = None
    attacksPerMember: int | None = None
    battleModifier: str | None = None
    preparationStartTime: str | None = None
    startTime: str | None = None
    endTime: str | None = None
    clan: WarClan | None = None
    opponent: WarClan | None = None


class ClanWarLogEntry(BaseModel):
    """A single entry in a clan's war log."""

    model_config = ConfigDict(extra="allow")

    result: str | None = None
    endTime: str | None = None
    teamSize: int | None = None
    attacksPerMember: int | None = None
    battleModifier: str | None = None
    clan: WarClan | None = None
    opponent: WarClan | None = None


# ---------------------------------------------------------------------------
# Clan War League models
# ---------------------------------------------------------------------------


class ClanWarLeagueMember(BaseModel):
    """A member in a Clan War League group."""

    model_config = ConfigDict(extra="allow")

    tag: str | None = None
    townHallLevel: int | None = None
    name: str | None = None


class ClanWarLeagueClan(BaseModel):
    """A clan participating in a Clan War League group."""

    model_config = ConfigDict(extra="allow")

    tag: str | None = None
    clanLevel: int | None = None
    name: str | None = None
    members: list[ClanWarLeagueMember] = []
    badgeUrls: BadgeUrls | None = None


class ClanWarLeagueRound(BaseModel):
    """A round within a Clan War League season containing war tags."""

    model_config = ConfigDict(extra="allow")

    warTags: list[str] = []


class ClanWarLeagueGroup(BaseModel):
    """Full Clan War League group with clans and rounds."""

    model_config = ConfigDict(extra="allow")

    tag: str | None = None
    state: str | None = None
    season: str | None = None
    clans: list[ClanWarLeagueClan] = []
    rounds: list[ClanWarLeagueRound] = []


# ---------------------------------------------------------------------------
# Capital Raid Season models
# ---------------------------------------------------------------------------


class ClanCapitalRaidSeasonMember(BaseModel):
    """A member's participation in a Capital Raid season."""

    model_config = ConfigDict(extra="allow")

    tag: str | None = None
    name: str | None = None
    attacks: int | None = None
    attackLimit: int | None = None
    bonusAttackLimit: int | None = None
    capitalResourcesLooted: int | None = None


class ClanCapitalRaidSeason(BaseModel):
    """A Clan Capital raid season with attack/defense logs and rewards."""

    model_config = ConfigDict(extra="allow")

    state: str | None = None
    startTime: str | None = None
    endTime: str | None = None
    capitalTotalLoot: int | None = None
    raidsCompleted: int | None = None
    totalAttacks: int | None = None
    enemyDistrictsDestroyed: int | None = None
    offensiveReward: int | None = None
    defensiveReward: int | None = None
    members: list[ClanCapitalRaidSeasonMember] = []
    attackLog: list[Any] = []
    defenseLog: list[Any] = []


# ---------------------------------------------------------------------------
# Ranking models
# ---------------------------------------------------------------------------


class ClanRankingClan(BaseModel):
    """Compact clan info in ranking entries."""

    model_config = ConfigDict(extra="allow")

    tag: str | None = None
    name: str | None = None
    badgeUrls: BadgeUrls | None = None


class ClanRankingEntry(BaseModel):
    """A clan's entry in the trophy rankings leaderboard."""

    model_config = ConfigDict(extra="allow")

    tag: str | None = None
    name: str | None = None
    location: Location | None = None
    badgeUrls: BadgeUrls | None = None
    clanLevel: int | None = None
    members: int | None = None
    clanPoints: int | None = None
    rank: int | None = None
    previousRank: int | None = None


class ClanBuilderBaseRankingEntry(BaseModel):
    """A clan's entry in the Builder Base rankings leaderboard."""

    model_config = ConfigDict(extra="allow")

    tag: str | None = None
    name: str | None = None
    location: Location | None = None
    badgeUrls: BadgeUrls | None = None
    clanLevel: int | None = None
    members: int | None = None
    rank: int | None = None
    previousRank: int | None = None
    clanBuilderBasePoints: int | None = None


class ClanCapitalRankingEntry(BaseModel):
    """A clan's entry in the Clan Capital rankings leaderboard."""

    model_config = ConfigDict(extra="allow")

    tag: str | None = None
    name: str | None = None
    location: Location | None = None
    badgeUrls: BadgeUrls | None = None
    clanLevel: int | None = None
    members: int | None = None
    rank: int | None = None
    previousRank: int | None = None
    clanCapitalPoints: int | None = None


class PlayerRankingEntry(BaseModel):
    """A player's entry in the trophy rankings leaderboard."""

    model_config = ConfigDict(extra="allow")

    tag: str | None = None
    name: str | None = None
    expLevel: int | None = None
    trophies: int | None = None
    attackWins: int | None = None
    defenseWins: int | None = None
    rank: int | None = None
    previousRank: int | None = None
    clan: ClanRankingClan | None = None
    league: League | None = None
    leagueTier: LeagueTier | None = None


class PlayerBuilderBaseRankingEntry(BaseModel):
    """A player's entry in the Builder Base rankings leaderboard."""

    model_config = ConfigDict(extra="allow")

    tag: str | None = None
    name: str | None = None
    expLevel: int | None = None
    rank: int | None = None
    previousRank: int | None = None
    builderBaseTrophies: int | None = None
    clan: ClanRankingClan | None = None
    builderBaseLeague: BuilderBaseLeague | None = None


# ---------------------------------------------------------------------------
# Gold Pass
# ---------------------------------------------------------------------------


class GoldPassSeason(BaseModel):
    """Current Gold Pass season start and end times."""

    model_config = ConfigDict(extra="allow")

    startTime: str | None = None
    endTime: str | None = None
