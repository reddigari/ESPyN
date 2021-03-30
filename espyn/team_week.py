from .player_week import PlayerWeek


class TeamWeek:

    def __init__(self, week_data, scoring_period):
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
