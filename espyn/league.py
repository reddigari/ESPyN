import urllib
import logging
import json

from .constants import ENDPOINT
from .team import Team
from .matchup import Matchup
from .utils import *
from .caches import LocalCache


class League:

    @staticmethod
    def _request_json(url, params):
        url += "?"
        for k, v in params.items():
            url += "{}={}&".format(k, v)
        try:
            res = urllib.request.urlopen(url)
            raw = res.read()
            return json.loads(raw.decode("windows-1252"))
        except urllib.request.URLError:
            return None

    def __init__(self, league_id, season=None, cache=None,
                 cache_dir=None, try_cache=False):
        self._cache = False
        self._endpoint = ENDPOINT
        self.league_id = league_id
        if season is None:
            self.season = current_season()
        else:
            self.season = season

        if cache is None:
            self._cache = None
        if cache == "cloud":
            # import if needed, storage import fails on App Engine
            from .caches import CloudStorageCache
            self._cache = CloudStorageCache()
        elif cache == "local":
            self._cache = LocalCache(cache_dir)
        else:
            # pass in special cache if using in web app
            self._cache = cache

        # fetch league data
        self._data = self._get_league_data(try_cache)
        self.name = self._data["name"]
        self.size = self._data["size"]
        self.draft_order = self._data["draftOrder"]
        self.reg_season_weeks = self._data["finalRegularSeasonMatchupPeriodId"]
        self.total_matchups = self._data["finalMatchupPeriodId"]
        self._matchup_week_map = self._data["scoringPeriodsByMatchupPeriod"]
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
                mn = matchup.matchup_num
                # add matchup and index for both teams if it doesn't exist
                if self._lookup_matchup(mn, int(t_id)) is None:
                    self._matchups.append(matchup)
                    tmp = self._matchup_dict.setdefault(mn, dict())
                    for i in matchup.team_ids:
                        tmp[i] = index
                    index += 1

    def __repr__(self):
        return "ESPN League {} - {} - {} teams".format(
            self.league_id, self.name, self.size
        )

    @property
    def teams(self):
        """
        Teams composing the league.
        :return: List of Team objects representing league's teams
        """
        teams = list(self._teams.values())
        return sorted(teams, key=lambda i: i.team_id)

    def get_team_by_id(self, team_id):
        """
        Returns team with given ID
        :param team_id: integer team ID
        :return: team with given ID
        """
        return self._teams[team_id]

    def _url_params(self, **kwargs):
        params = dict()
        params["seasonId"] = self.season
        params["leagueId"] = self.league_id
        for k, v in kwargs.items():
            params[k] = v
        return params

    def _get_league_data(self, try_cache=False):
        if try_cache and self._cache:
            data = self._load_cached_league()
            if data:
                return data["leaguesettings"]
        url = self._endpoint + "leagueSettings"
        params = self._url_params()
        logging.info("Requesting league settings from ESPN for %d." % self.league_id)
        data = self._request_json(url, params)
        if data is None:
            raise ValueError("That league is not publicly accessible.")
        # cache if using cache
        if self._cache:
            self._cache_league(data)
        return data["leaguesettings"]

    def _get_boxscore_data(self, matchup):
        if self._cache:
            data = self._load_cached_boxscore(matchup)
            if data:
                return data
        url = self._endpoint + "boxscore"
        params = self._url_params()
        params["teamId"] = matchup.home_team_id
        params["matchupPeriodId"] = matchup.matchup_num
        all_data = dict()
        for week in matchup.scoring_periods:
            params["scoringPeriodId"] = week
            logging.info("Requesting matchup data from ESPN.")
            data = self._request_json(url, params)
            all_data[week] = data["boxscore"]
            # cache data if using cache and week is over
            if (self._cache is not None) &\
                    (matchup.matchup_num < self.current_matchup_num()):
                self._cache_boxscore(data, matchup, week)
        return all_data

    def _lookup_matchup(self, matchup_num, team_id):
        try:
            matchup_idx = self._matchup_dict[matchup_num][team_id]
            return self._matchups[matchup_idx]
        except KeyError:
            return None

    def get_matchup(self, number, team_id, stats=False):
        """
        Returns matchup from specified week involving specified team.
        :param number: matchup number (usually a week number during reg season)
        :param team_id: integer team ID
        :param stats: whether to load boxscore (will require Internet
                      connection if data not cached)
        :return: specified matchup
        """
        matchup = self._lookup_matchup(number, team_id)
        if stats:
            box = self._get_boxscore_data(matchup)
            matchup.set_player_data(box)
        return matchup

    def get_matchups_by_number(self, number, stats=False):
        """
        Returns all matchups from specified week/number
        :param number: week/matchup number
        :param stats: whether to load boxscore (will require Internet
                      connection if data not cached)
        :return:  list of specified matchups
        """
        matchups = []
        team_ids = [team.team_id for team in self.teams]
        while len(team_ids) > 0:
            t_id = team_ids[0]
            matchup = self.get_matchup(number, t_id, stats)
            matchups.append(matchup)
            for team_id in matchup.team_ids:
                if team_id is not None:
                    team_ids.pop(team_ids.index(team_id))
        return matchups

    def all_scores(self, include_playoffs=True):
        """
        Returns list of scores for all matchups up to (and excluding) current week
        :param include_playoffs: whether to include scores from playoff matchups
        :return: list of team scores
        """
        scores = []
        cm = self.current_matchup_num()
        for m in self._matchups:
            if m.matchup_num >= cm or m.is_bye:
                continue
            if (not include_playoffs) and m.is_playoff:
                continue
            scores.extend(m.get_individual_scores())
        return scores

    def average_score(self):
        scores = self.all_scores()
        return float(sum(scores)) / len(scores)

    def matchup_num_to_week(self, matchup_num):
        num = str(matchup_num)
        return self._matchup_week_map.get(num)

    def week_to_matchup_num(self, week):
        for m, wks in self._matchup_week_map.items():
            if week in wks:
                return int(m)
        return None

    def current_matchup_num(self):
        cw = current_week()
        mn = self.week_to_matchup_num(cw)
        if mn is not None:
            return mn
        else:
            return 999

    def to_json(self):
        res = dict()
        res["league_id"] = self.league_id
        res["league_name"] = self.name
        res["league_size"] = self.size
        res["teams"] = [t.to_json() for t in self.teams]
        matchups = sorted(self._matchups, key=lambda i: i.week)
        res["matchups"] = [m.to_json() for m in matchups]
        res["all_scores"] = self.all_scores()
        return res

    ############################################################
    # methods for dealing with cache filenames and interacting #
    # with cache objects.                                      #
    ############################################################

    def _get_league_fname(self):
        return "{}_settings.json".format(self.league_id)

    def _get_fname_from_matchup(self, matchup, week):
        # name by week and home team ID
        fname = "{0}_{1:0>2}_{2:0>2}.json".format(
            self.league_id, week, matchup.home_team_id
        )
        return fname

    def _load_cached_league(self):
        fname = self._get_league_fname()
        return self._cache.read_from_cache(fname)

    def _load_cached_boxscore(self, matchup):
        all_data = dict()
        for week in matchup.scoring_periods:
            fname = self._get_fname_from_matchup(matchup, week)
            data = self._cache.read_from_cache(fname)
            if data is None:
                return None
            all_data[week] = data["boxscore"]
        return all_data

    def _cache_league(self, data):
        fname = self._get_league_fname()
        self._cache.write_to_cache(data, fname)

    def _cache_boxscore(self, data, matchup, week):
        fname = self._get_fname_from_matchup(matchup, week)
        self._cache.write_to_cache(data, fname)
