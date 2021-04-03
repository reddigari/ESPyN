from typing import Dict, Any

from .player_week import PlayerWeek


class TeamWeek:
    """Representation of team boxscore for a scoring period"""

    def __init__(self, week_data: Dict[str, Any],
                 scoring_period: int) -> None:
        """Create team-week instance

        :param week_data: data from API response
        :type week_data: Dict[str, Any]
        :param scoring_period: scoring period
        :type scoring_period: int
        """

        self.scoring_period = scoring_period
        self.points = week_data["pointsByScoringPeriod"][str(scoring_period)]
        self.slots = []
        for slot in week_data["rosterForCurrentScoringPeriod"]["entries"]:
            if slot.get("playerId") is None:
                continue
            self.slots.append(PlayerWeek(slot))

    def __repr__(self):
        return "Scoring Period {} : {} points".format(
            self.scoring_period, self.points)
