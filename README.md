# TechPowerUp Scraper

**Language:** English | [简体中文](README.zh-CN.md)

A Scrapy-based crawler for collecting CPU and GPU specification tables from [TechPowerUp](https://www.techpowerup.com/). The project can export separate CPU and GPU datasets as CSV or JSON.

## Features

- Scrapes TechPowerUp CPU and GPU list pages.
- Exports CPU and GPU data into separate files.
- Supports CSV and JSON output through `run.py --format`.
- Supports browser cookie reuse for TechPowerUp bot-check pages.
- Uses Scrapy HTTP cache to avoid repeating successful downloads.

## Installation

```powershell
pip install scrapy itemadapter
```

Optional, only needed when using `get_cookie.py --extract`:

```powershell
pip install browser_cookie3
```

## Usage

Run with the default CSV output:

```powershell
python run.py
```

Run with JSON output:

```powershell
python run.py --format json
```

Pass a browser cookie manually:

```powershell
python run.py --format json --cookie "your_cookie_string"
```

Or save a browser cookie to `cookies.json` first:

```powershell
python get_cookie.py
python get_cookie.py --extract
python run.py --format json
```

`cookies.json` is ignored by git because it may contain sensitive session data.

## Output Files

CSV mode writes:

- `cpus.csv`
- `gpus.csv`

JSON mode writes:

- `cpus.json`
- `gpus.json`

Generated output files are ignored by git.

## CPU Dataset

The CPU dataset contains:

- **Name**: CPU model name.
- **Codename**: CPU architecture or product codename.
- **Cores**: Core count.
- **Clock**: Base clock speed.
- **Socket**: Compatible socket.
- **Process**: Manufacturing node.
- **L3 Cache**: L3 cache size.
- **TDP**: Thermal design power.
- **Released**: Release date.

## GPU Dataset

The GPU dataset contains:

- **Product_Name**: GPU product name.
- **GPU_Chip**: GPU chip name.
- **Released**: Release date.
- **Bus**: Bus interface.
- **Memory**: Memory capacity.
- **GPU_clock**: GPU clock speed.
- **Memory_clock**: Memory clock speed.
- **Shaders_TMUs_ROPs**: Shader, TMU, and ROP counts.

## Notes

TechPowerUp may show a bot-check page. If the crawler receives blocked responses, complete the verification in a browser, extract the cookie with `get_cookie.py --extract`, then run the crawler again.

The original dataset snapshot from January 10, 2023 is available on [Kaggle](https://www.kaggle.com/datasets/baraazaid/cpu-and-gpu-stats).
