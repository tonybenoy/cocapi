from cocapi.cocapi import CocApi as CocApi
from cocapi.config import ApiConfig as ApiConfig

# For backward compatibility - AsyncCocApi is now unified into CocApi
AsyncCocApi = CocApi

# Optional Pydantic models - only imported if pydantic is available
try:
    from cocapi.models import (
        Achievement,
        ApiResponse,
        Clan,
        # Type aliases
        ClanDict,
        ClanMember,
        ClanSearchResult,
        Hero,
        HeroEquipment,
        League,
        Location,
        LocationRankingList,
        Player,
        PlayerDict,
        Spell,
        Troop,
    )

    __all__ = [
        "CocApi",
        "ApiConfig",
        "AsyncCocApi",
        "Clan",
        "Player",
        "ClanMember",
        "League",
        "Location",
        "Achievement",
        "Troop",
        "Hero",
        "HeroEquipment",
        "Spell",
        "ClanSearchResult",
        "LocationRankingList",
        "ApiResponse",
        "ClanDict",
        "PlayerDict",
    ]
except ImportError:
    # Pydantic not available, only export basic API
    __all__ = ["CocApi", "ApiConfig", "AsyncCocApi"]

name = "cocapi"
