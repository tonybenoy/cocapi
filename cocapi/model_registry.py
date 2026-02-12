"""
Registry mapping API endpoint patterns to Pydantic model classes.

Uses regex matching to map actual endpoint URIs (with tags/IDs) to the
correct response model. Returns None for unknown endpoints so the caller
can fall back to dynamic model generation.
"""

import re
from typing import Any, Dict, List, Optional, Tuple, Type

try:
    from pydantic import BaseModel

    from .schemas import (
        BuilderBaseLeague,
        CapitalLeague,
        Clan,
        ClanBuilderBaseRankingEntry,
        ClanCapitalRaidSeason,
        ClanCapitalRankingEntry,
        ClanMember,
        ClanRankingEntry,
        ClanSearchEntry,
        ClanWar,
        ClanWarLeagueGroup,
        ClanWarLogEntry,
        GoldPassSeason,
        Label,
        League,
        LeagueSeason,
        LeagueTier,
        Location,
        Paging,
        Player,
        PlayerBuilderBaseRankingEntry,
        PlayerRankingEntry,
        VerifyTokenResponse,
        WarLeague,
    )

    SCHEMAS_AVAILABLE = True
except ImportError:
    SCHEMAS_AVAILABLE = False

# Tag pattern: %23 followed by URL-encoded tag chars
_TAG = r"%23[A-Za-z0-9%]+"
_ID = r"[0-9]+"

# Each entry: (compiled regex, model class, is_paginated, item_model_or_None)
# For paginated endpoints: is_paginated=True, item model is the list item type
# For single-object endpoints: is_paginated=False, model is the response type
_ENDPOINT_PATTERNS: List[Tuple[re.Pattern[str], Any, bool]] = []

if SCHEMAS_AVAILABLE:
    _PATTERNS_RAW: List[Tuple[str, Any, bool]] = [
        # --- Clans ---
        (rf"^/clans/{_TAG}$", Clan, False),
        (rf"^/clans/{_TAG}/members$", ClanMember, True),
        (rf"^/clans/{_TAG}/warlog$", ClanWarLogEntry, True),
        (rf"^/clans/{_TAG}/currentwar$", ClanWar, False),
        (rf"^/clans/{_TAG}/currentwar/leaguegroup$", ClanWarLeagueGroup, False),
        (rf"^/clans/{_TAG}/capitalraidseasons$", ClanCapitalRaidSeason, True),
        (r"^/clans$", ClanSearchEntry, True),
        # --- Players ---
        (rf"^/players/{_TAG}$", Player, False),
        (rf"^/players/{_TAG}/verifytoken$", VerifyTokenResponse, False),
        # --- Locations ---
        (r"^/locations$", Location, True),
        (rf"^/locations/{_ID}$", Location, False),
        (rf"^/locations/{_ID}/rankings/clans$", ClanRankingEntry, True),
        (rf"^/locations/{_ID}/rankings/players$", PlayerRankingEntry, True),
        (
            rf"^/locations/{_ID}/rankings/clans-builder-base$",
            ClanBuilderBaseRankingEntry,
            True,
        ),
        (
            rf"^/locations/{_ID}/rankings/players-builder-base$",
            PlayerBuilderBaseRankingEntry,
            True,
        ),
        (rf"^/locations/{_ID}/rankings/capitals$", ClanCapitalRankingEntry, True),
        # --- Leagues ---
        (r"^/leagues$", League, True),
        (rf"^/leagues/{_ID}$", League, False),
        (rf"^/leagues/{_ID}/seasons$", LeagueSeason, True),
        (rf"^/leagues/{_ID}/seasons/[\w-]+$", PlayerRankingEntry, True),
        # --- Capital Leagues ---
        (r"^/capitalleagues$", CapitalLeague, True),
        (rf"^/capitalleagues/{_ID}$", CapitalLeague, False),
        # --- Builder Base Leagues ---
        (r"^/builderbaseleagues$", BuilderBaseLeague, True),
        (rf"^/builderbaseleagues/{_ID}$", BuilderBaseLeague, False),
        # --- League Tiers ---
        (r"^/leaguetiers$", LeagueTier, True),
        (rf"^/leaguetiers/{_ID}$", LeagueTier, False),
        # --- War Leagues ---
        (r"^/warleagues$", WarLeague, True),
        (rf"^/warleagues/{_ID}$", WarLeague, False),
        # --- Clan War Leagues (individual war) ---
        (rf"^/clanwarleagues/wars/{_TAG}$", ClanWarLeagueGroup, False),
        # --- Gold Pass ---
        (r"^/goldpass/seasons/current$", GoldPassSeason, False),
        # --- Labels ---
        (r"^/labels/clans$", Label, True),
        (r"^/labels/players$", Label, True),
    ]

    _ENDPOINT_PATTERNS = [
        (re.compile(pattern), model, paginated)
        for pattern, model, paginated in _PATTERNS_RAW
    ]


def get_model_for_endpoint(
    uri: str,
) -> Optional[Dict[str, Any]]:
    """
    Look up the model class for an endpoint URI.

    Args:
        uri: The API endpoint path (e.g., "/clans/%23ABC123")

    Returns:
        Dict with "model" (the model class) and "paginated" (bool),
        or None if no matching model is found.
    """
    if not SCHEMAS_AVAILABLE:
        return None

    for pattern, model_class, is_paginated in _ENDPOINT_PATTERNS:
        if pattern.match(uri):
            return {"model": model_class, "paginated": is_paginated}

    return None


def resolve_response(response: Dict[str, Any], uri: str) -> Any:
    """
    Resolve an API response dict into a Pydantic model if a matching
    schema exists. Returns the original dict if no model is found or
    if the response is an error.

    Args:
        response: The raw API response dict
        uri: The endpoint URI used for the request

    Returns:
        A Pydantic model instance, or the original dict as fallback.
    """
    if not SCHEMAS_AVAILABLE:
        return response

    if response.get("result") == "error":
        return response

    match = get_model_for_endpoint(uri)
    if match is None:
        return None  # Signal caller to use dynamic fallback

    model_class: Type[BaseModel] = match["model"]
    is_paginated: bool = match["paginated"]

    try:
        if is_paginated:
            # Validate each item in the list
            items = response.get("items", [])
            validated_items = [model_class.model_validate(item) for item in items]
            paging = None
            if "paging" in response:
                paging = Paging.model_validate(response["paging"])
            # Return a dict-like structure with validated models
            return {
                "items": validated_items,
                "paging": paging,
            }
        else:
            return model_class.model_validate(response)
    except Exception:
        return None  # Signal caller to use dynamic fallback
