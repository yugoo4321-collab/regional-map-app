from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"

EXPECTED_LABELS = [
    "地図",
    "区レポート",
    "デモ",
    "2区比較",
    "調査",
    "構造",
    "年齢",
    "特徴",
    "要因",
    "推移",
    "プロジェクト",
    "データ",
]


def main_tab_labels() -> list[str]:
    tree = ast.parse(APP_PATH.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.Call):
            continue
        function = node.value.func
        if not (
            isinstance(function, ast.Attribute)
            and isinstance(function.value, ast.Name)
            and function.value.id == "st"
            and function.attr == "tabs"
            and node.value.args
        ):
            continue
        labels_node = node.value.args[0]
        if not isinstance(labels_node, (ast.List, ast.Tuple)):
            continue
        labels = [
            item.value
            for item in labels_node.elts
            if isinstance(item, ast.Constant)
            and isinstance(item.value, str)
        ]
        if "区レポート" in labels and "データ" in labels:
            return labels
    raise AssertionError("メインタブが見つかりません")


class CompactNavigationTest(unittest.TestCase):
    def test_labels_are_unique(self) -> None:
        labels = main_tab_labels()
        self.assertEqual(len(labels), len(set(labels)))

    def test_compact_labels_exist(self) -> None:
        labels = main_tab_labels()
        for label in EXPECTED_LABELS:
            self.assertIn(label, labels)

    def test_long_old_labels_are_removed(self) -> None:
        labels = main_tab_labels()
        for old_label in [
            "地図とプロフィール",
            "3分デモ",
            "調査ボード",
            "構造分析",
            "年齢構成",
            "特徴分析",
            "要因分析",
            "経年変化",
        ]:
            self.assertNotIn(old_label, labels)

    def test_navigation_style_exists(self) -> None:
        text = APP_PATH.read_text(encoding="utf-8")
        self.assertIn("COMPACT_NAVIGATION_V1", text)


if __name__ == "__main__":
    unittest.main()
