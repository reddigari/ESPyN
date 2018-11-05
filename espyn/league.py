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
            if not os.path.exists(cache_dir):
                raise ValueError("The given cache directory does not exist.")
            self._cache = True
            self._cache_dir = cache_dir
        # fetch league data
        self._data = self._get_league_data()
        self.name = self._data["name"]
        self.size = self._data["size"]
        # set stat code to points map
        self.scoring_dict = dict()
        for item in self._data["scoringItems"]:
            self.scoring_dict[item['statId']] = item['points']
        # instantiate teams
        team_data = self._data["teams"]
        self._teams = {int(i): Team(td, self) for i, td in team_data.items()}
        # instantiate matchups and add indices to _matchup_dict
        self._matchups = []
        self._matchup_dict = {}
        index = 0
        for t_id, td in team_data.items():
            for si in td["scheduleItems"]:
                matchup = Matchup(si, self)
                week = matchup.week
                # add matchup and index for both teams if it doesn't exist
                if self._lookup_matchup(week, int(t_id)) is None:
                    self._matchups.append(matchup)
                    week_dict = self._matchup_dict.setdefault(week, dict())
                    for i in matchup.team_ids:
                        week_dict[i] = index
                    index += 1

    def __repr__(self):
        return "ESPN League {} - {} - {} teams".format(
            self.league_id, self.name, self.size
        )

    @property
    def teams(self):
        teams = list(self._teams.values())
        return sorted(teams, key=lambda i: i.team_id)

    def get_team_by_id(self, team_id):
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
        if res.status_code != 200:
            raise ValueError("That league ID did not return any data.")
        data = res.json()
        return data["leaguesettings"]

    def _get_boxscore_data(self, matchup):
        if self._cache:
            data = self._load_cached_boxscore(matchup)
            if data:
                return data["boxscore"]
        url = self._endpoint + "boxscore"
        params = self._url_params()
        params["matchupPeriodId"] = matchup.week
        params["teamId"] = matchup.home_team_id
        print("Requesting data over the web.")
        res = self._req.get(url, params=params)
        data = res.json()
        # cache data if using cache and week is over
        if self._cache & (matchup.week < current_week()):
            self._cache_boxscore(data, matchup)
        return data["boxscore"]

    def _lookup_matchup(self, week, team_id):
        try:
            matchup_idx = self._matchup_dict[week][team_id]
            return self._matchups[matchup_idx]
        except KeyError:
            return None

    def get_matchup(self, week, team_id, stats=False):
        matchup = self._lookup_matchup(week, team_id)
        if stats:
            data = self._get_boxscore_data(matchup)
            player_data = data["teams"]
            matchup.set_player_data(player_data)
        return matchup

    def get_matchups_by_week(self, week, stats=False):
        matchups = []
        team_ids = [team.team_id for team in self.teams]
        while len(team_ids) > 0:
            t_id = team_ids[0]
            matchup = self.get_matchup(week, t_id, stats)
            matchups.append(matchup)
            for team_id in matchup.team_ids:
                team_ids.pop(team_ids.index(team_id))
        return matchups

    ###########################################################
    # methods for reading and writing boxscores from/to cache #
    ###########################################################

    def _get_cache_filename(self, matchup):
        # name by week and home team ID
        fname = "{0}_{1:0>2}_{2:0>2}.json".format(
            self.league_id, matchup.week, matchup.home_team_id
        )
        return os.path.join(self._cache_dir, fname)

    def _load_cached_file(self, fname):
        if os.path.exists(fname):
            with open(fname, "r") as f:
                return json.load(f)
        return None

    def _load_cached_boxscore(self, matchup):
        fname = self._get_cache_filename(matchup)
        return self._load_cached_file(fname)

    def _cache_boxscore(self, data, matchup):
        fname = self._get_cache_filename(matchup)
        with open(fname, "w") as f:
            json.dump(data, f)
