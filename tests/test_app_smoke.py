from __future__ import annotations

import os
import time
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"


class AppSmokeTest(unittest.TestCase):
    def test_app_starts_without_streamlit_exception(self) -> None:
        previous = Path.cwd()
        started = time.perf_counter()
        app = None

        try:
            os.chdir(ROOT)
            app = AppTest.from_file(APP_PATH, default_timeout=90)
            app.run()
        finally:
            os.chdir(previous)

        assert app is not None
        elapsed = time.perf_counter() - started
        exceptions = [str(item.value) for item in app.exception]

        self.assertEqual(
            exceptions,
            [],
            "Streamlit実行時の例外: " + " / ".join(exceptions),
        )
        self.assertGreaterEqual(len(app.tabs), 5)
        self.assertLess(elapsed, 90)


if __name__ == "__main__":
    unittest.main()
