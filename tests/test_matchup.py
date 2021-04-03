import os
import json
from unittest import TestCase, mock

from espyn.matchup import Matchup
from espyn.team_week import TeamWeek


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
TEST_FILE = os.path.join(DATA_DIR, "2020_1603206_sp10.json")


class MatchupTests(TestCase):

    @staticmethod
    def get_mock_league(**kwargs):
        league = mock.Mock()
        league.matchup_num_to_week.return_value = [10]
        league.reg_season_weeks = 12
        league.get_team_by_id.return_value = mock.Mock(full_name="Mock Team")
        league.configure_mock(**kwargs)
        return league

    def setUp(self):
        with open(TEST_FILE) as f:
            data = json.load(f)
        self.matchup_data = data["schedule"][46]
        self.mock_league = self.get_mock_league()

    def test_matchup(self):
        matchup = Matchup(self.matchup_data, self.mock_league)
        self.assertEqual(matchup.matchup_num, 10)
        self.assertEqual(matchup.scoring_periods, [10])
        self.assertFalse(matchup.is_playoff)
        self.assertEqual(matchup.num_weeks, 1)
        self.assertEqual(matchup.home_team_id, 1)
        self.assertEqual(matchup.away_team_id, 3)
        self.assertEqual(matchup.home_team.full_name, "Mock Team")
        self.assertEqual(matchup.away_team.full_name, "Mock Team")
        self.assertEqual(matchup.home_scores, [84.2])
        self.assertEqual(matchup.away_scores, [105.0])
        self.assertEqual(matchup.winner, "AWAY")
        with self.assertRaises(RuntimeError):
            _ = matchup.all_data
        for phrase in ("Matchup #10", "Mock Team", "@", "84.2", "105.0"):
            self.assertIn(phrase, str(matchup))
        ind_scores = matchup.get_individual_scores()
        self.assertIn(84.2, ind_scores)
        self.assertIn(105.0, ind_scores)

    def test_matchup_boxscore(self):
        matchup = Matchup(self.matchup_data, self.mock_league)
        self.assertFalse(matchup.boxscore_loaded)
        self.assertIsNone(matchup.home_data)
        self.assertIsNone(matchup.away_data)
        matchup.set_boxscore_data(self.matchup_data, 10)
        self.assertTrue(matchup.boxscore_loaded)
        self.assertIsInstance(matchup.home_data[0], TeamWeek)
        self.assertIsInstance(matchup.away_data[0], TeamWeek)
        self.assertEqual(len(matchup.all_data), 2)

    def test_bye_matchup(self):
        new_data = {**self.matchup_data}
        del new_data["away"]
        matchup = Matchup(new_data, self.mock_league)
        self.assertTrue(matchup.is_bye)
        matchup.set_boxscore_data(new_data, 10)
        self.assertTrue(matchup.boxscore_loaded)
        self.assertIsNone(matchup.away_team)
        self.assertIn("BYE", str(matchup))
        self.assertEqual(len(matchup.get_individual_scores()), 0)

    def test_matchup_json(self):
        matchup = Matchup(self.matchup_data, self.mock_league)
        data = matchup.to_json()
        keys = ("matchup_num", "team_ids", "home_team_id",
                "away_team_id", "home_score", "away_score", "winner",
                "is_bye", "scoring_periods", "num_weeks", "is_playoff",
                "home_data", "away_data")
        for key in keys:
            self.assertIn(key, data)

    def test_bye_matchup_json(self):
        # some fields should be excluded for byes
        new_data = {**self.matchup_data}
        del new_data["away"]
        matchup = Matchup(new_data, self.mock_league)
        data = matchup.to_json()
        keys = ("home_score", "away_score", "winner")
        for key in keys:
            self.assertNotIn(key, data)
