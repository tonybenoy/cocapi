import httpx
import json


class CocApi:
    # Initialising requisites
    def __init__(self, token, timeout=20):
        self.token = token
        self.endpoint = 'https://api.clashofclans.com/v1'
        self.timeout = timeout
        self.headers = {'authorization': 'Bearer %s' % token,
                        'Accept': 'application/json'}

    # Function to handle requests
    def api_response(self, uri, params):
        url = self.endpoint + uri
        if params:
            params = json.dumps(params)
        try:
            response = httpx.get(
                url, data=params, headers=self.headers, timeout=self.timeout)
            return response.json()
        except:
            return '404'

    # Funtion to Search all clans by name and/or filtering the results using various criteria.
    # At least one filtering criteria must be defined and if name is used as part of search, it is required to be at least three characters long.
    # It is not possible to specify ordering for results so clients should not rely on any specific ordering as that may change in the future releases of the API.

    def clan(self, params=None):
        uri = '/clans'
        return self.api_response(uri, params)

    # Function to Get information about a single clan by clan tag.
    # Clan tags can be found using clan search operation.
    def clan_tag(self, tag, params=None):
        uri = '/clans/%23'+tag[1:]
        return self.api_response(uri, params)

    # Function to List clan members
    def clan_members(self, tag, params=None):
        uri = '/clans/%23'+tag[1:]+'/members'
        return self.api_response(uri, params)

    # Function to Retrieve clan's clan war log
    def clan_war_log(self, tag, params=None):
        uri = '/clans/%23'+tag[1:]+'/warlog'
        return self.api_response(uri, params)

    # Function to Retrieve information about clan's current clan war
    def clan_current_war(self, tag, params=None):
        uri = '/clans/%23'+tag[1:]+'/currentwar'
        return self.api_response(uri, params)

    # Function to Retrieve information about clan's current clan war league group
    def clan_leaguegroup(self, tag, params=None):
        uri = '/clans/%23'+tag[1:]+'/currentwar/leaguegroup'
        return self.api_response(uri, params)

    # Function to Retrieve information about a clan war league war.
    def warleague(self, sid, params=None):
        uri = '/clanwarleagues/wars/'+str(sid)
        return self.api_response(uri, params)

    # Function to Get information about a single player by player tag. Player tags can be found either in game or by from clan member lists.
    def players(self, tag, params=None):
        uri = '/players/%23'+tag[1:]
        return self.api_response(uri, params)

    # Function List all available locations
    def location(self, params=None):
        uri = '/locations'
        return self.api_response(uri, params)

    # Function to Get information about specific location
    def location_id(self, id, params=None):
        uri = '/locations/'+str(id)
        return self.api_response(uri, params)

    # Function to Get clan rankings for a specific location
    def location_id_clan_rank(self, id, params=None):
        uri = '/locations/'+str(id)+'/rankings/clans'
        return self.api_response(uri, params)

    # Function to Get player rankings for a specific location
    def location_id_player_rank(self, id, params=None):
        uri = '/locations/'+str(id)+'/rankings/players'
        return self.api_response(uri, params)

    # Function to Get clan versus rankings for a specific location
    def location_clan_versus(self, id, params=None):
        uri = '/locations/'+str(id)+'/rankings/clans-versus'
        return self.api_response(uri, params)

    # Function to Get player versus rankings for a specific location
    def location_player_versus(self, id, params=None):
        uri = '/locations/'+str(id)+'/rankings/players-versus'
        return self.api_response(uri, params)

    # Function to Get list of leagues
    def league(self, params=None):
        uri = '/leagues'
        return self.api_response(uri, params)

    # Function to Get league information
    def league_id(self, id, params=None):
        uri = '/leagues/'+str(id)
        return self.api_response(uri, params)

    # Function to Get league seasons. Note that league season information is available only for Legend League.
    def league_season(self, id, params=None):
        uri = '/leagues/'+str(id)+'/seasons'
        return self.api_response(uri, params)

    # Function to Get league season rankings. Note that league season information is available only for Legend League.
    def league_season_id(self, id, sid, params=None):
        uri = '/leagues/'+str(id)+'/seasons/'+str(sid)
        return self.api_response(uri, params)

    # Function to Get labels for a clan
    def labels_clans(self, params=None):
        uri = '/labels/clans'
        return self.api_response(uri, params)

    # Function to Get labels for a player
    def labels_players(self, params=None):
        uri = '/labels/players/'
        return self.api_response(uri, params)
