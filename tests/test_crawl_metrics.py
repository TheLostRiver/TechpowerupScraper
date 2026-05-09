import unittest

from techpowerup.crawl_metrics import CrawlMetrics


class FakeClock:
    def __init__(self):
        self.value = 100.0

    def __call__(self):
        return self.value


class CrawlMetricsTests(unittest.TestCase):
    def test_records_responses_items_cache_and_failures(self):
        clock = FakeClock()
        metrics = CrawlMetrics(clock=clock)

        metrics.record_response(
            url="https://www.techpowerup.com/gpu-specs/?year=2026",
            status=200,
            elapsed=0.25,
            cached=True,
            item_count=42,
        )
        metrics.record_response(
            url="https://www.techpowerup.com/cpu-specs/?year=2026",
            status=429,
            elapsed=1.5,
            cached=False,
            item_count=0,
        )
        metrics.record_item("GPU")
        metrics.record_item("CPU")
        metrics.record_item("CPU")

        summary = metrics.summary()

        self.assertEqual(summary["response_count"], 2)
        self.assertEqual(summary["status_counts"], {200: 1, 429: 1})
        self.assertEqual(summary["cache_hits"], 1)
        self.assertEqual(
            summary["failed_urls"],
            ["https://www.techpowerup.com/cpu-specs/?year=2026"],
        )
        self.assertEqual(summary["parsed_items"], 42)
        self.assertEqual(summary["item_counts"], {"GPU": 1, "CPU": 2})

    def test_elapsed_total_uses_injected_clock(self):
        clock = FakeClock()
        metrics = CrawlMetrics(clock=clock)
        clock.value = 112.5

        summary = metrics.summary()

        self.assertEqual(summary["elapsed_seconds"], 12.5)


if __name__ == "__main__":
    unittest.main()
