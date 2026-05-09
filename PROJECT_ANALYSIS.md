# TechPowerUp Scraper 项目分析报告

> 分析日期：2026-05-02

---

## 一、项目概述

这是一个基于 **Scrapy** 框架的 Web 爬虫项目，用于从 [TechPowerUp](https://www.techpowerup.com) 硬件规格数据库中抓取 **GPU（显卡）** 和 **CPU（处理器）** 的详细技术参数。

- **原作者**：BaraaZ95
- **许可证**：MIT License（2023）
- **原始用途**：机器学习、硬件对比研究（数据快照曾发布在 Kaggle，截至 2023-01-10）

---

## 二、项目结构

```
Techpowerup-scraper-main/
├── scrapy.cfg                      # Scrapy 项目配置（指向 techpowerup.settings）
├── LICENSE                         # MIT 许可证
├── README.md                       # 项目文档及数据集字段说明
├── .gitignore                      # 标准 Python gitignore（含 .scrapy）
├── .scrapy/httpcache/tpu/          # HTTP 缓存目录（上次爬取的缓存）
└── techpowerup/
    ├── __init__.py                 # 空包初始化文件
    ├── items.py                    # Item 模型定义（未使用，spider 直接 yield dict）
    ├── middlewares.py              # 默认 Scrapy 中间件（模板代码，未自定义）
    ├── pipelines.py               # 核心输出逻辑 — 写入 cpus.csv 和 gpus.csv
    ├── settings.py                # 核心配置 — 限速、UA、缓存、AutoThrottle
    └── spiders/
        └── tpu.py                 # Spider 主体 — URL 生成、HTML 解析、错误处理
```

---

## 三、技术栈与依赖

| 组件 | 说明 |
|------|------|
| Python | 3.10+（从 .pyc 文件推断） |
| Scrapy | Web 爬虫框架（核心依赖） |
| itemadapter | 用于 item 适配（import 但实际未深度使用） |
| csv | Python 标准库，用于输出 CSV 文件 |

**安装依赖：**

```bash
pip install scrapy itemadapter
```

> 注意：项目缺少 `requirements.txt`，需手动安装依赖。

---

## 四、运行方式

```bash
cd Q:\Tools\Techpowerup-scraper-main
scrapy crawl tpu
```

**执行流程：**

1. Spider 根据年份（1998-2023）× 过滤条件（分辨率/核心数）生成所有 URL
2. 逐个请求 URL，解析 HTML 表格中的硬件规格数据
3. 通过 Pipeline 将结果写入 `cpus.csv` 和 `gpus.csv`

---

## 五、输出数据格式

### 5.1 CPU 数据（cpus.csv）

| 字段 | 说明 |
|------|------|
| Name | 处理器名称 |
| Codename | 代号 |
| Cores | 核心数 |
| Clock | 时钟频率 |
| Socket | 插槽类型 |
| Process | 制程工艺 |
| L3 Cache | 三级缓存 |
| TDP | 热设计功耗 |
| Released | 发布时间 |

### 5.2 GPU 数据（gpus.csv）

| 字段 | 说明 |
|------|------|
| Product_Name | 产品名称 |
| GPU_Chip | GPU 芯片型号 |
| Released | 发布时间 |
| Bus | 总线接口 |
| Memory | 显存 |
| GPU_clock | GPU 时钟频率 |
| Memory_clock | 显存时钟频率 |
| Shaders_TMUs_ROPs | 着色器/纹理单元/光栅单元 |

---

## 六、配置参数详解

### 6.1 settings.py 配置

| 参数 | 值 | 说明 |
|------|-----|------|
| `BOT_NAME` | `'techpowerup'` | Scrapy 机器人名称 |
| `ROBOTSTXT_OBEY` | `True` | 遵守 robots.txt |
| `CONCURRENT_REQUESTS` | `1` | 单并发请求（非常保守） |
| `DOWNLOAD_DELAY` | `5`（秒） | 请求间隔 5 秒（代码注释：越慢越好，网站有限速） |
| `AUTOTHROTTLE_ENABLED` | `True` | 启用自适应限速（根据服务器响应动态调整延迟） |
| `HTTPCACHE_ENABLED` | `True` | 启用文件系统级 HTTP 缓存（支持断点续爬） |
| `DEFAULT_REQUEST_HEADERS` | Chrome 108 UA | 伪装为 Windows 10 上的 Chrome 108 浏览器 |

### 6.2 Spider 内部参数（tpu.py）

| 参数 | 值 | 说明 |
|------|-----|------|
| `years` | `range(1998, 2024)` | 爬取 1998-2023 年的硬件 |
| `resolutions` | `[0, 1, 480, 720, 1080, 768, 900, 1440, 2160]` | GPU 分辨率过滤器（9 个） |
| `Cores` | `[1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 16, ... 84, 9]` | CPU 核心数过滤器（31 个） |

**URL 总量估算：**
- GPU：26 年 × 9 分辨率 = **234 个 URL**
- CPU：26 年 × 31 核心数 = **806 个 URL**
- 合计约 **1,040 个 URL**

每个 URL 对应一个 TechPowerUp 搜索结果页（最多 100 条/页），通过不同过滤条件绕过分页限制。

---

## 七、反爬策略分析

| 策略 | 实现方式 | 效果评估 |
|------|----------|----------|
| 单并发请求 | `CONCURRENT_REQUESTS = 1` | 有效降低服务器压力 |
| 请求延迟 | `DOWNLOAD_DELAY = 5` | 每次请求间隔 5 秒 |
| 自适应限速 | `AUTOTHROTTLE_ENABLED = True` | 服务器响应慢时自动增加延迟 |
| HTTP 缓存 | `HTTPCACHE_ENABLED = True` | 已抓取的 URL 不会重复请求 |
| UA 伪装 | 设置 Chrome 108 User-Agent | 避免被识别为爬虫 |
| 遵守 robots.txt | `ROBOTSTXT_OBEY = True` | 合规性保障 |
| 429 状态码处理 | `handle_httpstatus_list = [404, 429]` | 仅记录，**不自动重试** |

---

## 八、已知问题与风险

### 8.1 严重 Bug：Pipeline 路由错误

**问题描述：**

`spiders/tpu.py` 的 `parse()` 方法 yield 的是 `(HW_dict, response)` 元组（第 55 行），但 `pipelines.py` 的 `process_item` 通过 `spider.response.url` 判断数据属于 CPU 还是 GPU。

**影响：**

`spider.response` 只会保存最后一个 response，而非当前 item 对应的 response。这意味着大量数据可能被路由到错误的 CSV 文件中。

**修复方案：**

在 yield item 时将 URL 信息一并传入，例如：

```python
# 在 parse() 中
hw_dict['source_url'] = response.url
yield hw_dict
```

然后在 pipeline 中通过 `item['source_url']` 判断类型。

### 8.2 无自动重试机制

**问题描述：**

遇到 HTTP 429（请求过多）或 404 时，URL 仅被记录到 `self.failed_urls`，不会重新排队。

**影响：**

大批量抓取时会丢失数据，尤其是被限速的请求。

**修复方案：**

使用 Scrapy 内置的重试中间件，或在 spider 中实现自定义重试逻辑：

```python
# 在 settings.py 中
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]
```

### 8.3 年份范围过时

**问题描述：**

`years = range(1998, 2024)` 硬编码到 2023 年，缺少 2024-2026 年的数据。

**修复方案：**

```python
from datetime import datetime
years = range(1998, datetime.now().year + 1)
```

### 8.4 Cores 列表异常

**问题描述：**

`Cores` 列表末尾的 `9` 看起来是乱序的，可能是笔误或有意为之的边界值。

### 8.5 未使用 Item 模型

**问题描述：**

`items.py` 定义了 `TechpowerupItem` 类，但 spider 直接 yield 原始 dict，Item 模型完全未使用。

---

## 九、用于个人 Web 项目的建议

### 9.1 必须修复

1. **修复 Pipeline 路由 Bug** — 确保 CPU/GPU 数据正确分类
2. **添加自动重试** — 避免因 429 限速丢失数据
3. **更新年份范围** — 覆盖 2024-2026 年数据

### 9.2 推荐改进

| 改进项 | 说明 |
|--------|------|
| 输出格式 | 将 CSV 改为 JSON 或直接写入数据库（如 SQLite/PostgreSQL），更方便 Web 项目使用 |
| 数据清洗 | 添加字段验证和清洗逻辑，确保数据质量 |
| 增量抓取 | 记录已抓取的 URL，支持增量更新而非全量重爬 |
| 日志完善 | 添加更详细的抓取进度日志，便于监控大批量任务 |
| 导出 API | 如果 Web 项目需要，可以添加数据导出接口 |

### 9.3 数据库适配示例

如果要将数据直接写入 SQLite，可修改 `pipelines.py`：

```python
import sqlite3

class DatabasePipeline:
    def open_spider(self, spider):
        self.conn = sqlite3.connect('hardware.db')
        self.cursor = self.conn.cursor()
        # 创建表
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS cpus (
            name TEXT, codename TEXT, cores TEXT, clock TEXT,
            socket TEXT, process TEXT, l3_cache TEXT, tdp TEXT, released TEXT
        )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS gpus (
            product_name TEXT, gpu_chip TEXT, released TEXT, bus TEXT,
            memory TEXT, gpu_clock TEXT, memory_clock TEXT, shaders_tmus_rops TEXT
        )''')

    def process_item(self, item, spider):
        url = item.get('source_url', '')
        if 'cpu' in url:
            self.cursor.execute('INSERT INTO cpus VALUES (?,?,?,?,?,?,?,?,?)',
                (item.get('Name'), item.get('Codename'), item.get('Cores'),
                 item.get('Clock'), item.get('Socket'), item.get('Process'),
                 item.get('L3 Cache'), item.get('TDP'), item.get('Released')))
        elif 'gpu' in url:
            self.cursor.execute('INSERT INTO gpus VALUES (?,?,?,?,?,?,?,?)',
                (item.get('Product_Name'), item.get('GPU_Chip'), item.get('Released'),
                 item.get('Bus'), item.get('Memory'), item.get('GPU_clock'),
                 item.get('Memory_clock'), item.get('Shaders_TMUs_ROPs')))
        self.conn.commit()
        return item

    def close_spider(self, spider):
        self.conn.close()
```

---

## 十、总结

| 维度 | 评估 |
|------|------|
| 功能完整性 | 基本可用，但存在 Pipeline 路由 Bug |
| 反爬策略 | 较为保守合理，但缺少自动重试 |
| 代码质量 | 中等，有未使用的代码和潜在 Bug |
| 可维护性 | 一般，缺少 requirements.txt 和文档 |
| 适用性 | 需修复后才能用于大批量数据抓取 |

**整体评价：** 项目框架合理，思路正确，但直接用于生产环境前需要修复 Pipeline 路由 Bug 和添加重试机制。修复后可以稳定抓取约 1,000+ 页的硬件规格数据，适合作为个人 Web 项目的数据源。
