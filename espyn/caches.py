import os
import json
import logging
from typing import Any, Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .league import League


class Cache:
    """Abstract base class for caches"""

    def set_league(self, league: "League") -> None:
        """Set league to be used with cache

        :param league: league whose data will be cached
        :type league: League
        """
        self.league = league

    def load(self, scoring_period: Optional[int] = None) -> Any:
        """Load data from cache

        If `scoring_period` is given, the API response containing
        that period's boxscores will be loaded.

        :param scoring_period: scoring period to load (optional)
        :type scoring_period: Optional[int]
        :return: JSON-deserialized cache entry
        :rtype: Any
        """
        raise NotImplementedError()

    def save(self, data: Any,
             scoring_period: Optional[int] = None) -> None:
        """Save data to cache

        :param data: JSON-serializable data to cache
        :type data: Any
        :param scoring_period: scoring period of boxscores in data
        :type scoring_period: Optional[int]
        """
        raise NotImplementedError()

    def _get_filename(self, scoring_period=None):
        season = self.league.season
        league_id = self.league.league_id
        if scoring_period is None:
            return f"{season}_{league_id}.json"
        return f"{season}_{league_id}_sp{scoring_period:02d}.json"


class LocalCache(Cache):
    """Concrete `Cache` implementation to read/write local JSON files"""

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


def cache_operation(func: Callable) -> Callable:
    """Wrap a `League` method in cache load/save attempts

    Decorated methods will first pass their parameters to the `load`
    method of the `League`'s `Cache` instance. If the cache hits,
    the data are returned. Otherwise the decorated method is called,
    and the retrieved data are passed to the `Cache`'s `save` method
    with the parameters of the original call.

    The first parameter of the decorated method is expected to have
    a `cache` attribute (typically the `League` instance).
    The decorator is dependent on the `load` and `save` methods
    expecting the same parameters as the decorated functions.

    :param func: function/method to decorate
    :type func: Callable
    :return: decorated function/method
    :rtype: Callable
    """
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
