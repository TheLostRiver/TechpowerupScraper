"""
Cookie 获取工具

用法：
  python get_cookie.py           打开 Chrome，完成验证后提取 Cookie
  python get_cookie.py --extract 仅提取 Chrome 中已有的 Cookie
"""

import json
import sys
import webbrowser
from pathlib import Path

COOKIE_FILE = Path(__file__).parent / "cookies.json"
DOMAIN = ".techpowerup.com"


def extract_cookies():
    """Extract TechPowerUp cookies from Chrome."""
    try:
        import browser_cookie3
    except ImportError:
        print("Error: browser_cookie3 not installed. Run: pip install browser_cookie3")
        return []

    try:
        cj = browser_cookie3.chrome(domain_name=DOMAIN)
        cookies = []
        for cookie in cj:
            cookies.append({
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain,
                "path": cookie.path,
            })
        return cookies
    except Exception as e:
        print(f"Error reading Chrome cookies: {e}")
        return []


def save_cookies(cookies):
    cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "cookies": cookies,
            "cookie_string": cookie_str,
        }, f, indent=2, ensure_ascii=False)
    return cookie_str


def main():
    extract_only = "--extract" in sys.argv

    print("=" * 50)
    print("TechPowerUp Cookie Getter")
    print("=" * 50)

    if not extract_only:
        print()
        print("Opening Chrome...")
        webbrowser.open("https://www.techpowerup.com/gpu-specs/")
        print()
        print("Please complete the drag captcha in Chrome,")
        print("then run again:")
        print(f"  python {sys.argv[0]} --extract")
        return

    # Extract mode
    print("\nExtracting cookies from Chrome...")
    cookies = extract_cookies()

    if not cookies:
        print("No TechPowerUp cookies found.")
        print("Make sure you completed the captcha in Chrome first.")
        return

    cookie_str = save_cookies(cookies)

    print(f"\nCookie saved to: {COOKIE_FILE}")
    print(f"Cookie count: {len(cookies)}")
    print(f"\nCookies found:")
    for c in cookies:
        val = c['value']
        print(f"  {c['name']} = {val[:60]}{'...' if len(val) > 60 else ''}")
    print(f"\nNow run:")
    print(f"  python run.py --format json")


if __name__ == "__main__":
    main()
