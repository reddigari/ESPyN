import os
import json
from unittest import TestCase, mock
from tempfile import TemporaryDirectory

from ..caches import Cache, LocalCache, cache_operation


class CacheTests(TestCase):

    def get_mock_league(self, **kwargs):
        league = mock.Mock(season=2019, league_id=9999)
        league.configure_mock(**kwargs)
        return league

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.mock_league = self.get_mock_league()
        self.data = dict(zip("abcdef", range(6)))

    def test_base_cache(self):
        cache = Cache()
        with self.assertRaises(NotImplementedError):
            cache.load()
        with self.assertRaises(NotImplementedError):
            cache.save(None)
        cache.set_league(self.mock_league)
        self.assertIs(cache.league, self.mock_league)

    def test_cache_load(self):
        cache = LocalCache(self.tmp.name)
        cache.set_league(self.mock_league)
        wo_sp_name = os.path.join(self.tmp.name, "2019_9999.json")
        w_sp_name = os.path.join(self.tmp.name, "2019_9999_sp01.json")
        # cache miss
        self.assertIsNone(cache.load())
        self.assertIsNone(cache.load(1))
        # write file so cache hits
        with open(wo_sp_name, "w") as f:
            json.dump(self.data, f)
        data = cache.load()
        self.assertEqual(data, self.data)
        with open(w_sp_name, "w") as f:
            json.dump(self.data, f)
        data = cache.load(1)
        self.assertEqual(data, self.data)
        # ignore hit on purpose
        cache = LocalCache(self.tmp.name, ignore_cache=True)
        cache.set_league(self.mock_league)
        self.assertTrue(os.path.exists(wo_sp_name))
        self.assertIsNone(cache.load())

    def test_cache_save(self):
        cache = LocalCache(self.tmp.name)
        cache.set_league(self.mock_league)
        # save data with no scoring period
        expected_fname = os.path.join(self.tmp.name, "2019_9999.json")
        cache.save(self.data)
        self.assertTrue(os.path.exists(expected_fname))
        with open(expected_fname) as f:
            self.assertEqual(self.data, json.load(f))
        # save data with scoring period
        expected_fname = os.path.join(self.tmp.name, "2019_9999_sp14.json")
        cache.save(self.data, 14)
        self.assertTrue(os.path.exists(expected_fname))
        with open(expected_fname) as f:
            self.assertEqual(self.data, json.load(f))

    def test_invalid_cache(self):
        not_real_dir = "/tmp/laskdjflaskdfla"
        self.assertFalse(os.path.exists(not_real_dir))
        with self.assertRaises(ValueError):
            cache = LocalCache(not_real_dir)

    def test_cache_decorator(self):
        # decorated function to test
        @cache_operation
        def decorated(league):
            return 42

        # when first arg has no cache attr, `decorated` should fire
        self.assertEqual(decorated(None), 42)

        # setup cache and league
        cache = LocalCache(self.tmp.name)
        league = self.get_mock_league(cache=cache) # league needs cache attr
        cache.set_league(league)

        # when first arg has cache that misses, `decorated` should fire
        self.assertEqual(decorated(league), 42)

        # write file so cache hits
        wo_sp_name = os.path.join(self.tmp.name, "2019_9999.json")
        with open(wo_sp_name, "w") as f:
            json.dump(self.data, f)

        # when first arg has cache that hits, expect that data
        self.assertEqual(decorated(league), self.data)


    def tearDown(self):
        self.tmp.cleanup()

