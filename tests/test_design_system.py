from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"
CSS_PATH = ROOT / "assets" / "app.css"
THEME_PATH = ROOT / "ui_theme.py"


def relative_luminance(hex_color: str) -> float:
    value = hex_color.lstrip("#")
    channels = [
        int(value[index:index + 2], 16) / 255
        for index in (0, 2, 4)
    ]

    linear = [
        channel / 12.92
        if channel <= 0.04045
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return (
        0.2126 * linear[0]
        + 0.7152 * linear[1]
        + 0.0722 * linear[2]
    )


def contrast_ratio(first: str, second: str) -> float:
    first_luminance = relative_luminance(first)
    second_luminance = relative_luminance(second)
    lighter = max(first_luminance, second_luminance)
    darker = min(first_luminance, second_luminance)
    return (lighter + 0.05) / (darker + 0.05)


class DesignSystemTest(unittest.TestCase):
    def test_theme_files_exist(self) -> None:
        self.assertTrue(CSS_PATH.exists())
        self.assertTrue(THEME_PATH.exists())

    def test_app_loads_external_theme_once(self) -> None:
        text = APP_PATH.read_text(encoding="utf-8")
        self.assertEqual(text.count("load_app_styles()"), 1)
        self.assertIn(
            "from ui_theme import load_app_styles",
            text,
        )

    def test_no_top_level_inline_style_blocks(self) -> None:
        tree = ast.parse(APP_PATH.read_text(encoding="utf-8"))
        violations: list[int] = []

        for node in tree.body:
            if not isinstance(node, ast.Expr):
                continue
            call = node.value
            if not isinstance(call, ast.Call) or not call.args:
                continue
            argument = call.args[0]
            if (
                isinstance(argument, ast.Constant)
                and isinstance(argument.value, str)
                and "<style>" in argument.value
            ):
                violations.append(node.lineno)

        self.assertEqual(
            violations,
            [],
            f"app.pyにトップレベルのstyleブロックが残っています: {violations}",
        )

    def test_accessibility_rules_exist(self) -> None:
        css = CSS_PATH.read_text(encoding="utf-8")
        for rule in [
            ":focus-visible",
            "prefers-reduced-motion",
            "forced-colors",
            'overflow-x: auto',
        ]:
            self.assertIn(rule, css)

    def test_core_color_contrast(self) -> None:
        pairs = [
            ("#152235", "#FFFFFF"),
            ("#3F4D5F", "#FFFFFF"),
            ("#FFFFFF", "#315F7B"),
            ("#536276", "#FFFFFF"),
        ]
        for foreground, background in pairs:
            with self.subTest(
                foreground=foreground,
                background=background,
            ):
                self.assertGreaterEqual(
                    contrast_ratio(foreground, background),
                    4.5,
                )

    def test_css_does_not_contain_font_files(self) -> None:
        css = CSS_PATH.read_text(encoding="utf-8")
        self.assertIsNone(
            re.search(r"url\([^)]*\.(woff2?|ttf|otf)", css, re.I)
        )


if __name__ == "__main__":
    unittest.main()
