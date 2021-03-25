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

    def __init__(self, cache_dir):
        if not os.path.exists(cache_dir):
            raise ValueError("The given cache directory does not exist.")
        self.cache_dir = cache_dir

    def load(self, scoring_period=None):
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


class GoogleCloudStorageCache(Cache):

    def __init__(self):
        from google.cloud import storage

        gac = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        bucket_name = os.environ.get("BUCKET_NAME")
        if gac is None or bucket_name is None:
            msg = ("You must set the environment variables 'GOOGLE_APPLICATION_CREDENTIALS'"
                   "and 'BUCKET_NAME' in order to use a Cloud Storage cache.")
            raise RuntimeError(msg)
        try:
            self._client = storage.Client()
            self._bucket = self._client.get_bucket(bucket_name)
        except:
            raise RuntimeError("Unable to connect to the specified Cloud Storage bucket.")

    def load(self, scoring_period=None):
        fname = self._get_filename(scoring_period)
        blob = self._bucket.get_blob(fname)
        if blob:
            raw = blob.download_as_string()
            logging.info(f"Read file {fname} from Cloud Storage.")
            return json.loads(raw)
        return None

    def save(self, data, scoring_period=None):
        fname = self._get_filename(scoring_period)
        blob = self._bucket.blob(fname)
        blob.upload_from_string(json.dumps(data))
        logging.info("Wrote file {fname} to Cloud Storage.")
