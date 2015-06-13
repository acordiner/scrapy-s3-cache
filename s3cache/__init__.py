import pickle
import tempfile
from boto.s3.connection import S3Connection
import os
from boto.utils import parse_ts
import datetime
from scrapy.exceptions import NotConfigured
from scrapy.responsetypes import responsetypes
from scrapy.contrib.httpcache import FilesystemCacheStorage
from scrapy.http import Headers
from scrapy.utils.project import data_path
import shutil
from w3lib.http import headers_raw_to_dict


class S3CacheStorage(FilesystemCacheStorage):

    def __init__(self, settings):
        super(S3CacheStorage, self).__init__(settings)
        self.tmpcachedir = data_path(settings.get(
            'S3CACHE_TEMPDIR',
            os.path.join(tempfile.tempdir, '.s3cache'),
        ))
        self.aws_access_key = settings['AWS_ACCESS_KEY_ID']
        self.aws_secret_key = settings['AWS_SECRET_ACCESS_KEY']
        self.bucket_name = settings['S3CACHE_BUCKET']
        if self.bucket_name is None:
            raise NotConfigured("S3CACHE_BUCKET must be specified")
        self._conn = None

    @property
    def conn(self):
        if self._conn is None:
            self._conn = S3Connection(self.aws_access_key, self.aws_secret_key)
        return self._conn

    def close_spider(self, spider):
        # move data from tmpcachedir to S3 bucket "cachedir"
        bucket = self.conn.create_bucket(self.bucket_name)
        for root, dirs, filenames in os.walk(self.tmpcachedir):
            for filename in filenames:
                local_path = os.path.join(root, filename)
                remote_path = os.path.relpath(local_path, self.tmpcachedir).lower()
                key = bucket.new_key(remote_path)
                with open(local_path) as fp:
                    key.set_contents_from_file(fp)
            if not dirs and filenames:  # delete leaf directories
                shutil.rmtree(root)

    def retrieve_response(self, spider, request):
        response = super(S3CacheStorage, self).retrieve_response(spider, request)
        if response is None:  # not in local filesystem cache, so try copying from s3
            local_path = self._get_request_path(spider, request)
            remote_path = os.path.relpath(local_path, self.tmpcachedir).lower()
            bucket = self.conn.get_bucket(self.bucket_name, validate=False)

            def _get_key(filename):
                key_name = os.path.join(remote_path, filename)
                return bucket.get_key(key_name)

            # check if the key exists
            metadata_key = _get_key('pickled_meta')
            if metadata_key is None:
                return None  # key not found

            # check if the cache entry has expired
            mtime = parse_ts(metadata_key.last_modified)
            if 0 < self.expiration_secs < (datetime.datetime.utcnow() - mtime).total_seconds():
                return None  # expired

            # deserialise the cached response
            metadata = pickle.loads(metadata_key.get_contents_as_string())
            body = _get_key('response_body').get_contents_as_string()
            rawheaders = _get_key('response_headers').get_contents_as_string()
            url = metadata.get('response_url')
            status = metadata['status']
            headers = Headers(headers_raw_to_dict(rawheaders))
            respcls = responsetypes.from_args(headers=headers, url=url)
            response = respcls(url=url, headers=headers, status=status, body=body)

        return response

    def _get_request_path(self, spider, request):
        path = super(S3CacheStorage, self)._get_request_path(spider, request)
        tmppath = os.path.join(self.tmpcachedir, os.path.relpath(path, self.cachedir))
        return tmppath