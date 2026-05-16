from datetime import datetime
from pathlib import Path
from time import perf_counter

import scrapy
from scrapy import signals

from techpowerup.crawl_metrics import CrawlMetrics

years = range(2024, datetime.now().year + 1)
gpu_urls = [f'https://www.techpowerup.com/gpu-specs/?year={year}' for year in years]
cpu_urls = [f'https://www.techpowerup.com/cpu-specs/?year={year}' for year in years]

class TpuSpider(scrapy.Spider):
    name = 'tpu'
    allowed_domains = ['www.techpowerup.com']
    handle_httpstatus_list = [403,404,429,410,500]

    def __init__(self, *args, cookie='', retry_failed_file='', **kwargs):
        super().__init__(*args, **kwargs)
        self.failed_urls = []
        self.cookie = cookie
        self.retry_failed_file = retry_failed_file
        self.metrics = CrawlMetrics()
        self.start_urls_count = 0

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(TpuSpider, cls).from_crawler(crawler, *args, **kwargs)
        spider.cookie = crawler.settings.get('BROWSER_COOKIE', '')
        crawler.signals.connect(spider.handle_spider_closed, signals.spider_closed)
        return spider

    def start_requests(self):
        urls = self.load_start_urls()
        self.start_urls_count = len(urls)
        headers = {}
        if self.cookie:
            headers['Cookie'] = self.cookie

        self.logger.info(
            "crawl_start urls=%s years=%s-%s cookie_present=%s retry_failed_file=%s",
            self.start_urls_count,
            years.start,
            years.stop - 1,
            bool(self.cookie),
            self.retry_failed_file or "",
        )

        for url in urls:
            yield scrapy.Request(
                url,
                headers=headers,
                meta={"request_started_at": perf_counter()},
            )

    def load_start_urls(self):
        if not self.retry_failed_file:
            return gpu_urls + cpu_urls

        urls = []
        seen = set()
        failed_path = Path(self.retry_failed_file)
        for line in failed_path.read_text(encoding="utf-8").splitlines():
            url = line.strip()
            if not url or url.startswith("#") or url in seen:
                continue
            seen.add(url)
            urls.append(url)
        return urls

    def parse(self, response):
        if response.status in [403, 404, 429, 410, 500]:
            self.crawler.stats.inc_value('failed_url_count')
            self.failed_urls.append(response.url)
            started_at = response.meta.get("request_started_at")
            elapsed = perf_counter() - started_at if started_at else 0.0
            cached = "cached" in getattr(response, "flags", [])
            self.metrics.record_response(response.url, response.status, elapsed, cached, 0)
            self.logger.warning(
                "response_failed url=%s status=%s elapsed=%.3fs cached=%s",
                response.url,
                response.status,
                elapsed,
                cached,
            )
            return

        started_at = response.meta.get("request_started_at")
        elapsed = perf_counter() - started_at if started_at else 0.0
        cached = "cached" in getattr(response, "flags", [])

        if "gpu" in response.url:
            items = list(self.parse_gpu(response))
        elif "cpu" in response.url:
            items = list(self.parse_cpu(response))
        else:
            items = []

        self.metrics.record_response(
            url=response.url,
            status=response.status,
            elapsed=elapsed,
            cached=cached,
            item_count=len(items),
        )
        self.logger.info(
            "response url=%s status=%s elapsed=%.3fs cached=%s items=%s",
            response.url,
            response.status,
            elapsed,
            cached,
            len(items),
        )

        for item in items:
            self.metrics.record_item(item.get('type'))
            yield item

    def parse_gpu(self, response):
        rows = response.xpath('//div[@id="list"]//table//tr[contains(@class, "vendor-")]')
        for row in rows:
            name = row.xpath('.//div[@class="item-name"]/a/text()').get('')
            released = row.xpath('.//div[@class="item-released"]/text()').get('')
            chip = row.xpath('.//div[@class="item-chip"]/a/text()').get('')

            tds = row.xpath('./td')
            bus = self.clean_text(tds[1]) if len(tds) > 1 else ''
            memory = self.clean_text(tds[2]) if len(tds) > 2 else ''
            gpu_clock = self.clean_text(tds[3]) if len(tds) > 3 else ''
            mem_clock = self.clean_text(tds[4]) if len(tds) > 4 else ''
            shaders = self.clean_text(tds[5]) if len(tds) > 5 else ''

            if name:
                yield {
                    'Product_Name': name.strip(),
                    'GPU_Chip': chip.strip(),
                    'Released': released.strip(),
                    'Bus': bus,
                    'Memory': memory,
                    'GPU_clock': gpu_clock,
                    'Memory_clock': mem_clock,
                    'Shaders_TMUs_ROPs': shaders,
                    'type': 'GPU'
                }

    def parse_cpu(self, response):
        rows = response.xpath('//div[@id="list"]//table//tr[contains(@class, "vendor-")]')
        for row in rows:
            tds = row.xpath('./td')
            if len(tds) < 8:
                continue

            name = tds[0].xpath('.//a/text()').get('')
            codename = self.clean_text(tds[1])
            cores = self.clean_text(tds[2])
            clock = self.clean_text(tds[3])
            socket = self.clean_text(tds[4])
            process = self.clean_text(tds[5])
            l3_cache = self.clean_text(tds[6])
            tdp = self.clean_text(tds[7])
            released = self.clean_text(tds[8]) if len(tds) > 8 else ''

            if name:
                yield {
                    'Name': name.strip(),
                    'Codename': codename,
                    'Cores': cores,
                    'Clock': clock,
                    'Socket': socket,
                    'Process': process,
                    'L3 Cache': l3_cache,
                    'TDP': tdp,
                    'Released': released,
                    'type': 'CPU'
                }

    def clean_text(self, td):
        text = td.xpath('string(.)').get('')
        return ' '.join(text.split()).strip()

    def handle_spider_closed(self, reason):
        summary = self.metrics.summary()
        failed_urls = summary["failed_urls"]
        self.crawler.stats.set_value('failed_urls', ', '.join(failed_urls))
        self.crawler.stats.set_value('metrics/elapsed_seconds', summary["elapsed_seconds"])
        self.crawler.stats.set_value('metrics/response_count', summary["response_count"])
        self.crawler.stats.set_value('metrics/cache_hits', summary["cache_hits"])
        self.crawler.stats.set_value('metrics/parsed_items', summary["parsed_items"])

        failed_file = self.crawler.settings.get("FAILED_URLS_FILE", "failed_urls.txt")
        if failed_urls:
            failed_path = Path(failed_file)
            if failed_path.parent != Path("."):
                failed_path.parent.mkdir(parents=True, exist_ok=True)
            failed_path.write_text("\n".join(failed_urls) + "\n", encoding="utf-8")

        # English/中文: one compact run summary makes performance comparisons easy.
        # 中文/English：用一条紧凑的运行摘要，方便比较不同性能配置。
        self.logger.info(
            "crawl_summary reason=%s elapsed=%.3fs responses=%s statuses=%s cache_hits=%s items=%s item_counts=%s failed=%s",
            reason,
            summary["elapsed_seconds"],
            summary["response_count"],
            summary["status_counts"],
            summary["cache_hits"],
            summary["parsed_items"],
            summary["item_counts"],
            len(failed_urls),
        )
