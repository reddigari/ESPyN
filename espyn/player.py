from .constants import POSITIONS, PRO_TEAMS


class Player:

    def __init__(self, player_data):
        self.first_name = player_data["firstName"]
        self.last_name = player_data["lastName"]
        self.default_position_id = player_data["defaultPositionId"]
        self.position = POSITIONS[self.default_position_id]
        self.eligible_slots = player_data["eligibleSlots"]
        self.player_id = player_data["id"]
        self._pro_team_id = player_data["proTeamId"]
        self.pro_team = PRO_TEAMS[self._pro_team_id]
        if player_data.get("stats"):
            self._pro_team_id_during_match = player_data["stats"][0]["proTeamId"]
            self.pro_team_during_match = PRO_TEAMS[self._pro_team_id_during_match]
        else:
            self.pro_team_during_match = None

    @property
    def full_name(self):
        return "{} {}".format(self.first_name, self.last_name)

    def __repr__(self):
        return "{}, {}, {}".format(
            self.full_name, self.position, self.pro_team
        )

    def to_json(self):
        res = dict()
        res["first_name"] = self.first_name
        res["last_name"] = self.last_name
        res["full_name"] = self.full_name
        res["position"] = self.position
        res["pro_team"] = self.pro_team
        res["player_id"] = self.player_id
        return res
