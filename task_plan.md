# TechPowerUp 爬虫性能优化计划

## 目标

把当前爬虫从“少量轻量 JSON 数据也可能跑数小时”的状态，优化为可观测、可调参、可恢复的 Scrapy 爬虫。优化前先补齐诊断日志和基准数据，避免盲目提高并发导致 403/429 或数据缺失。

## 当前约束

- 不删除或修改本项目之外的任何文件。
- 不提交 `cookies.json`、输出 JSON、Scrapy 缓存、本地 agent/plugin 缓存。
- 先规划和诊断，再改实现。
- 优先使用 Scrapy 现有能力，而不是重写成独立 requests/aiohttp 爬虫。

## 阶段 1：建立性能基线

状态：complete

要做：
- 记录一次当前配置下的真实运行指标。
- 指标包括请求数、状态码分布、cache 命中、item 数量、失败 URL、总耗时、每类页面解析数量。
- 确认慢点是在下载、限速等待、bot-check、解析、pipeline 写入，还是请求生成逻辑。

验收：
- 能回答“实际请求了多少 URL，每个 URL 平均耗时多少，失败在哪些状态码上”。

## 阶段 2：加入结构化爬虫日志

状态：complete

要做：
- 在 spider 启动时记录配置摘要：年份范围、目标 URL 数、输出格式、并发、delay、AutoThrottle、cache、cookie 是否存在。
- 在每个 response 处理时记录 URL、状态码、耗时、cache 命中标记、解析到的 item 数。
- 在关闭时输出汇总：总请求、成功、失败、403、429、500、CPU item、GPU item、失败 URL 列表。
- 日志要适合命令行查看，也要适合后续写入独立日志文件。

验收：
- 跑一次爬虫，不看源码也能判断瓶颈。

## 阶段 3：配置化性能档位

状态：complete

要做：
- 保留保守默认档，避免直接激进抓取。
- 增加可通过命令行覆盖的性能参数：并发、下载延迟、AutoThrottle 目标并发、重试次数、是否使用 HTTP cache。
- 在 `run.py` 中增加便捷参数或说明如何通过 `-s` 覆盖 Scrapy settings。

候选档位：
- safe：并发 1，delay 5s，适合首次绕过验证或排查封禁。
- balanced：并发 4，delay 1s，AutoThrottle target 2。
- fast-cache：用于已缓存或低风险测试，较高并发，低 delay。

验收：
- 同一份代码能用不同档位跑基准，不需要手改 `settings.py`。

## 阶段 4：请求调度与失败恢复

状态：complete

要做：
- 明确当前目标是年份列表页，还是还要进入详情页抓取数千条 item。
- 对失败 URL 增加可保存、可重跑的机制。
- 启用 Scrapy retry middleware，覆盖网络错误、408、429、5xx；403/410 默认只记录，不盲目重试。
- 尊重 `Retry-After` 或至少对 429 使用较长退避。

验收：
- 临时网络错误不会导致整批数据丢失。
- 失败 URL 可以单独重跑。

## 阶段 5：输出性能优化

状态：complete

要做：
- 评估 JSON 一次性 `json.dump(indent=2)` 对大数据量的影响。
- 如果数据量继续增长，考虑 JSONL 流式输出或减少 pretty indent。
- 保留现有 `cpus.json`/`gpus.json` 兼容输出。

验收：
- 写入耗时被日志量化；如果写入不是瓶颈，不做过度重构。

## 阶段 6：验证与回归

状态：complete

要做：
- 小样本：限制 1-2 个 URL，确认日志和解析正确。
- 中样本：当前年份范围全量跑一次，比较优化前后耗时。
- 失败场景：无 cookie、过期 cookie、403/429、cache 命中。
- 输出校验：CPU/GPU item 数量、字段完整性、JSON 可解析。

验收：
- 每个性能档位都有明确耗时、失败率、item 数量。
- 优化不牺牲数据完整性。

## 当前决策

- 先补观测能力，再调并发。
- 不直接把 `CONCURRENT_REQUESTS` 从 1 提到很高。
- 优先在 Scrapy 框架内优化。

## Errors Encountered

| Error | Attempt | Resolution |
|-------|---------|------------|
| `python -m unittest discover -v` ran 0 tests | Tried default unittest discovery as full regression evidence | Switched to the repository's explicit test module list and verified 16 tests pass |
