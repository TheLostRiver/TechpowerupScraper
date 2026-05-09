from collections import Counter
from time import perf_counter


class CrawlMetrics:
    """Collect lightweight crawl metrics.

    收集轻量级爬虫指标。

    This class intentionally has no Scrapy dependency so it can be unit-tested
    without network or crawler setup.

    该类刻意不依赖 Scrapy，便于在没有网络和爬虫环境的情况下做单元测试。
    """

    def __init__(self, clock=perf_counter):
        self.clock = clock
        self.started_at = self.clock()
        self.response_count = 0
        self.status_counts = Counter()
        self.cache_hits = 0
        self.failed_urls = []
        self.parsed_items = 0
        self.item_counts = Counter()
        self.total_response_seconds = 0.0

    def record_response(self, url, status, elapsed, cached, item_count):
        """Record one downloaded response.

        记录一次下载响应。
        """

        self.response_count += 1
        self.status_counts[status] += 1
        self.total_response_seconds += elapsed
        self.parsed_items += item_count

        if cached:
            self.cache_hits += 1

        if status >= 400:
            self.failed_urls.append(url)

    def record_item(self, item_type):
        """Record one emitted item by hardware type.

        按硬件类型记录一条已产出的 item。
        """

        if item_type:
            self.item_counts[item_type] += 1

    def summary(self):
        """Return a JSON-serializable metrics snapshot.

        返回可 JSON 序列化的指标快照。
        """

        elapsed = self.clock() - self.started_at
        return {
            "elapsed_seconds": round(elapsed, 3),
            "response_count": self.response_count,
            "status_counts": dict(self.status_counts),
            "cache_hits": self.cache_hits,
            "failed_urls": list(self.failed_urls),
            "parsed_items": self.parsed_items,
            "item_counts": dict(self.item_counts),
            "total_response_seconds": round(self.total_response_seconds, 3),
        }
