import requests

from .constants import *
from .team import Team
from .matchup import Matchup
from .utils import *


class League:

    def __init__(self, league_id, season=None, cache_dir=None):
        self._req = requests
        self.cache = False
        self._endpoint = ENDPOINT
        self.league_id = league_id
        if season is None:
            self.season = current_season()
        else:
            self.season = season
        if cache_dir:
            self._cache = True
            self._cache_dir = cache_dir
        # fetch league data
        self._data = self._get_league_data()
        # set stat code to points map
        self.scoring_dict = dict()
        for item in self._data["scoringItems"]:
            self.scoring_dict[item['statId']] = item['points']
        # get team data and set teams attr
        team_data = self._data["teams"].items()
        self.n_teams = len(team_data)
        self._teams = {int(i): Team(td, self) for i, td in team_data}

    @property
    def teams(self):
        return list(self._teams.values())

    def get_team(self, team_id):
        return self._teams[team_id]

    def _url_params(self, **kwargs):
        params = dict()
        params["seasonId"] = self.season
        params["leagueId"] = self.league_id
        for k, v in kwargs.items():
            params[k] = v
        return params

    def _get_league_data(self):
        url = self._endpoint + "leagueSettings"
        params = self._url_params()
        res = self._req.get(url, params=params)
        data = res.json()
        return data["leaguesettings"]

    def _get_matchup_data(self, week, team_id):
        url = self._endpoint + "boxscore"
        params = self._url_params()
        params["matchupPeriodId"] = week
        params["teamId"] = team_id
        res = self._req.get(url, params=params)
        data = res.json()
        return data["boxscore"]

    def get_matchup(self, week, team_id):
        data = self._get_matchup_data(week, team_id)
        matchup = Matchup(data, self)
        return matchup

    def get_all_matchups(self, week):
        matchups = []
        team_ids = [team.team_id for team in self.teams]
        while len(team_ids) > 0:
            t_id = team_ids[0]
            matchup = self.get_matchup(week, t_id)
            matchups.append(matchup)
            for team_id in matchup.team_ids:
                team_ids.pop(team_ids.index(team_id))
        return matchups
