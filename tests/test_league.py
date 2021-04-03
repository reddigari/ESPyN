import os
import json
import urllib.request
from io import BytesIO
from unittest import TestCase, mock

from espyn.league import League
from espyn.team import Team
from espyn.matchup import Matchup
from espyn.caches import LocalCache


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
TEST_FILE = os.path.join(DATA_DIR, "2020_1603206_sp10.json")


class LeagueTests(TestCase):

    def get_mock_cache(self, **kwargs):
        cache = mock.Mock()
        cache.load.return_value = self.league_data
        cache.configure_mock(**kwargs)
        return cache

    def setUp(self):
        with open(TEST_FILE) as f:
            self.league_data = json.load(f)

    def test_league_attrs(self):
        cache = self.get_mock_cache()
        league = League(1603206, season=2020, cache=cache)
        cache.load.assert_called()
        self.assertEqual(league.league_id, 1603206)
        self.assertEqual(league.name, "The Ocho, Dos")
        self.assertEqual(league.size, 10)
        self.assertEqual(league.reg_season_weeks, 12)
        self.assertEqual(league.total_matchups, 14)
        self.assertEqual(league.scoring_dict[42], 0.1)
        self.assertIsInstance(league.teams[0], Team)
        for phrase in ("League", "1603206", "The Ocho, Dos", "10"):
            self.assertIn(phrase, str(league))

    def test_league_methods(self):
        cache = self.get_mock_cache()
        league = League(1603206, season=2020, cache=cache)
        # matchup period mapping
        self.assertEqual(league.matchup_num_to_week(1), [1])
        self.assertEqual(set(league.matchup_num_to_week(14)), {15, 16})
        self.assertEqual(league.week_to_matchup_num(16), 14)
        team = league.get_team_by_id(7)
        self.assertIsInstance(team, Team)
        self.assertEqual(team.team_id, 7)
        self.assertEqual(len(league.all_scores()), 160)
        self.assertEqual(len(league.all_scores(False)), 120)
        self.assertAlmostEqual(league.average_score(), 94.199, 3)
        self.assertAlmostEqual(league.average_score(False), 95.300, 3)
        # matchup getters
        matchup = league.get_matchup(1, 7)
        self.assertIsInstance(matchup, Matchup)
        self.assertEqual(matchup.home_team_id, 7)
        self.assertIsNone(league.get_matchup(99, 7))
        matchups = league.get_matchups_by_number(1)
        self.assertEqual(len(matchups), 5)
        # populate matchup 10 boxscores (static data is from week 10)
        matchups = league.get_matchups_by_number(10, boxscore=True)
        for m in matchups:
            self.assertTrue(m.boxscore_loaded)

    def test_uncached_league(self):
        def get_stream():
            return BytesIO(json.dumps(self.league_data).encode())
        urllib.request.urlopen = mock.Mock(return_value=get_stream())
        league = League(1603206, season=2020)
        urllib.request.urlopen.assert_called()
        matchup = league.get_matchup(10, 7)
        self.assertFalse(matchup.boxscore_loaded)
        # reset mock data stream before requesting boxscore data
        urllib.request.urlopen = mock.Mock(return_value=get_stream())
        matchup = league.get_matchup(10, 7, boxscore=True)
        self.assertTrue(matchup.boxscore_loaded)

    def test_bad_network_data(self):
        bad_stream = mock.Mock()
        bad_stream.read.side_effect = urllib.request.URLError("")
        urllib.request.urlopen = mock.Mock(return_value=bad_stream)
        with self.assertRaises(ValueError):
            League(1603206, season=2020)


    def test_league_json(self):
        cache = self.get_mock_cache()
        league = League(1603206, season=2020, cache=cache)
        data = league.to_json()
        keys = ("league_id", "league_name", "league_size", "teams",
                "reg_season_weeks", "total_matchups", "matchups",
                "all_scores")
        for key in keys:
            self.assertIn(key, data)
