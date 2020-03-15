import httpx
import json


class CocApi:

    def __init__(self, token: str, timeout: int = 20):
        """
        Initialising requisites
        """
        self.token = token
        self.endpoint = 'https://api.clashofclans.com/v1'
        self.timeout = timeout
        self.headers = {'authorization': 'Bearer %s' % token,
                        'Accept': 'application/json'}

    def api_response(self, uri: str, params: dict = {}):
        """
        Function to handle requests,it is possible to use this handler on it's
        own to make request to the api on in case of a new or unsupported api
        Args:
            uri      -> The endpoint uri that needs to be called for the specific function
            params   -> Dictionary of supported params to be filtered
                        with Refer https://developer.clashofclans.com/#/documentation
        Return:
            The json response from the api as is or returns error if broken
        """
        url = self.endpoint + uri
        params = {}
        if params:
            params = json.dumps(params)
        try:
            response = httpx.get(
                url=url, params=params, headers=self.headers, timeout=self.timeout)
            return response.json()
        except:
            return {'result': 'error', 'message': 'Something broke'}

    def test(self) -> dict:
        """
        Function to test if the api is up and running.
        """
        response = httpx.get(url=self.endpoint, headers=self.headers)
        if response.status_code == 200:
            return {'result': 'success', 'message': 'Api is up and running!'}
        else:
            return {'result': 'error', 'message': 'Api is Down!'}

    def clan(self, params: dict = None) -> dict:
        """
        Function to Search all clans by name and/or filtering the results using various criteria.
        At least one filtering criteria must be defined and if name is used as part of search, it is required to be at least three characters long.
        It is not possible to specify ordering for results so clients should not rely on any specific ordering as that may change in the future releases of the API.
        """
        uri = '/clans'
        return self.api_response(uri=uri, params=params)

    def clan_tag(self, tag: str, params: dict = None) -> dict:
        """
        Function to Get information about a single clan by clan tag.
        Clan tags can be found using clan search operation.
        """
        uri = '/clans/%23'+tag[1:]
        return self.api_response(uri=uri, params=params)

    def clan_members(self, tag: str, params: dict = None) -> dict:
        """
        Function to List clan members
        """
        uri = '/clans/%23'+tag[1:]+'/members'
        return self.api_response(uri=uri, params)

    def clan_war_log(self, tag: str, params: dict = None) -> dict:
        """
        Function to Retrieve clan's clan war log
        """
        uri = '/clans/%23'+tag[1:]+'/warlog'
        return self.api_response(uri=uri, params=params)

    def clan_current_war(self, tag: str, params: dict = None) -> dict:
        """
        Function to Retrieve information about clan's current clan war
        """
        uri = '/clans/%23'+tag[1:]+'/currentwar'
        return self.api_response(uri=uri, params=params)

    def clan_leaguegroup(self, tag: str, params: dict = None) -> dict:
        """
        Function to Retrieve information about clan's current clan war league group
        """
        uri = '/clans/%23'+tag[1:]+'/currentwar/leaguegroup'
        return self.api_response(uri=uri, params=params)

    def warleague(self, sid: str, params: dict = None) -> dict:
        """
        Function to Retrieve information about a clan war league war.
        """
        uri = '/clanwarleagues/wars/'+str(sid)
        return self.api_response(uri=uri, params=params)

    def players(self, tag: str, params: dict = None) -> dict:
        """
        Function to Get information about a single player by player tag. Player tags can be found either in game or by from clan member lists.
        """
        uri = '/players/%23'+tag[1:]
        return self.api_response(uri=uri, params=params)

    def location(self, params: dict = None) -> dict:
        """
        Function List all available locations
        """
        uri = '/locations'
        return self.api_response(uri=uri, params=params)

    def location_id(self, id: str, params: dict = None) -> dict:
        """
        Function to Get information about specific location
        """
        uri = '/locations/'+str(id)
        return self.api_response(uri=uri, params=params)

    def location_id_clan_rank(self, id: str, params: dict = None) -> dict:
        """"
        Function to Get clan rankings for a specific location
        """"
        uri = '/locations/'+str(id)+'/rankings/clans'
        return self.api_response(uri=uri, params=params)

    def location_id_player_rank(self, id: str, params: dict = None) -> dict:
        """
        Function to Get player rankings for a specific location
        """
        uri = '/locations/'+str(id)+'/rankings/players'
        return self.api_response(uri=uri, params=params)

    def location_clan_versus(self, id: str, params: dict = None) -> dict:
        """
        Function to Get clan versus rankings for a specific location
        """
        uri = '/locations/'+str(id)+'/rankings/clans-versus'
        return self.api_response(uri=uri, params=params)

    def location_player_versus(self, id: str, params: dict = None) -> dict:
        """
        Function to Get player versus rankings for a specific location
        """
        uri = '/locations/'+str(id)+'/rankings/players-versus'
        return self.api_response(uri=uri, params=params)

    def league(self, params: dict = None) -> dict:
        """
        Function to Get list of leagues
        """
        uri = '/leagues'
        return self.api_response(uri=uri, params=params)

    def league_id(self, id: str, params: dict = None) -> dict:
        """
        Function to Get league information
        """
        uri = '/leagues/'+str(id)
        return self.api_response(uri=uri, params=params)

    def league_season(self, id: str, params: dict = None) -> dict:
        """
        Function to Get league seasons. Note that league season information is available only for Legend League.
        """
        uri = '/leagues/'+str(id)+'/seasons'
        return self.api_response(uri=uri, params=params)

    def league_season_id(self, id: str, sid: str, params: dict = None) -> dict:
        """
        Function to Get league season rankings. Note that league season information is available only for Legend League.
        """
        uri = '/leagues/'+str(id)+'/seasons/'+str(sid)
        return self.api_response(uri=uri, params=params)

    def labels_clans(self, params: dict = None) -> dict:
        """
        Function to Get labels for a clan
        """
        uri = '/labels/clans'
        return self.api_response(uri=uri, params)

    def labels_players(self, params: dict = None) -> dict:
        """
        Function to Get labels for a player
        """
        uri = '/labels/players/'
        return self.api_response(uri=uri, params)
