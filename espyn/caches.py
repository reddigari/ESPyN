import os
import json
import logging


class Cache:
    def set_league(self, league):
        self.league = league

    def load(self, scoring_period=None):
        raise NotImplementedError()

    def save(self, data, scoring_period=None):
        raise NotImplementedError()

    def _get_filename(self, scoring_period=None):
        season = self.league.season
        league_id = self.league.league_id
        if scoring_period is None:
            return f"{season}_{league_id}.json"
        return f"{season}_{league_id}_sp{scoring_period:02d}.json"


class LocalCache(Cache):

    def __init__(self, cache_dir, ignore_cache=False):
        if not os.path.exists(cache_dir):
            raise ValueError("The given cache directory does not exist.")
        self.cache_dir = cache_dir
        self.ignore_cache = ignore_cache

    def load(self, scoring_period=None):
        if self.ignore_cache:
            return None
        fname = self._get_filename(scoring_period)
        fpath = os.path.join(self.cache_dir, fname)
        try:
            with open(fpath, "r") as f:
                data = json.load(f)
            logging.info(f"Read file {fname} from local cache.")
            return data
        except:
            return None

    def save(self, data, scoring_period=None):
        fname = self._get_filename(scoring_period)
        fpath = os.path.join(self.cache_dir, fname)
        with open(fpath, "w") as f:
            json.dump(data, f)
        logging.info(f"Wrote file {fname} to local cache.")


def cache_operation(func):
    def wrapped(*args):
        cache = getattr(args[0], "cache", None)
        # if no cache, call the wrapped function as-is
        if cache is None:
            return func(*args)
        # otherwise, try returning data from cache
        data = cache.load(*args[1:])
        if data:
            return data
        # if the cache missed, call the wrapped function,
        # then write the data to the cache
        data = func(*args)
        cache.save(data, *args[1:])
        return data

    return wrapped
