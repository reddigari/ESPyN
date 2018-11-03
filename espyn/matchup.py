from .team_week import TeamWeek


class Matchup:

    def __init__(self, matchup_data, league):
        matchup = matchup_data["scheduleItems"][0]["matchups"][0]
        self.week = matchup_data["scheduleItems"][0]["matchupPeriodId"]
        self.home_team_id = matchup["homeTeamId"]
        self.away_team_id = matchup["awayTeamId"]
        self.home_score = matchup["homeTeamScores"][0]
        self.away_score = matchup["awayTeamScores"][0]
        self.outcome = matchup["outcome"]
        self.home_team = league.get_team(self.home_team_id)
        self.away_team = league.get_team(self.away_team_id)
        self.home_data = TeamWeek(matchup_data["teams"][0], self.home_team, self.week)
        self.away_data = TeamWeek(matchup_data["teams"][1], self.away_team, self.week)

    def __repr__(self):
        if self.outcome == 1:
            verb = "defeats"
        elif self.outcome == 2:
            verb = "defeated by"
        else:
            verb = "ties"
        h = self.home_team.owner
        a = self.away_team.owner
        return "Week {}: {} {} {}, {} to {}".format(
            self.week, h, verb, a, self.home_score, self.away_score
        )

    @property
    def team_ids(self):
        return [self.home_team_id, self.away_team_id]
