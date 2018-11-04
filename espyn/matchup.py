from .team_week import TeamWeek
from .utils import current_week


class Matchup:

    def __init__(self, sched_item, league, player_data=None):
        matchup = sched_item["matchups"][0]
        self.week = sched_item["matchupPeriodId"]
        self.home_team_id = matchup["homeTeamId"]
        self.away_team_id = matchup["awayTeamId"]
        self.home_score = matchup["homeTeamScores"][0]
        self.away_score = matchup["awayTeamScores"][0]
        self._outcome_code = matchup["outcome"]
        self.home_team = league.get_team(self.home_team_id)
        self.away_team = league.get_team(self.away_team_id)
        self.home_data = None
        self.away_data = None
        if player_data:
            self.set_player_data(player_data)

    def set_player_data(self, player_data):
        self.home_data = TeamWeek(player_data[0], self.home_team, self.week)
        self.away_data = TeamWeek(player_data[1], self.away_team, self.week)

    # outcome verb from home team's perspective
    _outcome_verbs = {
        0: "vs.",
        1: "defeats",
        2: "defeated by",
        3: "ties"
    }

    def __repr__(self):
        current = self.week == current_week()
        if current:
            verb = "currently playing"
        else:
            verb = self._outcome_verbs[self._outcome_code]
        h = self.home_team.owner
        a = self.away_team.owner
        if (self._outcome_code == 0) & (not current):
            return "Week {} : {} {} {}".format(self.week, h, verb, a)
        return "Week {} : {} {} {}, {} to {}".format(
            self.week, h, verb, a, self.home_score, self.away_score
        )

    @property
    def team_ids(self):
        return [self.home_team_id, self.away_team_id]
