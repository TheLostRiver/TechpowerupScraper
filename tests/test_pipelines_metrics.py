import json
import os
import tempfile
import unittest

from techpowerup.pipelines import CsvPipeline, JsonPipeline


class FakeStats:
    def __init__(self):
        self.values = {}

    def inc_value(self, key):
        self.values[key] = self.values.get(key, 0) + 1

    def set_value(self, key, value):
        self.values[key] = value


class FakeLogger:
    def info(self, *args, **kwargs):
        pass


class FakeSpider:
    def __init__(self):
        self.crawler = type("Crawler", (), {"stats": FakeStats()})()
        self.logger = FakeLogger()


class PipelineMetricsTests(unittest.TestCase):
    def test_json_pipeline_counts_items_and_records_write_time(self):
        spider = FakeSpider()
        pipeline = JsonPipeline()

        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                pipeline.process_item({"Name": "Example CPU", "type": "CPU"}, spider)
                pipeline.process_item({"Product_Name": "Example GPU", "type": "GPU"}, spider)
                pipeline.close_spider(spider)

                with open("cpus.json", "r", encoding="utf-8") as f:
                    cpus = json.load(f)
                with open("gpus.json", "r", encoding="utf-8") as f:
                    gpus = json.load(f)
            finally:
                os.chdir(old_cwd)

        self.assertEqual(cpus, [{"Name": "Example CPU"}])
        self.assertEqual(gpus, [{"Product_Name": "Example GPU"}])
        self.assertEqual(spider.crawler.stats.values["pipeline/cpu_items"], 1)
        self.assertEqual(spider.crawler.stats.values["pipeline/gpu_items"], 1)
        self.assertIn("pipeline/json_write_seconds", spider.crawler.stats.values)

    def test_csv_pipeline_counts_items_and_records_close_time(self):
        spider = FakeSpider()

        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                pipeline = CsvPipeline()
                pipeline.process_item({"Name": "Example CPU", "type": "CPU"}, spider)
                pipeline.process_item({"Product_Name": "Example GPU", "type": "GPU"}, spider)
                pipeline.close_spider(spider)
            finally:
                os.chdir(old_cwd)

        self.assertEqual(spider.crawler.stats.values["pipeline/cpu_items"], 1)
        self.assertEqual(spider.crawler.stats.values["pipeline/gpu_items"], 1)
        self.assertIn("pipeline/csv_close_seconds", spider.crawler.stats.values)


if __name__ == "__main__":
    unittest.main()
