import unittest
from unittest.mock import patch

from scrapy.http import Request, Response
from scrapy.settings import Settings

from techpowerup.middlewares import RetryAfterMiddleware


class DummyCrawler:
    def __init__(self, settings):
        self.settings = settings


class RetryAfterMiddlewareTests(unittest.TestCase):
    def test_429_response_sleeps_for_retry_after_header(self):
        crawler = DummyCrawler(Settings({"TPU_RETRY_AFTER_MAX_DELAY": 5}))
        middleware = RetryAfterMiddleware.from_crawler(crawler)
        request = Request("https://www.techpowerup.com/gpu-specs/?year=2026")
        response = Response(
            request.url,
            status=429,
            headers={"Retry-After": "3"},
            request=request,
        )

        with patch("techpowerup.middlewares.sleep") as sleep:
            result = middleware.process_response(request, response, spider=None)

        self.assertIs(result, response)
        sleep.assert_called_once_with(3)

    def test_non_429_response_does_not_sleep(self):
        crawler = DummyCrawler(Settings({"TPU_RETRY_AFTER_DEFAULT_DELAY": 0}))
        middleware = RetryAfterMiddleware.from_crawler(crawler)
        request = Request("https://www.techpowerup.com/gpu-specs/?year=2026")
        response = Response(request.url, status=200, request=request)

        with patch("techpowerup.middlewares.sleep") as sleep:
            result = middleware.process_response(request, response, spider=None)

        self.assertIs(result, response)
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
