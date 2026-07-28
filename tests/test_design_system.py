from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"
CSS_PATH = ROOT / "assets" / "app.css"
THEME_PATH = ROOT / "ui_theme.py"


class DesignSystemTest(unittest.TestCase):
    def test_theme_files_exist(self) -> None:
        self.assertTrue(CSS_PATH.exists())
        self.assertTrue(THEME_PATH.exists())

    def test_app_loads_theme_once(self) -> None:
        text = APP_PATH.read_text(encoding="utf-8")
        self.assertIn("from ui_theme import load_app_styles", text)
        self.assertEqual(text.count("load_app_styles()"), 1)

    def test_accessibility_rules_exist(self) -> None:
        css = CSS_PATH.read_text(encoding="utf-8")
        for rule in [
            ":focus-visible",
            "prefers-reduced-motion",
            "forced-colors",
            "overflow-x: auto",
        ]:
            self.assertIn(rule, css)


if __name__ == "__main__":
    unittest.main()
