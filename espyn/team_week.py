from .player_week import PlayerWeek


class TeamWeek:

    def __init__(self, week_data, team, week):
        self.week = week
        self.team = team
        self.points = week_data["appliedActiveRealTotal"]
        self.bench_points = week_data["appliedInactiveRealTotal"]
        self.slots = []
        for slot in week_data["slots"]:
            if slot.get("player") is None:
                continue
            self.slots.append(PlayerWeek(slot))

    def __repr__(self):
        return "Week {} : {} : {} points, {} bench points".format(
            self.week, self.team.owner, self.points, self.bench_points
        )
