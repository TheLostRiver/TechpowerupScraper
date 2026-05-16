# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from time import sleep

from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter


class TechpowerupSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class TechpowerupDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class RetryAfterMiddleware:
    def __init__(self, default_delay=30.0, max_delay=60.0):
        self.default_delay = default_delay
        self.max_delay = max_delay

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        return cls(
            default_delay=settings.getfloat("TPU_RETRY_AFTER_DEFAULT_DELAY", 30.0),
            max_delay=settings.getfloat("TPU_RETRY_AFTER_MAX_DELAY", 60.0),
        )

    def process_response(self, request, response, spider):
        if response.status != 429:
            return response

        delay = self.retry_after_delay(response)
        if delay > 0:
            if spider:
                spider.logger.warning(
                    "retry_after_backoff url=%s delay=%.3fs",
                    response.url,
                    delay,
                )
            sleep(delay)
        return response

    def retry_after_delay(self, response):
        value = response.headers.get("Retry-After")
        if not value:
            return self.default_delay

        text = value.decode("utf-8", errors="ignore").strip()
        try:
            delay = float(text)
        except ValueError:
            delay = self.retry_after_http_date_delay(text)

        return max(0.0, min(delay, self.max_delay))

    def retry_after_http_date_delay(self, text):
        try:
            retry_at = parsedate_to_datetime(text)
        except (TypeError, ValueError):
            return self.default_delay

        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        return (retry_at - datetime.now(timezone.utc)).total_seconds()
