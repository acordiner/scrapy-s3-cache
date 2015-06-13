from moto import mock_s3
from scrapy import Request
from scrapy.http import Response
from scrapy.tests.test_downloadermiddleware_httpcache import _BaseTest


class S3BackendTest(_BaseTest):

    storage_class = 's3cache.S3CacheStorage'

    def _get_settings(self, **new_settings):
        settings = super(S3BackendTest, self)._get_settings(**new_settings)
        settings.set('S3CACHE_BUCKET', 'mybucket')
        return settings

    @mock_s3
    def test_store_and_retrieve_s3(self):

        with self._storage() as storage:

            request1 = Request('http://www.example.com/page1')
            response1 = Response(request1.url,
                                 headers={'Content-Type': 'text/html'},
                                 body='test body 1',
                                 status=200)
            assert storage.retrieve_response(self.spider, request1) is None

            # store response, closing and re-opening spider to flush to s3
            storage.store_response(self.spider, request1, response1)
            storage.close_spider(self.spider)
            storage.open_spider(self.spider)

            self.assertEqualResponse(response1, storage.retrieve_response(self.spider, request1))

            request2 = Request('http://www.example.com/page2')
            response2 = Response(request2.url,
                                 headers={'Content-Type': 'text/html'},
                                 body='test body 2',
                                 status=200)

            # don't flush response to s3 yet; instead load from the local disk
            storage.store_response(self.spider, request2, response2)
            self.assertEqualResponse(response2, storage.retrieve_response(self.spider, request2))