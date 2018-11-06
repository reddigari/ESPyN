import os
import json
import logging
from google.cloud import storage


class LocalCache():

    def __init__(self, cache_dir):
        if not os.path.exists(cache_dir):
            raise ValueError("The given cache directory does not exist.")
        self.cache_dir = cache_dir

    def read_from_cache(self, fname):
        fpath = os.path.join(self.cache_dir, fname)
        try:
            with open(fpath, "r") as f:
                data = json.load(f)
            logging.info("Read file {} from local cache.".format(fname))
            return data
        except:
            return None

    def write_to_cache(self, data, fname):
        fpath = os.path.join(self.cache_dir, fname)
        with open(fpath, "w") as f:
            json.dump(data, f)
        logging.info("Wrote file {} to local cache.".format(fname))


class CloudStorageCache():

    def __init__(self):
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

    def read_from_cache(self, fname):
        blob = self._bucket.get_blob(fname)
        if blob:
            raw = blob.download_as_string()
            logging.info("Read file {} from Cloud Storage.".format(fname))
            return json.loads(raw)
        return None

    def write_to_cache(self, data, fname):
        blob = self._bucket.blob(fname)
        blob.upload_from_string(json.dumps(data))
        logging.info("Wrote file {} to Cloud Storage.".format(fname))
