import os
import json
from unittest import TestCase, mock

from espyn.team import Team
from espyn.constants import SEASON_OVER


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
TEST_FILE = os.path.join(DATA_DIR, "2020_1603206_sp10.json")


class TeamTests(TestCase):

    @staticmethod
    def get_mock_league(**kwargs):
        league = mock.Mock()
        league.draft_order.index.return_value = 99
        league.name_from_user_id.return_value = "Mockboi"
        league.total_matchups = 14
        league.current_matchup_num.return_value = 5
        league.configure_mock(**kwargs)
        return league

    def setUp(self):
        with open(TEST_FILE) as f:
            data = json.load(f)
        self.team_data = data["teams"][0]
        self.mock_league = self.get_mock_league()

    def test_team_attrs(self):
        league = self.get_mock_league()
        team = Team(self.team_data, league)
        self.assertEqual(team.team_id, 1)
        # implicitly tests multiple attributes
        self.assertEqual(str(team), "Team 1 : Mockboi : Quatro Quatro : 6-6-0")
        self.assertAlmostEqual(team.points_for, 1210.3)
        self.assertAlmostEqual(team.points_against, 1146.0)
        self.assertEqual(team.winning_pct, 0.5)
        self.assertEqual(team.draft_position, 100)

    def test_team_methods(self):
        league = self.get_mock_league()
        team = Team(self.team_data, league)
        _ = team.get_matchup(1)
        league.get_matchup.assert_called_with(1, 1, False)
        _ = team.get_data_by_matchup(7)
        league.get_matchup.assert_called_with(7, 1, True)
        # make sure home/away branching is covered
        league.get_matchup.return_value = mock.Mock(
            home_team_id=team.team_id, home_data=22)
        data = team.get_data_by_matchup(7)
        self.assertIs(data, 22)

    def test_team_scores(self):
        league = self.get_mock_league()
        team = Team(self.team_data, league)
        matchup = mock.Mock()
        league.get_matchup.return_value = matchup
        # always home team
        matchup.configure_mock(home_team_id=1, home_scores=[10],
                               is_bye=False)
        scores = team.scores()
        self.assertEqual(len(scores), 4)
        self.assertEqual(sum(scores), 40)
        # always away team
        matchup.configure_mock(away_team_id=1, away_scores=[20],
                               home_team_id=None)
        self.assertEqual(sum(team.scores()), 80)
        # season over (expect `league.total_matchups` scores)
        league.current_matchup_num.return_value = SEASON_OVER
        self.assertEqual(len(team.scores()), league.total_matchups)
        # all playoff matchups (expect 0 scores)
        matchup.configure_mock(is_playoff=True)
        scores = team.scores(include_playoffs=False)
        self.assertEqual(len(scores), 0)

    def test_ownerless_team(self):
        new_data = {k: v for k, v in self.team_data.items() if k != "owners"}
        team = Team(new_data, self.mock_league)
        self.assertEqual(team.owner, "<NO OWNER>")

    def test_team_json(self):
        league = self.get_mock_league()
        team = Team(self.team_data, league)
        data = team.to_json()
        keys = ("team_id", "team_abbrev", "team_location",
                "team_nickname", "owner", "division_id", "points_for",
                "points_against", "wins", "losses", "ties",
                "winning_pct", "transactions", "draft_position",
                "scores")
        for key in keys:
            self.assertIn(key, data)
