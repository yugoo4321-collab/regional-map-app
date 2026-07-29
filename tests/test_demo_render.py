from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"


class DemoRenderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = APP_PATH.read_text(encoding="utf-8")
        self.tree = ast.parse(self.text)

    def test_simple_demo_marker_exists_once(self) -> None:
        self.assertEqual(
            self.text.count("SIMPLE_DEMO_GUIDE_V1"),
            1,
        )

    def test_demo_tab_exists_once(self) -> None:
        labels: list[str] = []

        for node in self.tree.body:
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

            candidate = [
                item.value
                for item in labels_node.elts
                if isinstance(item, ast.Constant)
                and isinstance(item.value, str)
            ]

            if "データ" in candidate and any(
                label in {"地図", "地図とプロフィール"}
                for label in candidate
            ):
                labels = candidate
                break

        self.assertEqual(labels.count("デモ"), 1)

    def test_demo_has_visible_guide_content(self) -> None:
        self.assertIn(
            'st.subheader("3分で見る使い方")',
            self.text,
        )
        self.assertIn(
            "おすすめの順番：地図 → 区レポート → 年齢 → 調査",
            self.text,
        )

    def test_demo_guide_is_inside_demo_tab(self) -> None:
        matches = 0

        for node in ast.walk(self.tree):
            if not isinstance(node, ast.With):
                continue

            context_names = {
                item.id
                for item in ast.walk(node.items[0].context_expr)
                if isinstance(item, ast.Name)
            }
            if "demo_tab" not in context_names:
                continue

            source = ast.get_source_segment(
                self.text,
                node,
            ) or ""
            if "3分で見る使い方" in source:
                matches += 1

        self.assertEqual(matches, 1)


if __name__ == "__main__":
    unittest.main()
