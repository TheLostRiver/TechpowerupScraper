import io
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import run


class RunProfileTests(unittest.TestCase):
    def test_profiles_are_declared(self):
        self.assertIn("safe", run.PROFILES)
        self.assertIn("balanced", run.PROFILES)
        self.assertIn("fast-cache", run.PROFILES)
        self.assertEqual(run.PROFILES["balanced"]["CONCURRENT_REQUESTS"], "4")

    def test_invalid_profile_exits_before_scrapy_execute(self):
        def fail_execute():
            raise AssertionError("scrapy.cmdline.execute should not be called")

        with patch.object(sys, "argv", ["run.py", "--profile", "invalid"]):
            with patch.object(run.scrapy.cmdline, "execute", fail_execute):
                with self.assertRaises(SystemExit) as exc:
                    with redirect_stdout(io.StringIO()) as stdout:
                        run.main()

        self.assertEqual(exc.exception.code, 1)
        self.assertIn("unsupported profile 'invalid'", stdout.getvalue())

    def test_balanced_profile_adds_scrapy_settings(self):
        captured = {}

        def fake_execute():
            captured["argv"] = list(sys.argv)

        with patch.object(sys, "argv", ["run.py", "--format", "json", "--profile", "balanced"]):
            with patch.object(run, "load_cookie_from_file", lambda: ""):
                with patch.object(run.scrapy.cmdline, "execute", fake_execute):
                    run.main()

        self.assertIn("OUTPUT_FORMAT=json", captured["argv"])
        self.assertIn("CONCURRENT_REQUESTS=4", captured["argv"])
        self.assertIn("CONCURRENT_REQUESTS_PER_DOMAIN=4", captured["argv"])
        self.assertIn("DOWNLOAD_DELAY=1", captured["argv"])
        self.assertIn("AUTOTHROTTLE_TARGET_CONCURRENCY=2.0", captured["argv"])


if __name__ == "__main__":
    unittest.main()
