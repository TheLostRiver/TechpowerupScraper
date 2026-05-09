# TechPowerUp 爬虫性能发现

## 代码现状

- `techpowerup/settings.py` 当前 `CONCURRENT_REQUESTS = 1`，全局单并发。
- `techpowerup/settings.py` 当前 `DOWNLOAD_DELAY = 5`，每次请求固定延迟 5 秒。
- `techpowerup/settings.py` 当前开启 `AUTOTHROTTLE_ENABLED = True`，可能进一步增加等待。
- `techpowerup/settings.py` 当前开启 `HTTPCACHE_ENABLED = True`，有利于重复运行，但需要日志显示 cache 命中情况。
- `techpowerup/spiders/tpu.py` 当前 `years = range(2024, datetime.now().year + 1)`，截至 2026-05-09 会生成 3 年的 GPU 年份页和 3 年的 CPU 年份页，共 6 个初始 URL。
- `techpowerup/spiders/tpu.py` 当前只解析列表页 item，没有进入每个硬件详情页。
- `techpowerup/pipelines.py` JSON pipeline 当前先收集到内存，关闭 spider 时一次性写 `cpus.json` 和 `gpus.json`，并使用 `indent=2`。

## 初步判断

- 如果只跑当前 6 个列表页，单并发和 5 秒 delay 的理论等待约 30 秒级，不应达到数小时。
- 如果实际运行数小时，可能原因包括：
  - 实际运行的代码路径和当前 `tpu.py` 不一致。
  - 请求大量详情页或历史过滤组合，但当前代码里没有体现。
  - 被 403/429/bot-check 阻断后反复等待或重试。
  - AutoThrottle 在高延迟响应下把间隔拉得很长。
  - 网络请求未命中缓存且站点响应极慢。
- JSON 写入对数千条轻量数据通常不是数小时瓶颈，但需要日志量化。

## 风险点

- 直接提高并发可能触发 429 或 bot-check。
- `COOKIES_ENABLED = False` 但通过手动 `Cookie` header 传 cookie；这可以工作，但需要日志确认 cookie 是否已注入。
- 失败 URL 当前只写入 Scrapy stats 的字符串，不利于重跑和排查。
- 没有结构化运行摘要，难以比较优化前后效果。

