from pkg_resources import get_distribution, DistributionNotFound

try:
    __version__ = get_distribution("espyn").version
except DistributionNotFound:
    pass

from .league import League
from .matchup import Matchup
from .team import Team
from .team_week import TeamWeek
from .player_week import PlayerWeek
from .player import Player
