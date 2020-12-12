from .team_week import TeamWeek
from .utils import current_week


class Matchup:

    def __init__(self, matchup_data, league):
        self._data = matchup_data
        self._league = league
        self.matchup_num = self._data["matchupPeriodId"]
        self._boxscore_loaded = False
        self.is_playoff = self.matchup_num > league.reg_season_weeks
        self.is_bye = False  # change upon inspection of data
        self.scoring_periods = league.matchup_num_to_week(self.matchup_num)
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
        self.home_data = None
        self.away_data = None

    @property
    def home_team(self):
        return self._league.get_team_by_id(self.home_team_id)

    @property
    def away_team(self):
        if self.away_team_id is not None:
            return self._league.get_team_by_id(self.away_team_id)
        else:
            return None

    # def set_player_data(self, player_data):
    #     self.home_data = []
    #     self.away_data = []
    #     for week in self.scoring_periods:
    #         h = TeamWeek(player_data[week]["teams"][0], self.home_team, week)
    #         self.home_data.append(h)
    #         if not self.is_bye:
    #             a = TeamWeek(player_data[week]["teams"][1], self.away_team, week)
    #             self.away_data.append(a)
    #     self._boxscore_loaded = True

    @property
    def team_ids(self):
        return [self.home_team_id, self.away_team_id]

    @property
    def all_data(self):
        if not self._boxscore_loaded:
            raise RuntimeError("Boxscore not loaded for this matchup.")
        return [self.home_data, self.away_data]

    def to_json(self):
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
        # if self._boxscore_loaded:
        #     res["home_data"] = [[pw.to_json() for pw in data.slots] for data in self.home_data]
        #     res["away_data"] = [[pw.to_json() for pw in data.slots] for data in self.away_data]
        return res

    def get_individual_scores(self):
        if self.is_bye:
            return []
        scores = []
        scores.extend(self.home_scores)
        scores.extend(self.away_scores)
        return scores
