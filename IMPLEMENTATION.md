# 项目改造实现文档

> 日期：2026-05-02
> 目标：支持 JSON/CSV 双格式导出 + 修复已知 Bug

---

## 一、改造总览

| 任务 | 文件 | 状态 |
|------|------|------|
| Task 1：修复 spider yield 逻辑 | `techpowerup/spiders/tpu.py` | ✅ |
| Task 2：修复 pipeline 路由 + UTF-8 | `techpowerup/pipelines.py` | ✅ |
| Task 3：添加 OUTPUT_FORMAT 配置 | `techpowerup/settings.py` | ✅ |
| Task 4：重写 pipeline 支持 JSON | `techpowerup/pipelines.py` | ✅ |
| Task 5：创建命令行入口 | `run.py`（新建） | ✅ |
| Task 6：更新年份范围为动态 | `techpowerup/spiders/tpu.py` | ✅ |

---

## 二、各任务详细改动

### Task 1：修复 spider yield 逻辑

**文件**：`techpowerup/spiders/tpu.py`

**问题**：
- 原代码 `yield HW_dict, response` yield 了元组，pipeline 无法正确接收
- `HW['Type'] = 'GPU'` 在第 41/44 行设置，但第 52 行 `HW = dict(zip(...))` 创建了新 dict，导致 Type 字段丢失

**改动**：
```python
# 改动前
if "gpu" in response.url:
    columns = [...]
    HW['Type'] = 'GPU'
elif "cpu" in response.url:
    columns = [...]
    HW['Type'] = 'CPU'

rows = response.css('div[id="list"] > table > tr')
for row in rows:
    values = []
    for td in row.css('td'):
        info = td.css('a::text').get() or td.css('::text').get()
        values.append(info)
    HW = dict(zip(columns, values))
    total.append(HW)
for HW_dict in total:
    yield HW_dict, response  # Bug: yield 元组

# 改动后
hw_type = None
if "gpu" in response.url:
    columns = [...]
    hw_type = 'GPU'
elif "cpu" in response.url:
    columns = [...]
    hw_type = 'CPU'

rows = response.css('div[id="list"] > table > tr')
for row in rows:
    values = []
    for td in row.css('td'):
        info = td.css('a::text').get() or td.css('::text').get()
        values.append(info)
    HW = dict(zip(columns, values))
    HW['type'] = hw_type  # 在 dict 创建后添加 type
    yield HW  # 修复: yield 单个 dict
```

**要点**：
- 用变量 `hw_type` 暂存类型，避免被 `dict(zip(...))` 覆盖
- 每个 yield 的 dict 都包含 `type` 字段（`'CPU'` 或 `'GPU'`）
- yield 单个 dict 而非元组

---

### Task 2：修复 pipeline 路由 + UTF-8 编码

**文件**：`techpowerup/pipelines.py`

**问题**：
- `spider.response.url` 不存在，会抛出 `AttributeError`
- CSV 文件未指定编码，Windows 默认 cp1252 会导致非 ASCII 字符乱码
- 未指定 `newline=''`，Windows 下 CSV 会多出空行
- `process_item` 未 return item，阻断了后续 pipeline

**改动**：
```python
# 改动前
def __init__(self):
    self.cpu_file = open("cpus.csv", "w")
    self.gpu_file = open("gpus.csv", "w")
    ...

def process_item(self, item, spider):
    if "cpu" in spider.response.url:  # Bug: 属性不存在
        self.cpu_writer.writerow(item)
    elif "gpu" in spider.response.url:
        self.gpu_writer.writerow(item)
    # Bug: 没有 return item

# 改动后
def __init__(self):
    self.cpu_file = open("cpus.csv", "w", newline='', encoding='utf-8')
    self.gpu_file = open("gpus.csv", "w", newline='', encoding='utf-8')
    ...

def process_item(self, item, spider):
    row = {k: v for k, v in item.items() if k != 'type'}
    if item.get('type') == 'CPU':
        self.cpu_writer.writerow(row)
    elif item.get('type') == 'GPU':
        self.gpu_writer.writerow(row)
    return item
```

**要点**：
- 路由改为通过 `item.get('type')` 判断，不再依赖 response
- 添加 `encoding='utf-8'` 和 `newline=''`
- CSV 写入时排除 `type` 字段（它不是硬件规格数据）
- 末尾 `return item` 保持 pipeline 链畅通

---

### Task 3：添加 OUTPUT_FORMAT 配置

**文件**：`techpowerup/settings.py`

**改动**：
```python
# 在 SPIDER_MODULES 下方添加
OUTPUT_FORMAT = 'csv'  # 可选 'csv' 或 'json'
```

**要点**：
- 默认值为 `'csv'`，保持向后兼容
- 可通过 `scrapy crawl tpu -s OUTPUT_FORMAT=json` 或 `run.py --format json` 覆盖

---

### Task 4：重写 pipeline 支持 JSON 输出

**文件**：`techpowerup/pipelines.py`

**设计思路**：
- 将原有 Pipeline 拆分为 `CsvPipeline` 和 `JsonPipeline` 两个独立类
- 保留 `TechpowerupPipeline` 作为工厂类，通过 `from_crawler` 根据配置返回对应实例

**完整代码**：
```python
class CsvPipeline:
    """CSV 输出：边爬边写，内存占用低"""

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
    """JSON 输出：先收集到内存，爬完后一次性写入"""

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


class TechpowerupPipeline:
    """工厂类：根据 OUTPUT_FORMAT 设置选择 Pipeline"""

    @classmethod
    def from_crawler(cls, crawler):
        format = crawler.settings.get('OUTPUT_FORMAT', 'csv')
        if format == 'json':
            return JsonPipeline()
        return CsvPipeline()
```

**要点**：
- `TechpowerupPipeline.from_crawler` 是 Scrapy 的标准扩展点，会在启动时自动调用
- JSON 输出使用 `ensure_ascii=False` 保留中文等非 ASCII 字符
- 输出文件中不包含 `type` 字段（纯硬件规格数据）
- `settings.py` 中 `ITEM_PIPELINES` 仍指向 `TechpowerupPipeline`，无需改动

---

### Task 5：创建命令行入口 run.py

**文件**：`run.py`（新建）

**完整代码**：
```python
import sys
import scrapy.cmdline


def main():
    format = 'csv'
    args = sys.argv[1:]

    if '--format' in args:
        idx = args.index('--format')
        if idx + 1 < len(args):
            format = args[idx + 1]
            if format not in ('csv', 'json'):
                print(f"Error: unsupported format '{format}'. Use 'csv' or 'json'.")
                sys.exit(1)
            args.pop(idx)
            args.pop(idx)
        else:
            print("Error: --format requires a value (csv or json).")
            sys.exit(1)

    cmd = ['scrapy', 'crawl', 'tpu', '-s', f'OUTPUT_FORMAT={format}'] + args
    sys.argv = cmd
    scrapy.cmdline.execute()


if __name__ == '__main__':
    main()
```

**使用方式**：
```bash
# 默认 CSV 格式
python run.py

# 指定 JSON 格式
python run.py --format json

# 带 Cookie 运行（绕过 bot 检查）
python run.py --format json --cookie "your_cookie_here"

# 传递额外 scrapy 参数
python run.py --format json --loglevel INFO
```

---

### Task 6：更新年份范围为动态

**文件**：`techpowerup/spiders/tpu.py`

**改动**：
```python
# 改动前
years = range(1998, 2024)

# 改动后
from datetime import datetime
years = range(1998, datetime.now().year + 1)
```

**要点**：
- 自动包含当前年份，无需手动维护
- 2026 年运行时范围为 1998-2026

---

## 三、输出文件说明

### CSV 格式
- `cpus.csv` — CPU 规格数据（9 列）
- `gpus.csv` — GPU 规格数据（8 列）
- 编码：UTF-8
- 适合：Excel 打开、数据库导入、数据分析

### JSON 格式
- `cpus.json` — CPU 规格数据（JSON 数组）
- `gpus.json` — GPU 规格数据（JSON 数组）
- 编码：UTF-8，`indent=2` 格式化
- 适合：Web 项目直接使用、API 返回、NoSQL 数据库导入

---

## 四、修改文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `techpowerup/spiders/tpu.py` | 修改 | 修复 yield、添加 type 字段、动态年份 |
| `techpowerup/pipelines.py` | 重写 | 拆分为 CsvPipeline + JsonPipeline + 工厂类 |
| `techpowerup/settings.py` | 修改 | 添加 OUTPUT_FORMAT 配置项 |
| `run.py` | 新建 | 命令行入口，支持 --format 参数 |

---

## 五、Bot 检查绕过方案

### 问题

TechPowerUp 在 2023 年后部署了反爬虫防火墙，包含：
- JavaScript PoW（工作量证明）挑战
- 拖拽验证码（drag captcha）
- 即使 Playwright headless 浏览器也无法自动完成拖拽验证

### 解决方案：Cookie 复用

手动在浏览器中通过一次验证，提取 Cookie 给 Scrapy 使用。

**获取 Cookie 步骤**：
1. 用 Chrome 打开 `https://www.techpowerup.com/gpu-specs/`
2. 如果弹出 bot 检查，手动完成拖拽验证
3. 按 `F12` → `Network` 标签 → 刷新页面
4. 点击第一个请求 → `Request Headers` → 找到 `Cookie:` 行
5. 复制整个 Cookie 值

**使用方式**：
```bash
# 通过命令行参数
python run.py --format json --cookie "your_cookie_value_here"

# 或在 settings.py 中配置
BROWSER_COOKIE = 'your_cookie_value_here'
```

**注意事项**：
- Cookie 有效期通常为几小时到一天
- 过期后需要重新获取
- IP 变化可能导致 Cookie 失效

---

## 六、额外修复

### 6.1 缓存 gzip 解压

旧版 Scrapy 缓存的 response body 是 gzip 压缩的，新版未自动解压。

**修复**：在 `parse()` 中添加 gzip 检测和解压：
```python
body = response.body
if body[:2] == b'\x1f\x8b':
    body = gzip.decompress(body)
    response = HtmlResponse(url=response.url, body=body, encoding='utf-8')
```

### 6.2 缓存指纹迁移

Scrapy 2.15 的 `request_fingerprint` 算法与旧版不同，旧缓存无法命中。

**修复**：运行缓存迁移脚本（已在运行时执行过）：
```python
from scrapy.utils.request import fingerprint
from scrapy.http import Request
# 遍历缓存目录，用新指纹重命名
```

### 6.3 handle_httpstatus_list 扩展

添加 403 状态码处理，避免 HttpError 中间件忽略 403 响应。

---

## 七、验证方式

```bash
# 安装依赖
pip install scrapy itemadapter

# 带 Cookie 运行（CSV）
python run.py --format csv --cookie "your_cookie_here"

# 带 Cookie 运行（JSON）
python run.py --format json --cookie "your_cookie_here"

# 不带 Cookie 运行（仅使用缓存数据）
python run.py --format json
```
