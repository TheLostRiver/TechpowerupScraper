import json
import sys
from pathlib import Path

import scrapy.cmdline

COOKIE_FILE = Path(__file__).parent / "cookies.json"

# Performance profiles / 性能档位
# English/中文: defaults stay conservative; faster profiles are explicit opt-in.
# 中文/English：默认配置保持保守，更快的档位需要显式选择。
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


def load_cookie_from_file():
    if COOKIE_FILE.exists():
        with open(COOKIE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("cookie_string", "")
    return ""


def main():
    format = 'csv'
    cookie = ''
    profile = ''
    args = sys.argv[1:]

    # Parse --format
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

    # Parse --profile
    if '--profile' in args:
        idx = args.index('--profile')
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

    # Parse --cookie
    if '--cookie' in args:
        idx = args.index('--cookie')
        if idx + 1 < len(args):
            cookie = args[idx + 1]
            args.pop(idx)
            args.pop(idx)
        else:
            print("Error: --cookie requires a value (the browser cookie string).")
            sys.exit(1)

    # Auto-load cookie from file if not provided via --cookie
    if not cookie:
        cookie = load_cookie_from_file()
        if cookie:
            print(f"[auto] Loaded cookie from {COOKIE_FILE.name}")
        else:
            print("[warn] No cookie found. Run 'python get_cookie.py' first, or use --cookie flag.")
            print("       Without cookie, only cached data will be available.")

    # Build scrapy command
    cmd = ['scrapy', 'crawl', 'tpu', '-s', f'OUTPUT_FORMAT={format}']
    if cookie:
        cmd += ['-s', f'BROWSER_COOKIE={cookie}']
    if profile:
        print(f"[profile] Using {profile} profile")
        for key, value in PROFILES[profile].items():
            cmd += ['-s', f'{key}={value}']
    cmd += args

    sys.argv = cmd
    scrapy.cmdline.execute()


if __name__ == '__main__':
    main()
