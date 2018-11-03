from .player import Player
from .constants import SLOTS


class PlayerWeek:

    def __init__(self, stat_data):
        self.player = Player(stat_data["player"])
        self.slot_id = stat_data["slotCategoryId"]
        self.slot = SLOTS[self.slot_id]
        real = stat_data["currentPeriodRealStats"]
        proj = stat_data["currentPeriodProjectedStats"]
        self.points = real.get("appliedStatTotal")
        self.projected_points = proj.get("appliedStatTotal")
        # self._coded_stats = {int(k): v for k, v in real["rawStats"].items()}

    @property
    def projection_error(self):
        return self.projected_points - self.points

    def calculate_points(self, score_values):
        """
        Manually calculates points from score code to fantasy points mapping
        :param score_values: dict with code keys and point values
        :return: player's fantasy points according to mapping
        """
        total = 0
        for code, val in self._coded_stats:
            if code in score_values:
                total += score_values[code] * val
        return total

    def __repr__(self):
        pts_str = "Inactive" if self.points is None else "%0.1f points" % self.points
        return "{} : {} : {}".format(
            self.slot, self.player, pts_str
        )

