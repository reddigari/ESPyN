import requests
import json
import os.path

from .constants import ENDPOINT
from .team import Team
from .matchup import Matchup
from .utils import *


class League:

    def __init__(self, league_id, season=None, cache_dir=None):
        self._req = requests
        self._cache = False
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
        if self._cache:
            data = self._load_cached_matchup(week, team_id)
            if data:
                return data["boxscore"]
        url = self._endpoint + "boxscore"
        params = self._url_params()
        params["matchupPeriodId"] = week
        params["teamId"] = team_id
        res = self._req.get(url, params=params)
        data = res.json()
        # cache data if using cache and week is over
        if (self._cache) & (week < current_week()):
            # shitty way to cache the data under both team IDs
            m_info = data["boxscore"]["scheduleItems"][0]["matchups"][0]
            team_ids = [m_info["homeTeamId"], m_info["awayTeamId"]]
            self._cache_matchup(data, week, team_ids)
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

    ##########################################################
    # methods for reading and writing matchups from/to cache #
    ##########################################################
    def _get_cache_filename(self, week, team_id):
        fname = "{0}_{1:0>2}_{2:0>2}.json".format(
            self.league_id, week, team_id
        )
        return os.path.join(self._cache_dir, fname)

    def _load_cached_file(self, fname):
        if os.path.exists(fname):
            with open(fname, "r") as f:
                return json.load(f)
        return None

    def _load_cached_matchup(self, week, team_id):
        fname = self._get_cache_filename(week, team_id)
        return self._load_cached_file(fname)

    def _cache_matchup(self, data, week, team_ids):
        # save twice, once under each team ID
        for team_id in team_ids:
            fname = self._get_cache_filename(week, team_id)
            with open(fname, "w") as f:
                json.dump(data, f)
