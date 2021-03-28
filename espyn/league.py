import urllib.request
import logging
import json

from .constants import ENDPOINT, SEASON_OVER
from .team import Team
from .matchup import Matchup
from .utils import *
from .caches import LocalCache


class League:

    @staticmethod
    def _request_json(url):
        try:
            res = urllib.request.urlopen(url)
            raw = res.read()
            return json.loads(raw.decode("windows-1252"))
        except urllib.request.URLError:
            return None

    def __init__(self, league_id, season=None, cache=None,
                 try_cache=False):
        if cache:
            self._cache = cache
            self._cache.set_league(self)
        self._endpoint = ENDPOINT
        self.league_id = league_id
        if season is None:
            self.season = current_season()
        else:
            self.season = season

        # fetch league data
        self._data = self._get_league_data(try_cache)
        settings = self._data["settings"]
        self.name = settings["name"]
        self.size = settings["size"]
        self.draft_order = settings["draftSettings"]["pickOrder"]
        self.draft_type = settings["draftSettings"]["type"]
        self.reg_season_weeks = settings["scheduleSettings"]["matchupPeriodCount"]
        self._matchup_week_map = settings["scheduleSettings"]["matchupPeriods"]
        self.total_matchups = len(self._matchup_week_map)
        members = self._data["members"]
        self._members = {i["id"]: i for i in members}
        # set stat code to points map
        self.scoring_dict = dict()
        for item in settings["scoringSettings"]["scoringItems"]:
            self.scoring_dict[item["statId"]] = item["points"]
        # instantiate teams
        team_data = self._data["teams"]
        self._teams = dict()
        for team in team_data:
            self._teams[team["id"]] = Team(team, self)
        # instantiate matchups and add indices to _matchup_dict
        self._matchups = []
        self._matchup_dict = {}
        for i, item in enumerate(self._data["schedule"]):
            matchup = Matchup(item, self)
            self._matchups.append(matchup)
            num = matchup.matchup_num
            # add matchup index to lookup dict for both teams
            tmp = self._matchup_dict.setdefault(num, dict())
            for team_id in matchup.team_ids:
                tmp[team_id] = i

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

    def _get_league_data(self, try_cache=False):
        if try_cache:
            data = self._cache.load()
            if data:
                return data
        logging.info("Requesting league settings from ESPN for %d." % self.league_id)
        data = self._request_json(
            self._endpoint.format(self.season, self.league_id))
        if data is None:
            raise ValueError("That league is not publicly accessible.")
        # cache if using cache
        if self._cache:
            self._cache.save(data)
        return data

    def _get_scoring_period_data(self, scoring_period, try_cache=False):
        if try_cache:
            data = self._cache.load(scoring_period)
            if data:
                return data
        logging.info("Requesting boxscore data from ESPN for %d, period %d."
                     % (self.league_id, scoring_period))
        url = self._endpoint.format(self.season, self.league_id)
        url += f"&scoringPeriodId={scoring_period}"
        data = self._request_json(url)
        if data is None:
            raise RuntimeError("Failed to request scoring period data.")
        if self._cache:
            self._cache.save(data, scoring_period)
        return data

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
        idx = set(self._matchup_dict[number].values())
        return [self._matchups[i] for i in idx]

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

    def average_score(self, include_playoffs=True):
        scores = self.all_scores(include_playoffs)
        return float(sum(scores)) / len(scores)

    def matchup_num_to_week(self, matchup_num):
        num = str(matchup_num)
        return self._matchup_week_map.get(num)

    def week_to_matchup_num(self, week):
        for m, wks in self._matchup_week_map.items():
            if week in wks:
                return int(m)
        return None

    def name_from_user_id(self, user_id):
        member = self._members.get(user_id)
        if member:
            return f"{member['firstName']} {member['lastName']}"
        return None

    def current_matchup_num(self):
        cw = current_week()
        mn = self.week_to_matchup_num(cw)
        if mn is not None:
            return mn
        else:
            return SEASON_OVER

    def to_json(self):
        res = dict()
        res["league_id"] = self.league_id
        res["league_name"] = self.name
        res["league_size"] = self.size
        res["teams"] = [t.to_json() for t in self.teams]
        res["reg_season_weeks"] = self.reg_season_weeks
        res["total_matchups"] = self.total_matchups
        matchups = sorted(self._matchups, key=lambda i: i.matchup_num)
        res["matchups"] = [m.to_json() for m in matchups]
        res["all_scores"] = self.all_scores()
        return res
