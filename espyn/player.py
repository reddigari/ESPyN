from .constants import POSITIONS, PRO_TEAMS


class Player:

    def __init__(self, player_data):
        self.first_name = player_data["firstName"]
        self.last_name = player_data["lastName"]
        self.pct_owned = player_data["percentOwned"]
        self.default_position_id = player_data["defaultPositionId"]
        self.position = POSITIONS[self.default_position_id]
        self.eligible_slots = player_data["eligibleSlotCategoryIds"]
        self.player_id = player_data["playerId"]
        self.pro_team_id = player_data["proTeamId"]
        self.pro_team = PRO_TEAMS[self.pro_team_id]
        self.sports_id = player_data["sportsId"]
        self.ticker_id = player_data["tickerId"]

    @property
    def full_name(self):
        return "{} {}".format(self.first_name, self.last_name)

    def __repr__(self):
        return "{}, {}, {}".format(
            self.full_name, self.position, self.pro_team
        )
