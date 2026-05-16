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

## 2026-05-09 基准结果

- safe profile 小样本命令：`python run.py --format json --profile safe -s CLOSESPIDER_PAGECOUNT=1`
  - Cookie：从 `cookies.json` 自动加载。
  - 初始 URL：6。
  - 实际解析页面：1。
  - 状态码：`{200: 1}`。
  - cache 命中：1。
  - item：GPU 41，CPU 0。
  - JSON 写入耗时：约 0.002 秒。
  - 结果：`crawl_start`、`response`、`pipeline_json_written`、`crawl_summary` 均正常出现。
- balanced profile 当前 URL 集命令：`python run.py --format json --profile balanced`
  - Cookie：从 `cookies.json` 自动加载。
  - 初始 URL：6。
  - 状态码：`{200: 6}`。
  - cache 命中：6。
  - item：GPU 123，CPU 282，总计 405。
  - JSON 写入耗时：约 0.005 秒。
  - 失败 URL：0。
  - 输出校验：`python -m json.tool cpus.json` 和 `python -m json.tool gpus.json` 通过。
- 观察：
  - 当前 6 个列表页在 cache 命中情况下小于 1 秒完成，不是慢点。
  - JSON 写入耗时毫秒级，不是当前瓶颈。
  - 如果用户实际遇到“数千条跑数小时”，更可能来自历史全量 URL、详情页 URL、未命中 cache、AutoThrottle/固定 delay 或 bot-check。
  - Scrapy 2.15.2 提示 `start_requests()` 和 pipeline 方法签名存在 deprecation warning，后续可作为兼容性清理任务。

## 详情页/分页抓取决策

- 当前实现只抓取 2024-2026 的 CPU/GPU 年份列表页，不进入详情页。
- 当前 balanced 基准总计 405 条 item；如果目标是数千条数据，当前 URL 范围明显不够。
- CPU 2024 和 CPU 2025 均解析到 100 条，疑似命中 TechPowerUp 列表页单页上限，需要确认是否存在分页、过滤条件拆分或详情页补抓。
- 本轮优化分支先完成可观测性、日志、性能档位和基础重试，不把详情页/分页抓取混入同一个改动。
- 下一轮建议单独写计划，覆盖：
  - 历史年份范围恢复或参数化。
  - 分页检测与调度。
  - 详情页 URL 提取、去重、并发上限。
  - 断点续爬和失败 URL 重跑。
  - 100、1000、全量三档 benchmark。

## 2026-05-16 阶段 4 缺口复核

- `techpowerup/spiders/tpu.py` 已能把失败响应记录到 metrics，并在关闭时写入 `FAILED_URLS_FILE`。
- `techpowerup/settings.py` 已启用 Scrapy retry，并覆盖 408、429、500、502、503、504；403/410 不在重试码中，符合“默认只记录”的计划约束。
- 当前仍缺少“失败 URL 可以单独重跑”的入口；README 也写明当前只是记录失败，后续再加 `--retry-failed`。
- 当前没有针对 429 `Retry-After` 或较长退避的自有测试/中间件；需要用最小 downloader middleware 在重试前记录并阻塞一个可配置的短等待，实际默认可保守一些，测试中用 0 秒避免拖慢。

## 2026-05-16 阶段 4 实现结果

- `run.py --retry-failed failed_urls.txt` 会转成 Scrapy spider 参数 `-a retry_failed_file=failed_urls.txt`。
- `TpuSpider` 在提供 `retry_failed_file` 时只从该文件读取非空、非注释、去重后的 URL 作为起始请求；默认模式仍生成当前 CPU/GPU 年份列表页。
- 新增 `RetryAfterMiddleware`，仅对 429 响应生效，读取 `Retry-After` 秒数或 HTTP 日期，按 `TPU_RETRY_AFTER_MAX_DELAY` 封顶后再把响应交给 Scrapy retry middleware。
- README 英文/中文已改为实际的失败 URL 重跑命令，并说明 429 会按 `Retry-After` 保守等待。
