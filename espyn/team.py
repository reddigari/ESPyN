from typing import Any, Dict, List, TYPE_CHECKING

from .constants import SEASON_OVER
if TYPE_CHECKING:
    from .league import League
    from .matchup import Matchup
    from .team_week import TeamWeek


class Team:
    """Representation of fantasy team

    :param team_data: data from API response
    :type team_data: Dict[str, Any]
    :param league: fantasy league to which team belongs
    :type league: League
    """

    def __init__(self, team_data: Dict[str, Any],
                 league: "League") -> None:
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
    def full_name(self) -> str:
        """Full team name (location and nickname)

        :return: full team name
        :rtype: str
        """
        return "{} {}".format(self.team_location, self.team_nickname)

    @property
    def record(self) -> str:
        """Team record (W-L-T)

        :return: record
        :rtype: str
        """
        return "{}-{}-{}".format(self.wins, self.losses, self.ties)

    def get_matchup(self, number: int,
                    boxscore: bool = False) -> "Matchup":
        """Get team's matchup by number

        :param number: matchup number
        :type number: int
        :param boxscore: whether to load boxscore
        :type boxscore: bool
        :return: matchup for given scoring period
        :rtype: Matchup
        """
        return self._league.get_matchup(number, self.team_id, boxscore)

    def get_data_by_matchup(self, number: int) -> List["TeamWeek"]:
        """Get team's boxscore (player-level data) for matchup

        :param number: matchup number
        :type week: int
        :return: boxscore data
        :rtype: List[TeamWeek]
        """
        # loads boxscore automatically
        m = self.get_matchup(number, True)
        if m.home_team_id == self.team_id:
            return m.home_data
        else:
            return m.away_data

    def scores(self, include_playoffs: bool = True) -> List[float]:
        """Get scores from individual scoring periods

        :param include_playoffs: include scores from playoff matchups
        :type include_playoffs: bool
        :return: team's scores
        :rtype: List[float]
        """
        scores = []
        total_m = self._league.total_matchups + 1
        for m_num in range(1, total_m):
            m = self.get_matchup(m_num)
            if m is None or m.is_bye or m.winner == "UNDECIDED":
                continue
            if (not include_playoffs) and m.is_playoff:
                continue
            if m.home_team_id == self.team_id:
                scores.extend(m.home_scores)
            else:
                scores.extend(m.away_scores)
        return scores

    def to_json(self) -> Dict[str, Any]:
        """Get JSON-serializable dictionary representation

        :return: dictionary representation of team
        :rtype: Dict[str, Any]
        """
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
