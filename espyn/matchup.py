from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .team_week import TeamWeek
if TYPE_CHECKING:
    from .league import League
    from .team import Team


class Matchup:
    """Representation of a fantasy matchup

    Matchups may contain one or more scoring periods depending on the
    league settings. A scoring period is one NFL week.

    :param matchup_data: data from API response
    :type matchup_data: Dict[str, Any]
    :param league: fantasy league to which matchup belongs
    :type league: League
    """

    def __init__(self, matchup_data: Dict[str, Any],
                 league: "League") -> None:
        self._data = matchup_data
        self._league = league
        self.matchup_num = self._data["matchupPeriodId"]
        self.scoring_periods = league.matchup_num_to_scoring_periods(
            self.matchup_num)
        self._boxscore_data = {
            "home": {i: None for i in self.scoring_periods},
            "away": {i: None for i in self.scoring_periods},
        }
        self._boxscore_loaded = {i: False for i in self.scoring_periods}
        self._errors = set()
        self.is_playoff = self.matchup_num > league.reg_season_weeks
        self.is_bye = False  # change upon inspection of data
        self.num_weeks = len(self.scoring_periods)
        self.home_team_id = self._data["home"]["teamId"]
        self.home_score = self._data["home"]["totalPoints"]
        pscores = self._data["home"].get("pointsByScoringPeriod", dict())
        self.home_scores = [pscores.get(str(i), 0) for i in self.scoring_periods]
        if self._data.get("away"):
            self.away_team_id = self._data["away"]["teamId"]
            self.away_score = self._data["away"]["totalPoints"]
            pscores = self._data["away"].get("pointsByScoringPeriod", dict())
            self.away_scores = [pscores.get(str(i), 0) for i in self.scoring_periods]
        else:
            self.is_bye = True
            self.away_team_id = None
            self.away_score = None
            self.away_scores = []
        self.winner = self._data["winner"]

    @property
    def boxscore_loaded(self) -> bool:
        """Whether boxscore (player-level) data have been loaded

        Requires network request if data are not cached.
        :return: whether boxscore is loaded
        :rtype: bool
        """
        return all(self._boxscore_loaded.values())

    @property
    def error(self) -> Optional[str]:
        """Description of errors encountered setting boxscore data

        :return: Optional[str]
        """
        if len(self._errors):
            return " ".join(self._errors)
        return None

    @property
    def home_data(self) -> Optional[List[TeamWeek]]:
        """Home team's boxscore(s) if loaded

        :return: home team's boxscore(s) or None
        :rtype: Optional[List[TeamWeek]]
        """
        if not self.boxscore_loaded:
            return None
        return [self._boxscore_data["home"][i] for i in self.scoring_periods]

    @property
    def away_data(self) -> Optional[List[TeamWeek]]:
        """Away team's boxscore(s) if loaded (and not bye)

        :return: away team's boxscore(s) or None
        :rtype: Optional[List[TeamWeek]]
        """
        if not self.boxscore_loaded or self.is_bye:
            return None
        return [self._boxscore_data["away"][i] for i in self.scoring_periods]

    def _validate_boxscore_data(self, data, scoring_period):
        if "rosterForCurrentScoringPeriod" not in data["home"]:
            self._errors.add(
                f"Boxscore missing home team data for period {scoring_period}.")
        if not self.is_bye and "rosterForCurrentScoringPeriod" not in data["away"]:
            self._errors.add(
                f"Boxscore missing away team data for period {scoring_period}.")
        return

    def set_boxscore_data(self, data, scoring_period):
        self._validate_boxscore_data(data, scoring_period)
        if self.error:
            return
        self._boxscore_data["home"][scoring_period] = TeamWeek(
            data["home"], scoring_period)
        if not self.is_bye:
            self._boxscore_data["away"][scoring_period] = TeamWeek(
                data["away"], scoring_period)
        self._boxscore_loaded[scoring_period] = True

    @property
    def home_team(self) -> "Team":
        """Home team

        :return: home team
        :rtype: Team
        """
        return self._league.get_team_by_id(self.home_team_id)

    @property
    def away_team(self) -> Optional["Team"]:
        """Away team

        :return: away team, if not bye matchup
        :rtype: Optional[Team]
        """
        if self.away_team_id is not None:
            return self._league.get_team_by_id(self.away_team_id)
        else:
            return None

    @property
    def team_ids(self) -> List[int]:
        """Team IDs of matchup teams

        :return: team IDs
        :rtype: List[int]
        """
        return [self.home_team_id, self.away_team_id]

    def __repr__(self):
        WINNER_SYM = chr(0x2705)
        prog = ""
        if self.winner == "UNDECIDED" and not self.is_bye:
            prog = " (in progress)"
        prefix = f"Matchup #{self.matchup_num}{prog}"
        home_exp = "{} ({})".format(
            self.home_team.full_name, self.home_score)
        if self.is_bye:
            return f"{prefix} : {home_exp} : BYE"
        away_exp = f"{self.away_team.full_name} ({self.away_score})"
        if self.winner == "HOME":
            home_exp += WINNER_SYM
        elif self.winner == "AWAY":
            away_exp += WINNER_SYM
        return f"{prefix} : {away_exp} @ {home_exp}"

    @property
    def all_data(self) -> List[Optional[List[TeamWeek]]]:
        """All boxscores in matchup

        :return: home and away boxscores
        :rtype: List[Optional[List[TeamWeek]]]

        :raise: RuntimeError if boxscore data not yet loaded
        """
        if not self.boxscore_loaded:
            raise RuntimeError("Boxscore not loaded for this matchup.")
        return [self.home_data, self.away_data]

    def to_json(self) -> Dict[str, Any]:
        """Get JSON-serializable dictionary representation

        :return: dictionary representation of matchup
        :rtype: Dict[str, Any]
        """
        res = dict()
        res["matchup_num"] = self.matchup_num
        res["team_ids"] = self.team_ids
        res["home_team_id"] = self.home_team_id
        res["away_team_id"] = self.away_team_id
        if not self.is_bye:
            res["home_score"] = self.home_score
            res["away_score"] = self.away_score
            res["winner"] = self.winner
        res["is_bye"] = self.is_bye
        res["scoring_periods"] = self.scoring_periods
        res["num_weeks"] = self.num_weeks
        res["is_playoff"] = self.is_playoff
        res["home_data"] = None
        res["away_data"] = None
        return res

    def get_individual_scores(self) -> List[float]:
        """Get scores from individual scoring periods for both teams

        :return: scores from all scoring periods
        :rtype: List[float]
        """
        if self.is_bye:
            return []
        scores = []
        scores.extend(self.home_scores)
        scores.extend(self.away_scores)
        return scores
