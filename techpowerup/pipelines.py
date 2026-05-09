# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


from itemadapter import ItemAdapter
import csv
import json


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
        return item

    def close_spider(self, spider):
        self.cpu_file.close()
        self.gpu_file.close()


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
        return item

    def close_spider(self, spider):
        with open("cpus.json", "w", encoding='utf-8') as f:
            json.dump(self.cpu_items, f, ensure_ascii=False, indent=2)
        with open("gpus.json", "w", encoding='utf-8') as f:
            json.dump(self.gpu_items, f, ensure_ascii=False, indent=2)


# Keep the old class name as an alias for backward compatibility,
# but route to the correct pipeline based on OUTPUT_FORMAT setting.
class TechpowerupPipeline:

    @classmethod
    def from_crawler(cls, crawler):
        format = crawler.settings.get('OUTPUT_FORMAT', 'csv')
        if format == 'json':
            return JsonPipeline()
        return CsvPipeline()
