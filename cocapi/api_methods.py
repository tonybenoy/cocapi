"""
All Clash of Clans API endpoint methods
"""

import urllib.parse
from typing import TYPE_CHECKING, Any, Awaitable, Dict, Optional, Union

from .utils import clean_tag

if TYPE_CHECKING:
    # Only for type checking - avoid circular imports
    pass


class ApiMethods:
    """Mixin class containing all COC API endpoint methods"""

    # These methods will be provided by the inheriting class (CocApi)
    def _validate_params(self, params: Optional[Dict[str, Any]]) -> bool:
        """Implemented in CocApi class"""
        raise NotImplementedError

    def _api_response(
        self,
        uri: str,
        params: Optional[Dict[str, Any]] = None,
        use_dynamic_model: bool = False,
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Implemented in CocApi class"""
        raise NotImplementedError

    def _api_post_response(
        self,
        uri: str,
        json_body: Dict[str, Any],
        params: Optional[Dict[str, Any]] = None,
        use_dynamic_model: bool = False,
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Implemented in CocApi class"""
        raise NotImplementedError

    def _deprecated_api_response(
        self,
        uri: str,
        method_name: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Implemented in CocApi class"""
        raise NotImplementedError

    # This will be set by the inheriting class
    ERROR_INVALID_PARAM: Dict[str, str]

    def clan_tag(
        self, tag: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get clan information"""
        if not self._validate_params(params):
            return self.ERROR_INVALID_PARAM

        tag = clean_tag(tag)
        return self._api_response(f"/clans/%23{urllib.parse.quote(tag)}", params)

    def clan_members(
        self, clan_tag: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get clan members"""
        if not self._validate_params(params):
            return self.ERROR_INVALID_PARAM

        clan_tag = clean_tag(clan_tag)
        return self._api_response(
            f"/clans/%23{urllib.parse.quote(clan_tag)}/members", params
        )

    def clan_current_war(
        self, clan_tag: str
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get current clan war information"""
        clan_tag = clean_tag(clan_tag)
        return self._api_response(
            f"/clans/%23{urllib.parse.quote(clan_tag)}/currentwar"
        )

    def clan_war_log(
        self, clan_tag: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get clan war log"""
        if not self._validate_params(params):
            return self.ERROR_INVALID_PARAM

        clan_tag = clean_tag(clan_tag)
        return self._api_response(
            f"/clans/%23{urllib.parse.quote(clan_tag)}/warlog", params
        )

    def clan_leaguegroup(
        self, clan_tag: str
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get clan's current clan war league group"""
        clan_tag = clean_tag(clan_tag)
        return self._api_response(
            f"/clans/%23{urllib.parse.quote(clan_tag)}/currentwar/leaguegroup"
        )

    def clan_capitalraidseasons(
        self, clan_tag: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get clan capital raid seasons"""
        if not self._validate_params(params):
            return self.ERROR_INVALID_PARAM

        clan_tag = clean_tag(clan_tag)
        return self._api_response(
            f"/clans/%23{urllib.parse.quote(clan_tag)}/capitalraidseasons", params
        )

    def players(
        self, player_tag: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get player information"""
        if not self._validate_params(params):
            return self.ERROR_INVALID_PARAM

        player_tag = clean_tag(player_tag)
        return self._api_response(
            f"/players/%23{urllib.parse.quote(player_tag)}", params
        )

    def clan(
        self,
        name: str = "",
        limit: int = 10,
        params: Optional[Dict[str, Any]] = None,
        war_frequency: Optional[str] = None,
        location_id: Optional[int] = None,
        min_members: Optional[int] = None,
        max_members: Optional[int] = None,
        min_clan_points: Optional[int] = None,
        min_clan_level: Optional[int] = None,
        label_ids: Optional[str] = None,
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Search clans by name and/or filtering criteria

        Args:
            name: Search clans by name (min 3 characters if used)
            limit: Limit number of results
            params: Optional pagination params (after, before)
            war_frequency: Filter by war frequency
            location_id: Filter by location identifier
            min_members: Filter by minimum number of members
            max_members: Filter by maximum number of members
            min_clan_points: Filter by minimum clan points
            min_clan_level: Filter by minimum clan level
            label_ids: Comma separated list of label IDs to filter by
        """
        if not self._validate_params(params):
            return self.ERROR_INVALID_PARAM

        search_params: Dict[str, Any] = {"name": name, "limit": limit}

        if war_frequency is not None:
            search_params["warFrequency"] = war_frequency
        if location_id is not None:
            search_params["locationId"] = location_id
        if min_members is not None:
            search_params["minMembers"] = min_members
        if max_members is not None:
            search_params["maxMembers"] = max_members
        if min_clan_points is not None:
            search_params["minClanPoints"] = min_clan_points
        if min_clan_level is not None:
            search_params["minClanLevel"] = min_clan_level
        if label_ids is not None:
            search_params["labelIds"] = label_ids

        if params:
            search_params.update(params)

        return self._api_response("/clans", search_params)

    def warleague(
        self, war_tag: str
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get information about a clan war league war"""
        war_tag = clean_tag(war_tag)
        return self._api_response(
            f"/clanwarleagues/wars/%23{urllib.parse.quote(war_tag)}"
        )

    def location(
        self, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get list of locations"""
        if not self._validate_params(params):
            return self.ERROR_INVALID_PARAM
        return self._api_response("/locations", params)

    def location_id(
        self, location_id: str
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get information about a location"""
        return self._api_response(f"/locations/{str(location_id)}")

    def location_id_clan_rank(
        self, location_id: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get clan rankings for a location"""
        if not self._validate_params(params):
            return self.ERROR_INVALID_PARAM
        return self._api_response(
            f"/locations/{str(location_id)}/rankings/clans", params
        )

    def location_id_player_rank(
        self, location_id: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get player rankings for a location"""
        if not self._validate_params(params):
            return self.ERROR_INVALID_PARAM
        return self._api_response(
            f"/locations/{str(location_id)}/rankings/players", params
        )

    def location_clan_versus(
        self, location_id: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get clan versus rankings for a location (possibly deprecated)"""
        if not self._validate_params(params):
            return self.ERROR_INVALID_PARAM
        return self._deprecated_api_response(
            f"/locations/{str(location_id)}/rankings/clans-versus",
            "location_clan_versus",
            params,
        )

    def location_player_versus(
        self, location_id: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get player versus rankings for a location (possibly deprecated)"""
        if not self._validate_params(params):
            return self.ERROR_INVALID_PARAM
        return self._deprecated_api_response(
            f"/locations/{str(location_id)}/rankings/players-versus",
            "location_player_versus",
            params,
        )

    def location_clans_builder_base(
        self, location_id: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get clan builder base rankings for a location"""
        if not self._validate_params(params):
            return self.ERROR_INVALID_PARAM
        return self._api_response(
            f"/locations/{str(location_id)}/rankings/clans-builder-base", params
        )

    def location_players_builder_base(
        self, location_id: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get player builder base rankings for a location"""
        if not self._validate_params(params):
            return self.ERROR_INVALID_PARAM
        return self._api_response(
            f"/locations/{str(location_id)}/rankings/players-builder-base", params
        )

    def league(
        self, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get list of leagues"""
        if not self._validate_params(params):
            return self.ERROR_INVALID_PARAM
        return self._api_response("/leagues", params)

    def league_id(
        self, league_id: str
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get league information"""
        return self._api_response(f"/leagues/{str(league_id)}")

    def league_season(
        self, id: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get league seasons (Legend League only)"""
        if not self._validate_params(params):
            return self.ERROR_INVALID_PARAM
        return self._api_response(f"/leagues/{str(id)}/seasons", params)

    def league_season_id(
        self, id: str, sid: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get league season rankings (Legend League only)"""
        if not self._validate_params(params):
            return self.ERROR_INVALID_PARAM
        return self._api_response(f"/leagues/{str(id)}/seasons/{str(sid)}", params)

    def warleagues(self) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get list of clan war leagues"""
        return self._api_response("/warleagues")

    def warleagues_id(
        self, league_id: str
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get information about a clan war league"""
        return self._api_response(f"/warleagues/{str(league_id)}")

    def labels_clans(
        self, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get labels for clans"""
        if not self._validate_params(params):
            return self.ERROR_INVALID_PARAM
        return self._api_response("/labels/clans", params)

    def labels_players(
        self, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get labels for players"""
        if not self._validate_params(params):
            return self.ERROR_INVALID_PARAM
        return self._api_response("/labels/players", params)

    def capitalleagues(
        self, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get list of capital leagues"""
        if not self._validate_params(params):
            return self.ERROR_INVALID_PARAM
        return self._api_response("/capitalleagues", params)

    def capitalleagues_id(
        self, league_id: str
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get information about a capital league"""
        return self._api_response(f"/capitalleagues/{str(league_id)}")

    def builderbaseleagues(
        self, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get list of builder base leagues"""
        if not self._validate_params(params):
            return self.ERROR_INVALID_PARAM
        return self._api_response("/builderbaseleagues", params)

    def builderbaseleagues_id(
        self, league_id: str
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get information about a builder base league"""
        return self._api_response(f"/builderbaseleagues/{str(league_id)}")

    def goldpass(
        self, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get information about the current gold pass season"""
        if not self._validate_params(params):
            return self.ERROR_INVALID_PARAM
        return self._api_response("/goldpass/seasons/current", params)

    # --- New endpoints ---

    def verify_player_token(
        self, player_tag: str, token: str
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Verify a player API token to confirm account ownership

        Args:
            player_tag: Tag of the player
            token: API token found in the player's game settings
        """
        player_tag = clean_tag(player_tag)
        return self._api_post_response(
            f"/players/%23{urllib.parse.quote(player_tag)}/verifytoken",
            {"token": token},
        )

    def leaguetiers(
        self, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get list of league tiers"""
        if not self._validate_params(params):
            return self.ERROR_INVALID_PARAM
        return self._api_response("/leaguetiers", params)

    def leaguetiers_id(
        self, league_tier_id: str
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get information about a specific league tier"""
        return self._api_response(f"/leaguetiers/{str(league_tier_id)}")

    def location_capital_rankings(
        self, location_id: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        """Get capital rankings for a location"""
        if not self._validate_params(params):
            return self.ERROR_INVALID_PARAM
        return self._api_response(
            f"/locations/{str(location_id)}/rankings/capitals", params
        )
