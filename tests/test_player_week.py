import os
import json
from unittest import TestCase

from espyn.player_week import PlayerWeek
from espyn.player import Player


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
TEST_FILE = os.path.join(DATA_DIR, "2020_1603206_sp10.json")


class PlayerTest(TestCase):

    def setUp(self):
        with open(TEST_FILE) as f:
            data = json.load(f)
        home = data["schedule"][46]["home"]
        roster = home["rosterForCurrentScoringPeriod"]["entries"]
        self.entry_data = roster[2]

    def test_player_week(self):
        pweek = PlayerWeek(self.entry_data)
        self.assertAlmostEqual(pweek.points, 25.6, 4)
        self.assertAlmostEqual(pweek.projected_points, 13.9, 1)
        for phrase in ("RB", "Josh Jacobs", "25.6 points"):
            self.assertIn(phrase, pweek.__repr__())
        self.assertIsInstance(pweek.player, Player)

    def test_stat_line(self):
        pweek = PlayerWeek(self.entry_data)
        stats = pweek.stat_line
        self.assertEqual(stats["rush_att"], 21)
        self.assertEqual(stats["rush_yds"], 112)
        self.assertEqual(stats["rush_td"], 2)
        self.assertEqual(stats["rec"], 4)
        self.assertEqual(stats["rec_yds"], 24)

    def test_manual_score_calc(self):
        pweek = PlayerWeek(self.entry_data)
        scoring_items = {24: 0.1, 25: 6, 42: 0.1, 43: 6}
        points = pweek.calculate_points(scoring_items)
        self.assertEqual(points, 25.6)

    def test_player_week_json(self):
        pweek = PlayerWeek(self.entry_data)
        data = pweek.to_json()
        keys = ("player", "slot", "stats", "points",
                "projected_points", "projection_error")
        for key in keys:
            assert key in data
