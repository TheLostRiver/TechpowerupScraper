import unittest
from pathlib import Path


class ReadmeDocsTests(unittest.TestCase):
    def test_english_readme_documents_profiles_and_diagnostics(self):
        readme = Path("README.md").read_text(encoding="utf-8")

        self.assertIn("## Performance Profiles", readme)
        self.assertIn("python run.py --format json --profile safe", readme)
        self.assertIn("python run.py --format json --profile balanced", readme)
        self.assertIn("## Crawl Diagnostics", readme)
        self.assertIn("LOG_FILE=logs/crawl.log", readme)
        self.assertIn("## Failed URL Recovery", readme)
        self.assertIn("python run.py --retry-failed failed_urls.txt", readme)

    def test_chinese_readme_documents_profiles_and_diagnostics(self):
        readme = Path("README.zh-CN.md").read_text(encoding="utf-8")

        self.assertIn("## 性能档位", readme)
        self.assertIn("python run.py --format json --profile safe", readme)
        self.assertIn("python run.py --format json --profile balanced", readme)
        self.assertIn("## 爬虫诊断日志", readme)
        self.assertIn("LOG_FILE=logs/crawl.log", readme)
        self.assertIn("## 失败 URL 恢复", readme)
        self.assertIn("python run.py --retry-failed failed_urls.txt", readme)


if __name__ == "__main__":
    unittest.main()
