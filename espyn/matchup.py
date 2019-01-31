from .team_week import TeamWeek
from .utils import current_week


class Matchup:

    def __init__(self, sched_item, league, player_data=None):
        matchup = sched_item["matchups"][0]
        self._boxscore_loaded = False
        self.matchup_num = sched_item["matchupPeriodId"]
        self.is_playoff = self.matchup_num > league.reg_season_weeks
        self.scoring_periods = league.matchup_num_to_week(self.matchup_num)
        self.num_weeks = len(self.scoring_periods)
        self.home_team_id = matchup.get("homeTeamId")
        self.away_team_id = matchup.get("awayTeamId")
        self.home_team = league.get_team_by_id(self.home_team_id)
        if self.away_team_id is not None:
            self.away_team = league.get_team_by_id(self.away_team_id)
        self.is_bye = False
        if matchup["isBye"]:
            self.is_bye = True
            return
        self.home_score = sum(matchup["homeTeamScores"])
        self.home_scores = matchup["homeTeamScores"]
        self.away_score = sum(matchup["awayTeamScores"])
        self.away_scores = matchup["awayTeamScores"]
        self._outcome_code = matchup["outcome"]
        self.home_data = None
        self.away_data = None
        if player_data:
            self.set_player_data(player_data)

    def set_player_data(self, player_data):
        self.home_data = []
        self.away_data = []
        for week in self.scoring_periods:
            h = TeamWeek(player_data[week]["teams"][0], self.home_team, week)
            self.home_data.append(h)
            if not self.is_bye:
                a = TeamWeek(player_data[week]["teams"][1], self.away_team, week)
                self.away_data.append(a)
        self._boxscore_loaded = True

    # outcome verb from home team's perspective
    _outcome_verbs = {
        0: "vs.",
        1: "defeats",
        2: "defeated by",
        3: "ties"
    }

    def __repr__(self):
        if self.is_bye:
            return "Week {} : {} BYE WEEK".format(
                self.matchup_num, self.home_team.owner)
        current = current_week() in self.scoring_periods
        if current:
            verb = "currently playing"
        else:
            verb = self._outcome_verbs[self._outcome_code]
        h = self.home_team.owner
        a = self.away_team.owner
        if (self._outcome_code == 0) & (not current):
            return "Week {} : {} {} {}".format(self.matchup_num, h, verb, a)
        return "Week {} : {} {} {}, {} to {}".format(
            self.matchup_num, h, verb, a, self.home_score, self.away_score
        )

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
            res["outcome"] = self._outcome_code
        res["is_bye"] = self.is_bye
        res["scoring_periods"] = self.scoring_periods
        res["num_weeks"] = self.num_weeks
        res["is_playoff"] = self.is_playoff
        res["home_data"] = None
        res["away_data"] = None
        if self._boxscore_loaded:
            res["home_data"] = [[pw.to_json() for pw in data.slots] for data in self.home_data]
            res["away_data"] = [[pw.to_json() for pw in data.slots] for data in self.away_data]
        return res

    def get_individual_scores(self):
        if self.is_bye:
            return []
        scores = []
        scores.extend(self.home_scores)
        scores.extend(self.away_scores)
        return scores
