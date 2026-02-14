"""
Clash of Clans API Wrapper - cocapi v4.0.0

A Python wrapper for the official Clash of Clans API with enhanced features:
- Async and sync support
- Request caching with TTL
- Automatic retries with exponential backoff
- Request metrics and monitoring
- Middleware system for request/response processing
- Dynamic Pydantic model generation
- Custom endpoint support for future API changes
- Configurable base URL with safety warnings

Basic Usage:
    from cocapi import CocApi

    api = CocApi("your_api_token")
    clan = api.clan_tag("#CLAN_TAG")

Advanced Usage:
    from cocapi import CocApi, ApiConfig

    config = ApiConfig(
        enable_caching=True,
        cache_ttl=600,
        max_retries=3,
        enable_metrics=True
    )

    api = CocApi("your_token", config=config)

Async Usage:
    from cocapi import CocApi, ApiConfig

    async def get_clan_info():
        config = ApiConfig(enable_rate_limiting=True)
        async with CocApi("token", config=config) as api:
            clan = await api.clan_tag("#CLAN_TAG")
            return clan
"""

# Main API class - primary interface
from .async_client import AsyncCocApiCore, AsyncRateLimiter

# Advanced components for power users
from .cache import CacheManager
from .client import CocApi

# Configuration classes
from .config import ApiConfig, CacheEntry, RequestMetric

# Key management (credential-based auth)
from .key_manager import (
    AsyncKeyManager,
    InvalidCredentials,
    KeyManagerError,
    SyncKeyManager,
)
from .metrics import MetricsTracker

# Common middleware functions
from .middleware import (
    MiddlewareManager,
    add_debug_logging_middleware,
    add_request_id_middleware,
    add_response_size_middleware,
    add_response_timestamp_middleware,
    add_user_agent_middleware,
)

# Utility functions
from .models import create_dynamic_model, get_pydantic_info, validate_pydantic_available
from .utils import build_url, clean_tag, validate_params

# Pydantic response models (optional - only available when pydantic is installed)
try:
    from .schemas import (
        Achievement,
        BadgeUrls,
        BuilderBaseLeague,
        CapitalLeague,
        ChatLanguage,
        Clan,
        ClanBuilderBaseRankingEntry,
        ClanCapital,
        ClanCapitalRaidSeason,
        ClanCapitalRankingEntry,
        ClanMember,
        ClanRankingEntry,
        ClanSearchEntry,
        ClanWar,
        ClanWarLeagueClan,
        ClanWarLeagueGroup,
        ClanWarLeagueMember,
        ClanWarLeagueRound,
        ClanWarLogEntry,
        GoldPassSeason,
        Hero,
        HeroEquipment,
        IconUrls,
        Label,
        League,
        LeagueSeason,
        LeagueTier,
        Location,
        Paging,
        Player,
        PlayerBuilderBaseRankingEntry,
        PlayerClan,
        PlayerHouse,
        PlayerRankingEntry,
        Spell,
        Troop,
        VerifyTokenResponse,
        WarAttack,
        WarClan,
        WarLeague,
        WarMember,
    )

    _SCHEMAS_AVAILABLE = True
except (ImportError, SyntaxError):
    _SCHEMAS_AVAILABLE = False

# Version info
__version__ = "4.0.1"
__author__ = "Tony Benoy"
__email__ = "me@tonybenoy.com"

# Main exports - what users typically need
__all__ = [
    # Primary API class
    "CocApi",
    # Configuration
    "ApiConfig",
    # Advanced components (for power users)
    "AsyncCocApiCore",
    "CacheManager",
    "MetricsTracker",
    "MiddlewareManager",
    "AsyncRateLimiter",
    # Key management
    "SyncKeyManager",
    "AsyncKeyManager",
    "KeyManagerError",
    "InvalidCredentials",
    # Data structures
    "CacheEntry",
    "RequestMetric",
    # Utility functions
    "create_dynamic_model",
    "validate_pydantic_available",
    "get_pydantic_info",
    "clean_tag",
    "build_url",
    "validate_params",
    # Common middleware
    "add_user_agent_middleware",
    "add_request_id_middleware",
    "add_debug_logging_middleware",
    "add_response_timestamp_middleware",
    "add_response_size_middleware",
    # Version info
    "__version__",
    "__author__",
    "__email__",
]

# Conditionally add Pydantic model exports
if _SCHEMAS_AVAILABLE:
    __all__ += [
        # Response models (require pydantic)
        "Achievement",
        "BadgeUrls",
        "BuilderBaseLeague",
        "CapitalLeague",
        "ChatLanguage",
        "Clan",
        "ClanBuilderBaseRankingEntry",
        "ClanCapital",
        "ClanCapitalRaidSeason",
        "ClanCapitalRankingEntry",
        "ClanMember",
        "ClanRankingEntry",
        "ClanSearchEntry",
        "ClanWar",
        "ClanWarLeagueClan",
        "ClanWarLeagueGroup",
        "ClanWarLeagueMember",
        "ClanWarLeagueRound",
        "ClanWarLogEntry",
        "GoldPassSeason",
        "Hero",
        "HeroEquipment",
        "IconUrls",
        "Label",
        "League",
        "LeagueSeason",
        "LeagueTier",
        "Location",
        "Paging",
        "Player",
        "PlayerBuilderBaseRankingEntry",
        "PlayerClan",
        "PlayerHouse",
        "PlayerRankingEntry",
        "Spell",
        "Troop",
        "VerifyTokenResponse",
        "WarAttack",
        "WarClan",
        "WarLeague",
        "WarMember",
    ]

name = "cocapi"
