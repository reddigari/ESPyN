import urllib.request
import logging
import json
from typing import Optional, List, Dict, Any

from .constants import ENDPOINT, SEASON_OVER
from .team import Team
from .matchup import Matchup
from .utils import *
from .caches import Cache, cache_operation


class League:
    """Representation of an ESPN fantasy football league"""

    @staticmethod
    def _request_json(url):
        try:
            res = urllib.request.urlopen(url)
            raw = res.read()
            return json.loads(raw.decode("windows-1252"))
        except urllib.request.URLError:
            return None

    def __init__(self, league_id: int, season: Optional[int] = None,
                 cache: Optional[Cache] = None) -> None:
        """Retrieve and model a league for a given season.

        :param league_id: ID of ESPN league
        :type league_id: int
        :param season: NFL season
        :type season: int, optional
        :param cache: cache to reduce network requests
        :type cache: espyn.cache.Cache, optional
        """
        if cache:
            self.cache = cache
            self.cache.set_league(self)
        self._endpoint = ENDPOINT
        self.league_id = league_id
        if season is None:
            self.season = current_season()
        else:
            self.season = season

        # fetch league data
        self._data = self._get_league_data()
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
    def teams(self) -> List[Team]:
        """Teams composing the league.

        :return: list of teams in league
        :rtype: List[Team]
        """
        teams = list(self._teams.values())
        return sorted(teams, key=lambda i: i.team_id)

    def get_team_by_id(self, team_id: int) -> Team:
        """Get team with given team ID

        :param team_id: team ID
        :type team_id: int
        :return: :class:`Team` with given ID
        :rtype: Team
        """
        return self._teams[team_id]

    @cache_operation
    def _get_league_data(self):
        logging.info("Requesting league settings from ESPN for %d." % self.league_id)
        data = self._request_json(
            self._endpoint.format(self.season, self.league_id))
        if data is None:
            raise ValueError("That league is not publicly accessible.")
        return data

    @cache_operation
    def _get_scoring_period_data(self, scoring_period):
        logging.info("Requesting boxscore data from ESPN for %d, period %d."
                     % (self.league_id, scoring_period))
        url = self._endpoint.format(self.season, self.league_id)
        url += f"&scoringPeriodId={scoring_period}"
        data = self._request_json(url)
        if data is None:
            raise RuntimeError("Failed to request scoring period data.")
        return data

    def _populate_boxscores(self, matchup_num):
        scoring_periods = self.matchup_num_to_scoring_periods(matchup_num)
        if scoring_periods is None:
            raise ValueError(
                "This league does not have a matchup number %d." % matchup_num)
        for sp in scoring_periods:
            data = self._get_scoring_period_data(sp)
            data = [i for i in data["schedule"] if i["matchupPeriodId"] == matchup_num]
            # for each matchup in this period, lookup Matchup object
            # by home team ID, and set the boxscore data
            for datum in data:
                m = self.get_matchup(matchup_num, datum["home"]["teamId"])
                m.set_boxscore_data(datum, sp)

    def _lookup_matchup(self, matchup_num, team_id):
        try:
            matchup_idx = self._matchup_dict[matchup_num][team_id]
            return self._matchups[matchup_idx]
        except KeyError:
            return None

    def get_matchup(self, number: int, team_id: int,
                    boxscore: bool = False) -> Matchup:
        """Get matchup by matchup number and team ID

        :param number: matchup number (usually a week number during reg season)
        :type number: int
        :param team_id: team ID
        :type team_id: int
        :param boxscore: whether to load boxscore (will require Internet
                         connection if data not cached)
        :type boxscore: bool
        :return: specified matchup
        :rtype: Matchup
        """
        matchup = self._lookup_matchup(number, team_id)
        if boxscore:
            if not matchup.boxscore_loaded:
                self._populate_boxscores(number)
        return matchup

    def get_matchups_by_number(self, number: int,
                               boxscore: bool = False) -> List[Matchup]:
        """Get all matchups from matchup number

        :param number: matchup number (usually a week number during reg season)
        :type number: int
        :param boxscore: whether to load boxscore (will require Internet
                         connection if data not cached)
        :type boxscore: bool
        :return: specified matchups
        :rtype: List[Matchup]
        """
        idx = set(self._matchup_dict[number].values())
        matchups = [self._matchups[i] for i in idx]
        if boxscore:
            if not all(i.boxscore_loaded for i in matchups):
                self._populate_boxscores(number)
        return matchups

    def all_scores(self, include_playoffs: bool = True) -> List[float]:
        """Get list of scores for all matchups up to (and excluding) current week

        :param include_playoffs: whether to include scores from playoff matchups
        :type include_playoffs: bool
        :return: list of team scores
        :rtype: List[float]
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

    def average_score(self, include_playoffs: bool = True) -> float:
        """Get league's average score (per scoring period)

        :param include_playoffs: whether to include scores from playoff matchups
        :type include_playoffs: bool
        :return: average score
        :rtype: float
        """
        scores = self.all_scores(include_playoffs)
        return float(sum(scores)) / len(scores)

    def matchup_num_to_scoring_periods(self, matchup_num: int) -> List[int]:
        """Get scoring periods corresponding to a matchup number

        :param matchup_num: matchup number
        :type matchup_num: int
        :return: scoring period(s) composing matchup
        :rtype: List[int]
        """
        num = str(matchup_num)
        return self._matchup_week_map.get(num)

    def week_to_matchup_num(self, week: int) -> int:
        """Get matchup number corresponding to a scoring period

        :param week: scoring period
        :type week: int
        :return: matchup number
        :rtype: int
        """
        for m, wks in self._matchup_week_map.items():
            if week in wks:
                return int(m)
        return None

    def name_from_user_id(self, user_id: str) -> Optional[str]:
        """Get member name from ESPN user ID

        :param user_id: ESPN user ID
        :type user_id: str
        :return: member name
        :rtype: Optional[str]
        """
        member = self._members.get(user_id)
        if member:
            return f"{member['firstName']} {member['lastName']}"
        return None

    def current_matchup_num(self) -> int:
        """Get current matchup number

        :return: matchup number
        :rtype: int
        """
        cw = current_week()
        mn = self.week_to_matchup_num(cw)
        if mn is not None:
            return mn
        else:
            return SEASON_OVER

    def to_json(self) -> Dict[str, Any]:
        """Get JSON-serializable dictionary representation

        :return: dictionary representation of league
        :rtype: Dict[str, Any]
        """
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
