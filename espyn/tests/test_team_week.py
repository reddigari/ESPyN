import os
import json
from unittest import TestCase

from ..team_week import TeamWeek
from ..player_week import PlayerWeek


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
TEST_FILE = os.path.join(DATA_DIR, "2020_1603206_sp10.json")


class PlayerTest(TestCase):

    def setUp(self):
        with open(TEST_FILE) as f:
            data = json.load(f)
        self.roster_data = data["schedule"][46]["home"]
        self.scoring_period = 10

    def test_team_week(self):
        tweek = TeamWeek(self.roster_data, self.scoring_period)
        self.assertAlmostEqual(tweek.points, 84.2, 4)
        for phrase in ("Scoring Period 10", "84.2 points"):
            self.assertIn(phrase, tweek.__repr__())
        self.assertEqual(len(tweek.slots), 16)
        self.assertIsInstance(tweek.slots[0], PlayerWeek)

