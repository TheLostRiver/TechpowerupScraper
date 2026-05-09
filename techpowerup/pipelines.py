# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


from itemadapter import ItemAdapter
import csv
import json
from time import perf_counter


gpu_columns =['Product_Name','GPU_Chip', 'Released','Bus', 'Memory', 'GPU_clock', 'Memory_clock','Shaders_TMUs_ROPs']

cpu_columns = ['Name', 'Codename', 'Cores', 'Clock', 'Socket', 'Process', 'L3 Cache', 'TDP', 'Released']


class CsvPipeline:

    def __init__(self):
        self.cpu_file = open("cpus.csv", "w", newline='', encoding='utf-8')
        self.gpu_file = open("gpus.csv", "w", newline='', encoding='utf-8')
        self.cpu_writer = csv.DictWriter(self.cpu_file, fieldnames=cpu_columns)
        self.gpu_writer = csv.DictWriter(self.gpu_file, fieldnames=gpu_columns)
        self.cpu_writer.writeheader()
        self.gpu_writer.writeheader()

    def process_item(self, item, spider):
        row = {k: v for k, v in item.items() if k != 'type'}
        if item.get('type') == 'CPU':
            self.cpu_writer.writerow(row)
        elif item.get('type') == 'GPU':
            self.gpu_writer.writerow(row)

        # English/中文: expose output volume in Scrapy stats for benchmarks.
        # 中文/English：把输出数量写入 Scrapy stats，便于性能基准对比。
        item_type = item.get("type")
        if item_type:
            spider.crawler.stats.inc_value(f"pipeline/{item_type.lower()}_items")
        return item

    def close_spider(self, spider):
        started_at = perf_counter()
        self.cpu_file.close()
        self.gpu_file.close()
        elapsed = perf_counter() - started_at
        spider.crawler.stats.set_value("pipeline/csv_close_seconds", round(elapsed, 3))
        spider.logger.info("pipeline_csv_closed elapsed=%.3fs", elapsed)


class JsonPipeline:

    def __init__(self):
        self.cpu_items = []
        self.gpu_items = []

    def process_item(self, item, spider):
        row = {k: v for k, v in item.items() if k != 'type'}
        if item.get('type') == 'CPU':
            self.cpu_items.append(row)
        elif item.get('type') == 'GPU':
            self.gpu_items.append(row)

        # English/中文: keep item counters independent from output format.
        # 中文/English：item 计数不依赖具体输出格式。
        item_type = item.get("type")
        if item_type:
            spider.crawler.stats.inc_value(f"pipeline/{item_type.lower()}_items")
        return item

    def close_spider(self, spider):
        started_at = perf_counter()
        with open("cpus.json", "w", encoding='utf-8') as f:
            json.dump(self.cpu_items, f, ensure_ascii=False, indent=2)
        with open("gpus.json", "w", encoding='utf-8') as f:
            json.dump(self.gpu_items, f, ensure_ascii=False, indent=2)
        elapsed = perf_counter() - started_at
        spider.crawler.stats.set_value("pipeline/json_write_seconds", round(elapsed, 3))
        spider.logger.info(
            "pipeline_json_written cpus=%s gpus=%s elapsed=%.3fs",
            len(self.cpu_items),
            len(self.gpu_items),
            elapsed,
        )


# Keep the old class name as an alias for backward compatibility,
# but route to the correct pipeline based on OUTPUT_FORMAT setting.
class TechpowerupPipeline:

    @classmethod
    def from_crawler(cls, crawler):
        format = crawler.settings.get('OUTPUT_FORMAT', 'csv')
        if format == 'json':
            return JsonPipeline()
        return CsvPipeline()
