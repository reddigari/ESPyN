from .player import Player
from .constants import SLOTS, STAT_CODES


class PlayerWeek:

    def __init__(self, stat_data):
        ppe = stat_data["playerPoolEntry"]
        self.player = Player(ppe["player"])
        self.slot_id = stat_data["lineupSlotId"]
        self.slot = SLOTS[self.slot_id]
        stats_arr = ppe["player"]["stats"]
        if not stats_arr:
            return
        real = stats_arr[0]
        proj = stats_arr[1] if len(stats_arr) == 2 else dict()
        self.points = ppe["appliedStatTotal"]
        self.projected_points = proj.get("appliedTotal") or 0.
        self._coded_stats, self._coded_proj = dict(), dict()
        self._coded_stats = {
            int(k): v for k, v in real["stats"].items()
        }
        if proj.get("stats"):
            self._coded_proj = {
                int(k): v for k, v in proj["stats"].items()
            }

    def __repr__(self):
        pts_str = "Inactive" if self.points is None else "%0.1f points" % self.points
        return "{} : {} : {}".format(
            self.slot, self.player, pts_str
        )

    @property
    def stat_line(self):
        stats = {}
        for code, val in self._coded_stats.items():
            stat = STAT_CODES.get(code)
            if stat:
                stats[stat] = val
        return stats

    @property
    def projection_error(self):
        try:
            return self.projected_points - self.points
        except TypeError:  # sometimes one or both values is None
            return None

    def calculate_points(self, score_values):
        """
        Manually calculates points from score code to fantasy points mapping
        :param score_values: dict with code keys and point values
        :return: player's fantasy points according to mapping
        """
        total = 0
        for code, val in self._coded_stats.items():
            if code in score_values:
                total += score_values[code] * val
        return round(total, 2)

    def to_json(self):
        res = dict()
        res["player"] = self.player.to_json()
        res["slot"] = self.slot
        res["stats"] = self.stat_line
        res["points"] = self.points
        res["projected_points"] = self.projected_points
        res["projection_error"] = self.projection_error
        return res
