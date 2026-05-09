import scrapy
from scrapy import signals
from datetime import datetime

years = range(2024, datetime.now().year + 1)
gpu_urls = [f'https://www.techpowerup.com/gpu-specs/?year={year}' for year in years]
cpu_urls = [f'https://www.techpowerup.com/cpu-specs/?year={year}' for year in years]

class TpuSpider(scrapy.Spider):
    name = 'tpu'
    allowed_domains = ['www.techpowerup.com']
    handle_httpstatus_list = [403,404,429,410,500]

    def __init__(self, *args, cookie='', **kwargs):
        super().__init__(*args, **kwargs)
        self.failed_urls = []
        self.cookie = cookie

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(TpuSpider, cls).from_crawler(crawler, *args, **kwargs)
        spider.cookie = crawler.settings.get('BROWSER_COOKIE', '')
        crawler.signals.connect(spider.handle_spider_closed, signals.spider_closed)
        return spider

    def start_requests(self):
        urls = gpu_urls + cpu_urls
        headers = {}
        if self.cookie:
            headers['Cookie'] = self.cookie
        for url in urls:
            yield scrapy.Request(url, headers=headers)

    def parse(self, response):
        if response.status in [403, 404, 429, 410, 500]:
            self.crawler.stats.inc_value('failed_url_count')
            self.failed_urls.append(response.url)
            return

        if "gpu" in response.url:
            yield from self.parse_gpu(response)
        elif "cpu" in response.url:
            yield from self.parse_cpu(response)

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
        self.crawler.stats.set_value('failed_urls', ', '.join(self.failed_urls))
