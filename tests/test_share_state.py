from __future__ import annotations

import unittest

from share_state import build_share_url, normalize_tab, tab_slug


class ShareStateTest(unittest.TestCase):
    def test_tab_aliases(self) -> None:
        self.assertEqual(normalize_tab("demo"), "3分デモ")
        self.assertEqual(normalize_tab("history"), "経年変化")
        self.assertEqual(normalize_tab("要因分析"), "要因分析")
        self.assertIsNone(normalize_tab("unknown"))

    def test_tab_slug(self) -> None:
        self.assertEqual(tab_slug("3分デモ"), "demo")
        self.assertEqual(tab_slug("プロジェクト"), "project")

    def test_build_url(self) -> None:
        url = build_share_url(
            "https://example.streamlit.app/",
            tab="3分デモ",
            ward="杉並区",
        )
        self.assertTrue(url.startswith("https://example.streamlit.app/?"))
        self.assertIn("tab=demo", url)
        self.assertIn(
            "ward=%E6%9D%89%E4%B8%A6%E5%8C%BA",
            url,
        )

    def test_overview_ward_is_omitted(self) -> None:
        url = build_share_url(
            "https://example.streamlit.app",
            tab="map",
            ward="23区全体",
        )
        self.assertEqual(
            url,
            "https://example.streamlit.app/?tab=map",
        )


if __name__ == "__main__":
    unittest.main()
