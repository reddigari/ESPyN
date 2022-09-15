from typing import Any, Dict

from .player import Player
from .stat_line import StatLine
from .constants import SLOTS


class PlayerWeek:
    """Representation of player stat line for one NFL week

    :param stat_data: data from API response
    :type stat_data: Dict[str, Any]
    """
    stat_line = StatLine("_coded_stats")
    proj_line = StatLine("_coded_proj")

    def __init__(self, stat_data: Dict[str, Any]) -> None:
        ppe = stat_data["playerPoolEntry"]
        self.player = Player(ppe["player"])
        self.slot_id = stat_data["lineupSlotId"]
        self.slot = SLOTS[self.slot_id]
        self.points, self.projected_points = None, None
        stats_arr = ppe["player"]["stats"]
        if not stats_arr:
            return
        # real and projected stats objects are not in predictable order,
        # and neither is guaranteed to be there
        real = [i for i in stats_arr if i["statSourceId"] == 0]
        real = real[0] if real else dict()
        proj = [i for i in stats_arr if i["statSourceId"] == 1]
        proj = proj[0] if proj else dict()
        self.points = ppe["appliedStatTotal"]
        self.projected_points = proj.get("appliedTotal", 0.0)
        self._coded_stats, self._coded_proj = dict(), dict()
        if real.get("stats"):
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
    def projection_error(self) -> float:
        """Difference between projection and actual score

        :return: projection error, positive if projection too high
        :rtype: float
        """
        try:
            return self.projected_points - self.points
        except TypeError:  # sometimes one or both values is None
            return None

    def calculate_points(self, score_values: Dict[int, float]) -> float:
        """Manually calculate points from code to points mapping

        :param score_values: code to point-value mapping
        :type score_values: Dict[int, float]
        :return: player's fantasy points according to mapping
        :rtype: float
        """
        total = 0
        for code, val in self._coded_stats.items():
            if code in score_values:
                total += score_values[code] * val
        return round(total, 2)

    def to_json(self) -> Dict[str, Any]:
        """Get JSON-serializable dictionary representation

        :return: dictionary representation of player-week
        :rtype: Dict[str, Any]
        """
        res = dict()
        res["player"] = self.player.to_json()
        res["slot"] = self.slot
        res["stats"] = self.stat_line
        res["points"] = self.points
        res["projected_points"] = self.projected_points
        res["projection_error"] = self.projection_error
        return res
