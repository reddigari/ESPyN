from .constants import SEASON_OVER


class Team:

    def __init__(self, team_data, league):
        self._league = league
        self.team_id = team_data["id"]
        self.team_abbrev = team_data["abbrev"]
        self.team_location = team_data["location"]
        self.team_nickname = team_data["nickname"]
        if team_data.get("owners"):
            self.owner = league.name_from_user_id(team_data["owners"][0])
        else:
            self.owner = "<NO OWNER>"
        self.division_id = team_data["divisionId"]
        record = team_data["record"]["overall"]
        self.points_for = record["pointsFor"]
        self.points_against = record["pointsAgainst"]
        self.wins = record["wins"]
        self.losses = record["losses"]
        self.ties = record["ties"]
        self.winning_pct = record["percentage"]
        self.transactions = team_data["transactionCounter"]
        self.acquisitions = self.transactions["acquisitions"]
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
        if cm == SEASON_OVER:
            cm = self._league.total_matchups + 1
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
