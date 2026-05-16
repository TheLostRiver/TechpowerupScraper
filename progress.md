# TechPowerUp 爬虫性能优化进度

## 2026-05-09

- 已确认仓库已初始化并推送到 `origin/main`。
- 已读取 `settings.py`、`tpu.py`、`pipelines.py`。
- 已确认当前没有既有 `task_plan.md`、`findings.md`、`progress.md`。
- 已创建性能优化规划文件。
- 当前阶段：建立性能基线和日志设计。
- 已新增原子任务实现计划：`docs/superpowers/plans/2026-05-09-scraper-performance-optimization.md`。
- 已在 `codex/scraper-performance-observability` 分支开始实现。
- Task 1 完成：新增 `techpowerup/crawl_metrics.py` 和 `tests/test_crawl_metrics.py`，使用 TDD 验证 RED/GREEN。
- 验证：`python -m unittest tests.test_crawl_metrics -v` 通过 2 个测试；`python -m py_compile techpowerup\crawl_metrics.py tests\test_crawl_metrics.py` 通过。
- Task 2 完成：`TpuSpider` 接入 `CrawlMetrics`，新增启动日志、响应日志、失败响应日志、关闭汇总和失败 URL 文件写入。
- 验证：`python -m unittest tests.test_crawl_metrics tests.test_tpu_spider_metrics -v` 通过 3 个测试；`python -m py_compile techpowerup\spiders\tpu.py techpowerup\crawl_metrics.py tests\test_tpu_spider_metrics.py` 通过。
- Task 3 完成：`CsvPipeline` 和 `JsonPipeline` 写入 `pipeline/*_items` 计数，并记录 CSV 关闭耗时与 JSON 写入耗时。
- 验证：`python -m unittest tests.test_crawl_metrics tests.test_tpu_spider_metrics tests.test_pipelines_metrics -v` 通过 5 个测试；`python -m py_compile techpowerup\pipelines.py tests\test_pipelines_metrics.py` 通过。
- Task 4 完成：新增 `DOWNLOAD_TIMEOUT`、`RETRY_*`、`FAILED_URLS_FILE`、`LOG_LEVEL`，并忽略 `logs/` 与 `failed_urls*.txt`。
- 验证：`python -m unittest tests.test_crawl_metrics tests.test_tpu_spider_metrics tests.test_pipelines_metrics tests.test_diagnostic_settings -v` 通过 7 个测试；`python -m py_compile techpowerup\settings.py tests\test_diagnostic_settings.py` 通过。
- Task 5 完成：`run.py` 新增 `--profile safe|balanced|fast-cache`，并把 profile settings 注入 Scrapy 命令。
- 验证：`python -m unittest tests.test_crawl_metrics tests.test_tpu_spider_metrics tests.test_pipelines_metrics tests.test_diagnostic_settings tests.test_run_profiles -v` 通过 10 个测试；`python -m py_compile run.py tests\test_run_profiles.py` 通过。
- Task 6 完成：英文和中文 README 增加性能档位、爬虫诊断日志和失败 URL 恢复说明。
- 验证：`python -m unittest tests.test_crawl_metrics tests.test_tpu_spider_metrics tests.test_pipelines_metrics tests.test_diagnostic_settings tests.test_run_profiles tests.test_readme_docs -v` 通过 12 个测试；README 链接与代码块结构检查通过。
- Task 7 完成：运行 safe 小样本和 balanced 当前 URL 集基准。
- safe 小样本：1 个列表页，GPU 41，cache hit 1，失败 0，JSON 写入约 0.002 秒。
- balanced 当前 URL 集：6 个列表页，GPU 123，CPU 282，总计 405，cache hit 6，失败 0，JSON 写入约 0.005 秒。
- JSON 校验：`python -m json.tool cpus.json` 和 `python -m json.tool gpus.json` 通过；输出文件保持 git ignored。
- 发现：Scrapy 2.15.2 输出 `start_requests()` 与 pipeline 方法签名 deprecation warning，建议后续单独清理。
- Task 8 完成：根据 405 条列表页 item 和 CPU 年份页 100 条上限迹象，决定详情页/分页抓取另开计划，不混入本轮观测优化分支。

## 2026-05-13

- 应用户要求运行 2024 至 2026-05-13 当前 CPU/GPU 列表页抓取；创建项目内 `.venv` 并安装 Scrapy 2.15.2。
- 命令：`.\\.venv\\Scripts\\python.exe run.py --format json --profile safe -s HTTPCACHE_ENABLED=False -s LOG_FILE=logs\\crawl_2026-05-13_2024_to_current_safe.log -s FAILED_URLS_FILE=logs\\failed_urls_2026-05-13_2024_to_current.txt`
- 结果：6 个初始 URL 全部 200，cache hit 0，失败 0；GPU 125，CPU 282，总计 407。
- 分页/年份页明细：GPU 2024=41、2025=67、2026=17；CPU 2024=100、2025=100、2026=82。
- JSON 校验：`.\\.venv\\Scripts\\python.exe -m json.tool cpus.json` 与 `.\\.venv\\Scripts\\python.exe -m json.tool gpus.json` 通过。
- 备注：当前 spider 抓取 TechPowerUp 年份列表页，不按具体发布日期过滤；2026 年份页可能包含 `Unreleased` 或仅标为 `2026` 的条目。
- Stop hook 复核：已读取 `task_plan.md`；阶段 4 与阶段 6 仍是 broader optimization 的 `in_progress` 状态，本次用户要求的实际抓取和 JSON 校验已完成。

### Auto Record: 2026-05-13 21:26:06
- Tool: apply_patch
- Files:
  - `D:\Tools\Techpowerup-scraper-main\progress.md` (update)

### Auto Record: 2026-05-13 21:27:50
- Tool: apply_patch
- Files:
  - `D:\Tools\Techpowerup-scraper-main\progress.md` (update)

## 2026-05-16

- 应用户要求检查 git 状态并推送未推送提交。
- 推送前状态：`main...origin/main [ahead 8]`，工作区另有未提交的 `progress.md` 修改和未跟踪 `.codex/` 目录。
- 已执行：`git -c safe.directory=D:/Tools/Techpowerup-scraper-main push origin main`。
- 推送结果：`main` 从 `88092da` 更新到 `e0b88a1`，8 个既有提交已推送到 `origin/main`。
- 推送后状态：`main...origin/main`，无未推送提交；仍有未提交的 `progress.md` 修改和未跟踪 `.codex/` 目录。
- Stop hook 要求续接 planning-with-files；尝试运行 `session-catchup.py` 的提权请求被安全审查拒绝，未执行该脚本，改为直接读取 `task_plan.md`、`findings.md`、`progress.md` 和 git 状态恢复上下文。
- 当前计划复核：阶段 1、2、3、5 为 complete；阶段 4（请求调度与失败恢复）和阶段 6（验证与回归）仍为 in_progress。
- 下一步：检查现有重试、失败 URL 保存/重跑、429 退避和相关测试覆盖，决定阶段 4 是否已有实现缺口。
- 使用 TDD 补齐阶段 4：先新增失败测试，确认 `--retry-failed` 未传入 spider、spider 未读取失败 URL 文件、`RetryAfterMiddleware` 不存在，然后实现最小代码使测试通过。
- 代码变更：`run.py` 新增 `--retry-failed <file>`；`TpuSpider` 新增 `retry_failed_file` 读取逻辑；`techpowerup/middlewares.py` 新增 429 `Retry-After` 退避中间件；`settings.py` 启用该中间件并新增退避配置。
- 文档变更：README 英文/中文失败 URL 恢复章节改为实际命令，并说明 429 `Retry-After` 行为。
- 新增/更新测试：`tests/test_retry_after_middleware.py`、`tests/test_run_profiles.py`、`tests/test_tpu_spider_metrics.py`、`tests/test_readme_docs.py`。
- 验证：`.\\.venv\\Scripts\\python.exe -m unittest tests.test_crawl_metrics tests.test_tpu_spider_metrics tests.test_pipelines_metrics tests.test_diagnostic_settings tests.test_run_profiles tests.test_readme_docs tests.test_retry_after_middleware -v` 通过 16 个测试。
- 验证：`.\\.venv\\Scripts\\python.exe -m py_compile run.py techpowerup\\spiders\\tpu.py techpowerup\\middlewares.py techpowerup\\settings.py tests\\test_run_profiles.py tests\\test_tpu_spider_metrics.py tests\\test_retry_after_middleware.py tests\\test_readme_docs.py` 通过。
- 注意：`.\\.venv\\Scripts\\python.exe -m unittest discover -v` 在当前仓库发现 0 个测试，不能作为回归证据；已记录到 `task_plan.md` 的 Errors Encountered。
- 阶段状态：阶段 4（请求调度与失败恢复）和阶段 6（验证与回归）已更新为 complete。

### Auto Record: 2026-05-16 21:20:39
- Tool: apply_patch
- Files:
  - `D:\Tools\Techpowerup-scraper-main\progress.md` (update)

### Auto Record: 2026-05-16 21:21:54
- Tool: apply_patch
- Files:
  - `D:\Tools\Techpowerup-scraper-main\findings.md` (update)

### Auto Record: 2026-05-16 21:22:35
- Tool: apply_patch
- Files:
  - `D:\Tools\Techpowerup-scraper-main\tests\test_run_profiles.py` (update)
  - `D:\Tools\Techpowerup-scraper-main\tests\test_tpu_spider_metrics.py` (update)
  - `D:\Tools\Techpowerup-scraper-main\tests\test_retry_after_middleware.py` (add)

### Auto Record: 2026-05-16 21:23:34
- Tool: apply_patch
- Files:
  - `D:\Tools\Techpowerup-scraper-main\run.py` (update)
  - `D:\Tools\Techpowerup-scraper-main\techpowerup\spiders\tpu.py` (update)
  - `D:\Tools\Techpowerup-scraper-main\techpowerup\middlewares.py` (update)
  - `D:\Tools\Techpowerup-scraper-main\techpowerup\settings.py` (update)

### Auto Record: 2026-05-16 21:24:28
- Tool: apply_patch
- Files:
  - `D:\Tools\Techpowerup-scraper-main\README.md` (update)
  - `D:\Tools\Techpowerup-scraper-main\README.zh-CN.md` (update)

### Auto Record: 2026-05-16 21:26:18
- Tool: apply_patch
- Files:
  - `D:\Tools\Techpowerup-scraper-main\task_plan.md` (update)
  - `D:\Tools\Techpowerup-scraper-main\findings.md` (update)

### Commit/Push Attempt: 2026-05-16

- 应用户要求将测试和相关改动提交并推送。
- 提交前验证已通过：`.\\.venv\\Scripts\\python.exe -m unittest tests.test_crawl_metrics tests.test_tpu_spider_metrics tests.test_pipelines_metrics tests.test_diagnostic_settings tests.test_run_profiles tests.test_readme_docs tests.test_retry_after_middleware -v` 通过 16 个测试。
- 编译检查已通过：`.\\.venv\\Scripts\\python.exe -m py_compile run.py techpowerup\\spiders\\tpu.py techpowerup\\middlewares.py techpowerup\\settings.py tests\\test_run_profiles.py tests\\test_tpu_spider_metrics.py tests\\test_retry_after_middleware.py tests\\test_readme_docs.py`。
- 已显式暂存代码、文档、计划记录和新增测试文件；`.codex/` 仍为未跟踪且未暂存。
- `git commit -m "Add failed URL retry recovery"` 失败，原因是当前环境未配置 `user.name` / `user.email`。
- 尝试使用最近提交作者信息作为临时 commit identity 的提权请求被安全审查拒绝；未创建提交，未推送。
- 当前阻塞：需要用户明确指定本次提交使用的 Git 作者身份，例如 `Name <email>`。

### Commit Identity Approval: 2026-05-16

- 用户已明确指定本次提交作者身份：`Helsincy <824618415@qq.com>`。
- 将使用单次 `git -c user.name=Helsincy -c user.email=824618415@qq.com commit ...` 创建提交，不修改全局 Git 配置。

### Auto Record: 2026-05-16 21:30:26
- Tool: apply_patch
- Files:
  - `D:\Tools\Techpowerup-scraper-main\progress.md` (update)

### Auto Record: 2026-05-16 21:35:08
- Tool: apply_patch
- Files:
  - `D:\Tools\Techpowerup-scraper-main\progress.md` (update)
