import urllib
from typing import Any, Dict, Tuple
from warnings import warn

import httpx


class CocApi:
    def __init__(self, token: str, timeout: int = 20, status_code: bool = False):
        """
        Initialising requisites
        """
        self.token = token
        self.ENDPOINT = "https://api.clashofclans.com/v1"
        self.timeout = timeout
        self.headers = {
            "authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        self.status_code = status_code
        self.DEFAULT_PARAMS = ("limit", "after", "before")
        self.ERROR_INVALID_PARAM = {
            "result": "error",
            "message": "Invalid params for method",
        }
        test_reponse = self.test()
        if test_reponse.get("result") == "error":
            raise Exception(test_reponse.get("message"))

    def __check_if_dict_invalid(self, params: Dict, valid_items: Tuple = ()) -> bool:
        valid_items = self.DEFAULT_PARAMS if not valid_items else valid_items
        return set(params.keys()).issubset(valid_items)

    def __api_response(
        self, uri: str, params: Dict = {}, status_code: bool = False
    ) -> Dict:
        """
        Function to handle requests,it is possible to use this handler on it's
        own to make request to the api on in case of a new or unsupported api
        Args:
            uri  -> The endpoint uri that needs to be called for the specific function
            params   -> Dictionary of supported params to be filtered
                        with Refer https://developer.clashofclans.com/#/documentation
        Return:
            The json response from the api as is or returns error if broken
        """
        url = f"{self.ENDPOINT}{uri}?{urllib.parse.urlencode(params)}"  # type: ignore
        try:
            response = httpx.get(url=url, headers=self.headers, timeout=self.timeout)
            response_json = response.json()
            if status_code or self.status_code:
                response_json = dict(
                    response_json.update({"status_code": response.status_code})
                )
            return dict(response_json)
        except Exception as e:
            return {
                "result": "error",
                "message": "Something broke, please try again!",
                "exception": str(e),
            }

    def test(self) -> Dict[str, Any]:
        """
        Function to test if the api is up and running.
            Dictionary with a success if api is up error if false
        """
        response = httpx.get(url=self.ENDPOINT, headers=self.headers)
        if response.status_code == 200:
            return {"result": "success", "message": "Api is up and running!"}
        elif response.status_code == 403:
            return {
                "result": "error",
                "message": "Invalid token",
            }
        else:
            response_json = {
                "result": "error",
                "message": "Api is Down!",
            }
            if self.status_code:
                response_json.update(
                    {"status_code": response.status_code}
                )  # type: ignore
            return response_json

    def clan_leaguegroup(self, tag: str) -> Dict:
        """
        Function to Retrieve information about clan's current clan war league group
        """
        return self.__api_response(uri=f"/clans/%23{tag[1:]}/currentwar/leaguegroup")

    def warleague(self, sid: str) -> Dict:
        """
        Function to Retrieve information about a clan war league war.
        """
        return self.__api_response(uri=f"/clanwarleagues/wars/{str(sid)}")

    def clan_war_log(self, tag: str, params: Dict = {}) -> Dict:
        """
        Function to Retrieve clan's clan war log
        """
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(uri=f"/clans/%23{tag[1:]}/warlog", params=params)

    def clan(self, params: Dict = {}) -> Dict:
        """
        Function to Search all clans by name and/or filtering the results using
        various criteria.At least one filtering criteria must be defined and if
        name is used as part of search, it is required to be at least three
        characters long.It is not possible to specify ordering for results so
        clients should not rely on any specific ordering as that may change
        in the future releases of the API.
        """
        valid_items = tuple(
            [
                "name",
                "warFrequency",
                "locationId",
                "minMembers",
                "maxMembers",
                "minClanPoints",
                "minClanLevel",
                "labelIds",
            ]
            + list(self.DEFAULT_PARAMS)
        )
        if not self.__check_if_dict_invalid(params=params, valid_items=valid_items):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(uri="/clans", params=params)

    def clan_current_war(self, tag: str) -> Dict:
        """
        Function to Retrieve information about clan's current clan war
        """
        return self.__api_response(uri=f"/clans/%23{tag[1:]}/currentwar")

    def clan_tag(self, tag: str) -> Dict:
        """
        Function to Get information about a single clan by clan tag.
        Clan tags can be found using clan search operation.
        """
        return self.__api_response(uri=f"/clans/%23{tag[1:]}")

    def clan_members(self, tag: str, params: Dict = {}) -> Dict:
        """
        Function to List clan members
        """
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(uri=f"/clans/%23{tag[1:]}/members", params=params)

    def clan_capitalraidseasons(self, tag: str, params: Dict = {}) -> Dict:
        """
        Function to Retrieve information about clan's current clan war
        """
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(
            uri=f"/clans/%23{tag[1:]}/currentwar/capitalraidseasons", params=params
        )

    def players(self, tag: str) -> Dict:
        """
        Function to Get information about a single player by player tag.
        Player tags can be found either in game or by from clan member lists.
        """
        return self.__api_response(uri=f"/players/%23{tag[1:]}")

    def location_id_clan_rank(self, id: str, params: Dict = {}) -> Dict:
        """
        Function to Get clan rankings for a specific location
        """
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(
            uri=f"/locations/{str(id)}/rankings/clans", params=params
        )

    def location_id_player_rank(self, id: str, params: Dict = {}) -> Dict:
        """
        Function to Get player rankings for a specific location
        """
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(
            uri=f"/locations/{str(id)}/rankings/players", params=params
        )

    def location_clan_versus(self, id: str, params: Dict = {}) -> Dict:
        """
        Function to Get clan versus rankings for a specific location
        """
        warn(
            "This end will be deprecated in the future.",
            DeprecationWarning,
            stacklevel=2,
        )
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM

        return self.__api_response(
            uri=f"/locations/{str(id)}/rankings/clans-versus", params=params
        )

    def location_players_builder_base(self, id: str, params: Dict = {}) -> Dict:
        """
        Function to Get player builder base rankings for a specific location
        """

        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM

        return self.__api_response(
            uri=f"/locations/{str(id)}/rankings/players-builder-base", params=params
        )

    def location_clans_builder_base(self, id: str, params: Dict = {}) -> Dict:
        """
        Function to Get clan builder base rankings for a specific location
        """

        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM

        return self.__api_response(
            uri=f"/locations/{str(id)}/rankings/clans-builder-base", params=params
        )

    def location_player_versus(self, id: str, params: Dict = {}) -> Dict:
        """
        Function to Get player versus rankings for a specific location
        """
        warn(
            "This end will be deprecated in the future.",
            DeprecationWarning,
            stacklevel=2,
        )
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(
            uri=f"/locations/{str(id)}/rankings/players-versus", params=params
        )

    def location(self, params: Dict = {}) -> Dict:
        """
        Function List all available locations
        Will be depricated in the future in favour of locations

        """
        warn(
            "This method will be \
            deprecated in the future in favour\
            of locations to maintain parity with original api",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.locations(params=params)

    def locations(self, params: Dict = {}) -> Dict:
        """
        Function to List all available locations
        """
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(uri="/locations", params=params)

    def location_rankings_capitals(self, id: str, params: Dict = {}) -> Dict:
        """
        Function to Get capital rankings for a specific location
        """
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(
            uri=f"/locations/{str(id)}/rankings/capitals", params=params
        )

    def location_id(self, id: str) -> Dict:
        """
        Function to Get information about specific location
        """
        return self.__api_response(uri=f"/locations/{str(id)}")

    def league(self, params: Dict = {}) -> Dict:
        """
        Function to Get list of leagues
        """
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(uri="/leagues", params=params)

    def league_id(self, id: str) -> Dict:
        """
        Function to Get league information
        """
        return self.__api_response(uri=f"/leagues/{str(id)}")

    def league_season(self, id: str, params: Dict = {}) -> Dict:
        """
        Function to Get league seasons.
        Note that league season information is available only for Legend League.
        """
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(uri=f"/leagues/{str(id)}/seasons", params=params)

    def league_season_id(self, id: str, sid: str, params: Dict = {}) -> Dict:
        """
        Function to Get league season rankings.
        Note that league season information is available only for Legend League.
        """
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(
            uri=f"/leagues/{str(id)}/seasons/{str(sid)}", params=params
        )

    def warleagues(self) -> Dict:
        """
        Function to Get list of clan war leagues
        """
        return self.__api_response(
            uri="/warleagues",
        )

    def warleagues_id(self, league_id: str) -> Dict:
        """
        Function to Get information about a clan war league
        """
        return self.__api_response(
            uri=f"/warleagues/{str(league_id)}",
        )

    def labels_clans(self, params: Dict = {}) -> Dict:
        """
        Function to Get labels for a clan
        """
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(uri="/labels/clans", params=params)

    def labels_players(self, params: Dict = {}) -> Dict:
        """
        Function to Get labels for a player
        """
        if not self.__check_if_dict_invalid(params=params):
            return self.ERROR_INVALID_PARAM
        return self.__api_response(uri="/labels/players/", params=params)

    def goldpass_seasons_current(self) -> Dict:
        """
        Function to Get current gold pass season
        """
        return self.__api_response(uri="/goldpass/seasons/current")

    def player_verifytoken(self, token: str, player_tag: str) -> Dict:
        """
        Function to Verify player token
        """

        try:
            response = httpx.post(
                url=f"{self.ENDPOINT}/players/%23{player_tag[1:]}/verifytoken",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
                data={"token": token},
            )
            response_json = dict(response.json())

            if self.status_code:
                response_json = dict(response_json, status_code=response.status_code)
            return response_json
        except Exception as e:
            return {
                "status": "error",
                "message": "Something broke",
                "exception": str(e),
            }
