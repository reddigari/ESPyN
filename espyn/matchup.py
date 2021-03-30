from .team_week import TeamWeek


class Matchup:

    def __init__(self, matchup_data, league):
        self._data = matchup_data
        self._league = league
        self.matchup_num = self._data["matchupPeriodId"]
        self.scoring_periods = league.matchup_num_to_week(self.matchup_num)
        self._boxscore_data = {
            "home": {i: None for i in self.scoring_periods},
            "away": {i: None for i in self.scoring_periods},
        }
        self._boxscore_loaded = {i: False for i in self.scoring_periods}
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
    def boxscore_loaded(self):
        return all(self._boxscore_loaded.values())

    @property
    def home_data(self):
        if not self.boxscore_loaded:
            return None
        return [self._boxscore_data["home"][i] for i in self.scoring_periods]

    @property
    def away_data(self):
        if not self.boxscore_loaded or self.is_bye:
            return None
        return [self._boxscore_data["away"][i] for i in self.scoring_periods]

    def set_boxscore_data(self, data, scoring_period):
        assert "rosterForCurrentScoringPeriod" in data["home"]
        self._boxscore_data["home"][scoring_period] = TeamWeek(
            data["home"], scoring_period)
        if not self.is_bye:
            self._boxscore_data["away"][scoring_period] = TeamWeek(
                data["away"], scoring_period)
        self._boxscore_loaded[scoring_period] = True

    @property
    def home_team(self):
        return self._league.get_team_by_id(self.home_team_id)

    @property
    def away_team(self):
        if self.away_team_id is not None:
            return self._league.get_team_by_id(self.away_team_id)
        else:
            return None

    @property
    def team_ids(self):
        return [self.home_team_id, self.away_team_id]

    def __repr__(self):
        WINNER_SYM = chr(0x2705)
        prog = " (in progress)" if self.winner == "UNDECIDED" else ""
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
        return res

    def get_individual_scores(self):
        if self.is_bye:
            return []
        scores = []
        scores.extend(self.home_scores)
        scores.extend(self.away_scores)
        return scores
