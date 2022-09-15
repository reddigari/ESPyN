from .constants import STAT_CODES


class StatLine:
    """Descriptor to translate stat codes to named stats

    Inteded for composition with `PlayerWeek`. The specified attribute should
    be a dict mapping stat codes to the player's stats in that scoring period.
    """

    def __init__(self, data_attr: str):
        self.data_attr = data_attr

    def __get__(self, obj, objtype=None):
        data = getattr(obj, self.data_attr, dict())
        stats = dict()
        for code, val in data.items():
            key = STAT_CODES.get(code, code)
            stats[key] = val
        return stats
