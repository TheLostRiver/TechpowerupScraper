import json
import sys
from pathlib import Path

import scrapy.cmdline

COOKIE_FILE = Path(__file__).parent / "cookies.json"


def load_cookie_from_file():
    if COOKIE_FILE.exists():
        with open(COOKIE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("cookie_string", "")
    return ""


def main():
    format = 'csv'
    cookie = ''
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
    cmd += args

    sys.argv = cmd
    scrapy.cmdline.execute()


if __name__ == '__main__':
    main()
