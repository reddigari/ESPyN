from .utils import current_week


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
        self.draft_position = league.draft_order.index(self.team_id) + 1

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

    def get_matchup_by_week(self, week, stats=False):
        return self._league.get_matchup(week, self.team_id, stats)

    def get_data_by_week(self, week):
        # loads boxscore automatically
        m = self.get_matchup_by_week(week, True)
        if m.home_team_id == self.team_id:
            return m.home_data
        else:
            return m.away_data

    def scores(self, include_playoffs=True):
        scores = []
        cm = self._league.current_matchup_num()
        for w in range(1, cm):  # excludes matchup in progress
            m = self.get_matchup_by_week(w)
            if m is None or m.is_bye:
                continue
            if (not include_playoffs) and m.is_playoff:
                continue
            if m.home_team_id == self.team_id:
                scores.extend(m.home_scores)
            else:
                scores.extend(m.away_scores)
        return scores

    def current_roster(self):
        cw = current_week()
        m = self.get_matchup_by_week(cw, True)
        if m.home_team_id == self.team_id:
            data = m.home_data
        else:
            data = m.away_data
        return [s.player for s in data.slots]

    def to_json(self):
        res = dict()
        res["team_id"] = self.team_id
        res["team_abbrev"] = self.team_abbrev
        res["team_location"] = self.team_location
        res["team_nickname"] = self.team_nickname
        res["owner"] = self.owner
        res["division_id"] = self.division_id
        res["points_for"] = self.points_for
        res["points_against"] = self.points_against
        res["wins"] = self.wins
        res["losses"] = self.losses
        res["ties"] = self.ties
        res["winning_pct"] = self.winning_pct
        res["transactions"] = self.acquisitions
        res["draft_position"] = self.draft_position
        res["scores"] = self.scores()
        return res
