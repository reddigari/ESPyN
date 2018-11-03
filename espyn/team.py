class Team:

    def __init__(self, team_data, league):
        self._league = league
        self.team_id = team_data["teamId"]
        self.team_abbrev = team_data["teamAbbrev"]
        self.team_location = team_data["teamLocation"]
        self.team_nickname = team_data["teamNickname"]
        self.owner = team_data["owners"][0]["firstName"]
        self.division_id = team_data["division"]["divisionId"]
        record = team_data["record"]
        self.points_for = record["pointsFor"]
        self.points_against = record["pointsAgainst"]
        self.wins = record["overallWins"]
        self.losses = record["overallLosses"]
        self.ties = record["overallTies"]
        self.winning_pct = record["overallPercentage"]

    def __repr__(self):
        return "Team {} : {} : {} : {}".format(
            self.team_id, self.owner, self.full_name, self.record
        )

    @property
    def full_name(self):
        return "{} {}".format(self.team_location, self.team_nickname)

    @property
    def record(self):
        return "{}-{}-{}".format(self.wins, self.losses, self.ties)

    def get_matchup_by_week(self, week):
        return self._league.get_matchup(week, self.team_id)
