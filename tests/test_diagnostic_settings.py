import unittest
from pathlib import Path

import techpowerup.settings as settings


class DiagnosticSettingsTests(unittest.TestCase):
    def test_retry_timeout_and_log_settings_are_configured(self):
        self.assertEqual(settings.DOWNLOAD_TIMEOUT, 30)
        self.assertTrue(settings.RETRY_ENABLED)
        self.assertEqual(settings.RETRY_TIMES, 2)
        self.assertEqual(settings.FAILED_URLS_FILE, "failed_urls.txt")
        self.assertEqual(settings.LOG_LEVEL, "INFO")
        self.assertIn(408, settings.RETRY_HTTP_CODES)
        self.assertIn(429, settings.RETRY_HTTP_CODES)
        self.assertIn(500, settings.RETRY_HTTP_CODES)

    def test_generated_diagnostics_are_ignored_by_git(self):
        gitignore = Path(".gitignore").read_text(encoding="utf-8")

        self.assertIn("logs/", gitignore)
        self.assertIn("failed_urls*.txt", gitignore)


if __name__ == "__main__":
    unittest.main()
