class Team:

    def __init__(self, team_data, league):
        self._league = league
        self.team_id = team_data["teamId"]
        self.team_abbrev = team_data["teamAbbrev"]
        self.team_location = team_data["teamLocation"]
        self.team_nickname = team_data["teamNickname"]
        try:
            self.owner = team_data["owners"][0]["firstName"]
        except KeyError:
            self.owner = "Team {} Owner".format(self.team_id)
        self.division_id = team_data["division"]["divisionId"]
        record = team_data["record"]
        self.points_for = record["pointsFor"]
        self.points_against = record["pointsAgainst"]
        self.wins = record["overallWins"]
        self.losses = record["overallLosses"]
        self.ties = record["overallTies"]
        self.winning_pct = record["overallPercentage"]
        self.acquisitions = team_data["teamTransactions"]["overallAcquisitionTotal"]

    def __repr__(self):
        return "Team {} : {} : {} : {}".format(
            self.team_id, self.owner, self.full_name, self.record
        )

    def set_matchups(self, matchups):
        self.matchups = matchups

    @property
    def full_name(self):
        return "{} {}".format(self.team_location, self.team_nickname)

    @property
    def record(self):
        return "{}-{}-{}".format(self.wins, self.losses, self.ties)

    def get_matchup_by_week(self, week, stats=False):
        return self._league.get_matchup(week, self.team_id, stats)

    def get_data_by_week(self, week):
        m = self.get_matchup_by_week(week)
        if m.home_team_id == self.team_id:
            return m.home_data
        else:
            return m.away_data
