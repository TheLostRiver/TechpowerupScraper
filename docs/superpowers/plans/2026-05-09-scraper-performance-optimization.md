# Scraper Performance Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add observability first, then make TechPowerUp crawling faster through safe, configurable Scrapy settings without losing data or triggering avoidable 403/429 responses.

**Architecture:** Keep Scrapy as the crawling framework. Add a small metrics module for timing and counters, integrate it into the spider and pipelines, expose safe performance profiles through `run.py`, and document benchmark commands. Defaults remain conservative; faster modes are opt-in.

**Tech Stack:** Python 3, Scrapy, standard-library `logging`, `time`, `collections`, `dataclasses`, `unittest`, JSON/CSV file output.

---

## File Structure

- Create: `techpowerup/crawl_metrics.py`
  - Pure Python metrics collector for elapsed time, status counts, cache hits, failed URLs, and item counts.
- Create: `tests/test_crawl_metrics.py`
  - Unit tests for the metrics collector without network access.
- Modify: `techpowerup/spiders/tpu.py`
  - Attach request start timestamps, record per-response metrics, log startup and close summaries, persist failed URLs.
- Modify: `techpowerup/pipelines.py`
  - Record CPU/GPU item counts and output write durations in Scrapy stats.
- Modify: `techpowerup/settings.py`
  - Add retry, timeout, logging, failed URL file, and conservative default observability settings.
- Modify: `run.py`
  - Add `--profile safe|balanced|fast-cache` for repeatable performance tuning.
- Modify: `.gitignore`
  - Ignore generated logs and failed URL output.
- Modify: `README.md`
  - Document profiles, logging, benchmark commands, and failure recovery.

---

### Task 1: Add A Pure Metrics Collector

**Files:**
- Create: `techpowerup/crawl_metrics.py`
- Create: `tests/test_crawl_metrics.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_crawl_metrics.py`:

```python
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
        self.assertEqual(summary["failed_urls"], ["https://www.techpowerup.com/cpu-specs/?year=2026"])
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
```

- [ ] **Step 2: Run tests and confirm they fail because the module is missing**

Run:

```powershell
python -m unittest tests.test_crawl_metrics -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'techpowerup.crawl_metrics'`.

- [ ] **Step 3: Implement the metrics collector**

Create `techpowerup/crawl_metrics.py`:

```python
from collections import Counter
from time import perf_counter


class CrawlMetrics:
    """Collects lightweight crawl metrics for logs and Scrapy stats."""

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
        self.response_count += 1
        self.status_counts[status] += 1
        self.total_response_seconds += elapsed
        self.parsed_items += item_count

        if cached:
            self.cache_hits += 1

        if status >= 400:
            self.failed_urls.append(url)

    def record_item(self, item_type):
        if item_type:
            self.item_counts[item_type] += 1

    def summary(self):
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
```

- [ ] **Step 4: Run tests and confirm they pass**

Run:

```powershell
python -m unittest tests.test_crawl_metrics -v
```

Expected: PASS, 2 tests.

- [ ] **Step 5: Commit**

```powershell
git add techpowerup/crawl_metrics.py tests/test_crawl_metrics.py
git commit -m "Add crawl metrics collector"
```

---

### Task 2: Integrate Metrics And Per-Response Logs Into The Spider

**Files:**
- Modify: `techpowerup/spiders/tpu.py`

- [ ] **Step 1: Add imports and initialize metrics**

Modify the top of `techpowerup/spiders/tpu.py`:

```python
from datetime import datetime
from pathlib import Path
from time import perf_counter

import scrapy
from scrapy import signals

from techpowerup.crawl_metrics import CrawlMetrics
```

Inside `__init__`, add:

```python
self.metrics = CrawlMetrics()
self.start_urls_count = 0
```

- [ ] **Step 2: Record request start timestamps**

In `start_requests`, replace the request yield with:

```python
urls = gpu_urls + cpu_urls
self.start_urls_count = len(urls)
self.logger.info(
    "crawl_start urls=%s years=%s-%s cookie_present=%s",
    self.start_urls_count,
    years.start,
    years.stop - 1,
    bool(self.cookie),
)

for url in urls:
    yield scrapy.Request(
        url,
        headers=headers,
        meta={"request_started_at": perf_counter()},
    )
```

- [ ] **Step 3: Count parsed items before yielding them**

In `parse`, replace the body after the status check with:

```python
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
    self.metrics.record_item(item.get("type"))
    yield item
```

- [ ] **Step 4: Record failed responses with elapsed time**

In the existing `if response.status in [403, 404, 429, 410, 500]:` block, record metrics before returning:

```python
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
```

- [ ] **Step 5: Persist failed URLs and log summary on close**

Replace `handle_spider_closed` with:

```python
def handle_spider_closed(self, reason):
    summary = self.metrics.summary()
    failed_urls = summary["failed_urls"]
    self.crawler.stats.set_value("failed_urls", ", ".join(failed_urls))
    self.crawler.stats.set_value("metrics/elapsed_seconds", summary["elapsed_seconds"])
    self.crawler.stats.set_value("metrics/response_count", summary["response_count"])
    self.crawler.stats.set_value("metrics/cache_hits", summary["cache_hits"])
    self.crawler.stats.set_value("metrics/parsed_items", summary["parsed_items"])

    failed_file = self.crawler.settings.get("FAILED_URLS_FILE", "failed_urls.txt")
    if failed_urls:
        Path(failed_file).write_text("\n".join(failed_urls) + "\n", encoding="utf-8")

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
```

- [ ] **Step 6: Run syntax check**

Run:

```powershell
python -m py_compile techpowerup\spiders\tpu.py techpowerup\crawl_metrics.py
```

Expected: no output and exit code 0.

- [ ] **Step 7: Commit**

```powershell
git add techpowerup/spiders/tpu.py
git commit -m "Add spider crawl metrics logging"
```

---

### Task 3: Add Pipeline Output Timing And Item Counters

**Files:**
- Modify: `techpowerup/pipelines.py`

- [ ] **Step 1: Add timing import**

At the top of `techpowerup/pipelines.py`, add:

```python
from time import perf_counter
```

- [ ] **Step 2: Count processed items in CSV and JSON pipelines**

In both `CsvPipeline.process_item` and `JsonPipeline.process_item`, add after routing:

```python
item_type = item.get("type")
if item_type:
    spider.crawler.stats.inc_value(f"pipeline/{item_type.lower()}_items")
```

- [ ] **Step 3: Time JSON writes**

Replace `JsonPipeline.close_spider` with:

```python
def close_spider(self, spider):
    started_at = perf_counter()
    with open("cpus.json", "w", encoding="utf-8") as f:
        json.dump(self.cpu_items, f, ensure_ascii=False, indent=2)
    with open("gpus.json", "w", encoding="utf-8") as f:
        json.dump(self.gpu_items, f, ensure_ascii=False, indent=2)
    elapsed = perf_counter() - started_at
    spider.crawler.stats.set_value("pipeline/json_write_seconds", round(elapsed, 3))
    spider.logger.info(
        "pipeline_json_written cpus=%s gpus=%s elapsed=%.3fs",
        len(self.cpu_items),
        len(self.gpu_items),
        elapsed,
    )
```

- [ ] **Step 4: Time CSV close flush**

In `CsvPipeline.close_spider`, wrap close calls:

```python
started_at = perf_counter()
self.cpu_file.close()
self.gpu_file.close()
elapsed = perf_counter() - started_at
spider.crawler.stats.set_value("pipeline/csv_close_seconds", round(elapsed, 3))
spider.logger.info("pipeline_csv_closed elapsed=%.3fs", elapsed)
```

- [ ] **Step 5: Run syntax check**

Run:

```powershell
python -m py_compile techpowerup\pipelines.py
```

Expected: no output and exit code 0.

- [ ] **Step 6: Commit**

```powershell
git add techpowerup/pipelines.py
git commit -m "Add pipeline output timing"
```

---

### Task 4: Add Conservative Retry, Timeout, And Log Settings

**Files:**
- Modify: `techpowerup/settings.py`
- Modify: `.gitignore`

- [ ] **Step 1: Add generated diagnostics ignores**

Append to `.gitignore`:

```gitignore
# Generated crawl diagnostics
logs/
failed_urls*.txt
```

- [ ] **Step 2: Add retry and timeout settings**

In `techpowerup/settings.py`, below `DOWNLOAD_DELAY`, add:

```python
DOWNLOAD_TIMEOUT = 30

RETRY_ENABLED = True
RETRY_TIMES = 2
RETRY_HTTP_CODES = [408, 429, 500, 502, 503, 504]
```

- [ ] **Step 3: Add default diagnostic output settings**

Near `OUTPUT_FORMAT`, add:

```python
FAILED_URLS_FILE = "failed_urls.txt"
LOG_LEVEL = "INFO"
```

- [ ] **Step 4: Keep 403 out of cache**

Confirm this existing setting remains unchanged:

```python
HTTPCACHE_IGNORE_HTTP_CODES = [403]
```

- [ ] **Step 5: Run syntax check**

Run:

```powershell
python -m py_compile techpowerup\settings.py
```

Expected: no output and exit code 0.

- [ ] **Step 6: Commit**

```powershell
git add .gitignore techpowerup/settings.py
git commit -m "Add crawl retry and diagnostic settings"
```

---

### Task 5: Add Performance Profiles To The CLI

**Files:**
- Modify: `run.py`

- [ ] **Step 1: Add profile definitions**

Below `COOKIE_FILE`, add:

```python
PROFILES = {
    "safe": {
        "CONCURRENT_REQUESTS": "1",
        "DOWNLOAD_DELAY": "5",
        "AUTOTHROTTLE_ENABLED": "True",
        "AUTOTHROTTLE_TARGET_CONCURRENCY": "1.0",
    },
    "balanced": {
        "CONCURRENT_REQUESTS": "4",
        "CONCURRENT_REQUESTS_PER_DOMAIN": "4",
        "DOWNLOAD_DELAY": "1",
        "AUTOTHROTTLE_ENABLED": "True",
        "AUTOTHROTTLE_TARGET_CONCURRENCY": "2.0",
    },
    "fast-cache": {
        "CONCURRENT_REQUESTS": "16",
        "CONCURRENT_REQUESTS_PER_DOMAIN": "16",
        "DOWNLOAD_DELAY": "0.1",
        "AUTOTHROTTLE_ENABLED": "False",
    },
}
```

- [ ] **Step 2: Parse `--profile`**

In `main`, initialize:

```python
profile = ""
```

After parsing `--format`, add:

```python
if "--profile" in args:
    idx = args.index("--profile")
    if idx + 1 < len(args):
        profile = args[idx + 1]
        if profile not in PROFILES:
            print(f"Error: unsupported profile '{profile}'. Use safe, balanced, or fast-cache.")
            sys.exit(1)
        args.pop(idx)
        args.pop(idx)
    else:
        print("Error: --profile requires a value (safe, balanced, or fast-cache).")
        sys.exit(1)
```

- [ ] **Step 3: Apply profile settings to the Scrapy command**

After building the base `cmd`, add:

```python
if profile:
    print(f"[profile] Using {profile} profile")
    for key, value in PROFILES[profile].items():
        cmd += ["-s", f"{key}={value}"]
```

- [ ] **Step 4: Run CLI validation**

Run:

```powershell
python run.py --profile invalid
```

Expected: exits with `Error: unsupported profile 'invalid'. Use safe, balanced, or fast-cache.`

- [ ] **Step 5: Run syntax check**

Run:

```powershell
python -m py_compile run.py
```

Expected: no output and exit code 0.

- [ ] **Step 6: Commit**

```powershell
git add run.py
git commit -m "Add crawl performance profiles"
```

---

### Task 6: Add Benchmark And Recovery Documentation

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add a performance profiles section**

Append to `README.md`:

````markdown
## Performance Profiles

Use `run.py --profile` to choose a repeatable crawl speed:

- `safe`: single request, 5 second delay, safest for first runs and bot-check troubleshooting.
- `balanced`: moderate concurrency and 1 second delay, recommended after cookies are valid.
- `fast-cache`: high concurrency and very low delay, intended for cached or low-risk local benchmark runs.

Examples:

```powershell
python run.py --format json --profile safe
python run.py --format json --profile balanced
python run.py --format json --profile fast-cache
```
````

- [ ] **Step 2: Add a logging section**

Append:

````markdown
## Crawl Diagnostics

Each run logs:

- generated start URL count
- cookie presence without printing the cookie value
- response URL, status, elapsed seconds, cache flag, and parsed item count
- final status distribution, cache hits, total items, CPU/GPU item counts, and failed URL count
- JSON or CSV output write duration

To save logs to a file:

```powershell
python run.py --format json --profile balanced -s LOG_FILE=logs/crawl.log
```
````

- [ ] **Step 3: Add failure recovery section**

Append:

````markdown
## Failed URL Recovery

Failed URLs are written to `failed_urls.txt`. The first optimization pass records failures only; a later pass can add a `--retry-failed` mode to rerun just those URLs.
````

- [ ] **Step 4: Commit**

```powershell
git add README.md
git commit -m "Document crawl performance diagnostics"
```

---

### Task 7: Run Baseline And Balanced Benchmarks

**Files:**
- No code changes.

- [ ] **Step 1: Run compile checks**

Run:

```powershell
python -m py_compile run.py get_cookie.py techpowerup\items.py techpowerup\middlewares.py techpowerup\pipelines.py techpowerup\settings.py techpowerup\spiders\tpu.py techpowerup\crawl_metrics.py
```

Expected: no output and exit code 0.

- [ ] **Step 2: Run unit tests**

Run:

```powershell
python -m unittest tests.test_crawl_metrics -v
```

Expected: PASS, 2 tests.

- [ ] **Step 3: Run safe profile with a small page cap**

Run:

```powershell
python run.py --format json --profile safe -s CLOSESPIDER_PAGECOUNT=1
```

Expected:
- command completes
- logs include `crawl_start`
- logs include at least one `response` or `response_failed`
- logs include `crawl_summary`

- [ ] **Step 4: Run balanced profile with current URL set**

Run:

```powershell
python run.py --format json --profile balanced
```

Expected:
- command completes
- `cpus.json` and `gpus.json` are valid JSON
- `crawl_summary` shows response count, cache hits, status counts, and item counts

- [ ] **Step 5: Validate JSON output**

Run:

```powershell
python -m json.tool cpus.json > $null
python -m json.tool gpus.json > $null
```

Expected: no output and exit code 0.

- [ ] **Step 6: Commit benchmark notes if README or planning docs are updated**

```powershell
git add task_plan.md findings.md progress.md README.md
git commit -m "Record crawl benchmark results"
```

---

### Task 8: Decide Whether To Add Detail-Page Crawling

**Files:**
- No immediate code changes unless the benchmark proves current list pages are not enough.

- [ ] **Step 1: Compare actual item counts with expected dataset needs**

Use `crawl_summary` and JSON lengths to decide whether current list pages provide all required fields.

- [ ] **Step 2: If details are required, write a separate implementation plan**

The detail-page crawler should be planned separately because it changes request volume from a handful of listing pages to thousands of item pages. That plan must include:

```text
- detail URL extraction
- request deduplication
- detail parse schema
- per-domain concurrency caps
- incremental resume
- failed detail URL retry
- benchmark targets for 100, 1000, and full runs
```

- [ ] **Step 3: Do not mix detail crawling into this observability pass**

Expected: this first optimization branch remains focused on logs, metrics, profiles, and safe retries.
