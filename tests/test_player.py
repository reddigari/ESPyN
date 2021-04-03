import os
import json
from unittest import TestCase

from espyn.player import Player


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
TEST_FILE = os.path.join(DATA_DIR, "2020_1603206_sp10.json")


class PlayerTest(TestCase):

    def setUp(self):
        with open(TEST_FILE) as f:
            data = json.load(f)
        home = data["schedule"][46]["home"]
        roster = home["rosterForCurrentScoringPeriod"]["entries"]
        self.player_data = roster[2]["playerPoolEntry"]["player"]

    def test_player_with_stats(self):
        player = Player(self.player_data)
        self.assertEqual(player.full_name, "Josh Jacobs")
        self.assertEqual(player.position, "RB")
        self.assertEqual(player.pro_team, "LV")
        self.assertEqual(player.pro_team_during_match, "LV")
        repr = "Josh Jacobs, RB, LV"
        self.assertEqual(player.__repr__(), repr)

    def test_player_without_stats(self):
        new_data = {k: v for k, v in self.player_data.items() if k != "stats"}
        player = Player(new_data)
        self.assertIsNone(player.pro_team_during_match)

    def test_player_json(self):
        player = Player(self.player_data)
        data = player.to_json()
        keys = ("first_name", "last_name", "full_name",
                "position", "pro_team", "player_id")
        for key in keys:
            assert key in data
