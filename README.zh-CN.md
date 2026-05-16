# TechPowerUp 爬虫

**语言：** [English](README.md) | 简体中文

这是一个基于 [Scrapy](https://scrapy.org/) 的 TechPowerUp 爬虫，用于从 [TechPowerUp](https://www.techpowerup.com/) 抓取 CPU 和 GPU 规格列表，并分别导出 CPU/GPU 数据集。当前项目支持 CSV 和 JSON 两种输出格式。

## 功能

- 抓取 TechPowerUp 的 CPU 和 GPU 规格列表页。
- 将 CPU 与 GPU 数据分别写入独立文件。
- 通过 `run.py --format` 切换 CSV 或 JSON 输出。
- 支持复用浏览器 Cookie，用于通过 TechPowerUp 的 bot-check 页面。
- 使用 Scrapy HTTP cache，避免重复下载已经成功抓取过的页面。

## 安装依赖

```powershell
pip install scrapy itemadapter
```

如果需要使用 `get_cookie.py --extract` 从 Chrome 提取 Cookie，还需要安装：

```powershell
pip install browser_cookie3
```

## 使用方法

默认导出 CSV：

```powershell
python run.py
```

导出 JSON：

```powershell
python run.py --format json
```

手动传入浏览器 Cookie：

```powershell
python run.py --format json --cookie "your_cookie_string"
```

也可以先保存浏览器 Cookie 到 `cookies.json`：

```powershell
python get_cookie.py
python get_cookie.py --extract
python run.py --format json
```

`cookies.json` 可能包含敏感登录/会话信息，已被 `.gitignore` 忽略，不应提交到仓库。

## 性能档位

可以使用 `run.py --profile` 选择可重复的爬取速度：

- `safe`：单请求、5 秒延迟，适合首次运行、排查 bot-check 或封禁问题。
- `balanced`：中等并发、1 秒延迟，适合 Cookie 有效后的常规爬取。
- `fast-cache`：高并发、极低延迟，主要用于已有缓存或低风险的本地基准测试。

示例：

```powershell
python run.py --format json --profile safe
python run.py --format json --profile balanced
python run.py --format json --profile fast-cache
```

也可以在 profile 后继续传入 Scrapy 设置。后面的设置可以覆盖 profile 的默认值：

```powershell
python run.py --format json --profile balanced -s CLOSESPIDER_PAGECOUNT=1
```

## 爬虫诊断日志

每次运行会记录：

- 生成的初始 URL 数量
- Cookie 是否存在，但不会打印 Cookie 内容
- 每个响应的 URL、状态码、耗时、缓存标记和解析出的 item 数量
- 最终状态码分布、缓存命中、总 item 数、CPU/GPU item 数和失败 URL 数
- JSON 或 CSV 输出写入耗时

保存日志到文件：

```powershell
python run.py --format json --profile balanced -s LOG_FILE=logs/crawl.log
```

## 失败 URL 恢复

失败 URL 会写入 `failed_urls.txt`。可以只重跑这些 URL：

```powershell
python run.py --retry-failed failed_urls.txt
```

重跑时也可以继续组合常规输出格式和性能档位：

```powershell
python run.py --format json --profile safe --retry-failed failed_urls.txt
```

HTTP 429 响应会交给 Scrapy retry，并在服务端返回 `Retry-After` 时先等待；等待时间会受 `TPU_RETRY_AFTER_MAX_DELAY` 限制。

## 输出文件

CSV 模式会生成：

- `cpus.csv`
- `gpus.csv`

JSON 模式会生成：

- `cpus.json`
- `gpus.json`

这些输出文件已被 `.gitignore` 忽略。

## CPU 数据字段

CPU 数据集包含以下字段：

- **Name**：CPU 型号名称。
- **Codename**：架构或产品代号。
- **Cores**：核心数量。
- **Clock**：基础频率。
- **Socket**：插槽类型。
- **Process**：制造工艺。
- **L3 Cache**：三级缓存容量。
- **TDP**：热设计功耗。
- **Released**：发布日期。

## GPU 数据字段

GPU 数据集包含以下字段：

- **Product_Name**：GPU 产品名称。
- **GPU_Chip**：GPU 芯片名称。
- **Released**：发布日期。
- **Bus**：总线接口。
- **Memory**：显存容量。
- **GPU_clock**：GPU 频率。
- **Memory_clock**：显存频率。
- **Shaders_TMUs_ROPs**：着色器、纹理单元和光栅单元数量。

## Bot-check 与 Cookie

TechPowerUp 可能会显示 bot-check 页面。如果爬虫返回被拦截的响应，可以先在浏览器中手动完成验证，然后运行：

```powershell
python get_cookie.py --extract
```

之后再次运行爬虫：

```powershell
python run.py --format json
```

Cookie 通常有有效期。如果 Cookie 过期，需要重新在浏览器中验证并提取。

## 说明

原始项目的数据快照曾在 2023 年 1 月 10 日发布到 [Kaggle](https://www.kaggle.com/datasets/baraazaid/cpu-and-gpu-stats)。当前仓库中的代码已经增加了 JSON 输出、Cookie 复用和命令行入口等改造。
