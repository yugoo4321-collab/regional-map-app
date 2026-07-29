from __future__ import annotations

import ast
import unittest
from pathlib import Path

from guided_demo_tab import load_demo_inputs_from_files


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"
DEMO_PATH = ROOT / "guided_demo_tab.py"


def main_tabs(tree: ast.Module) -> tuple[list[str], list[str]]:
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
        target = node.targets[0] if node.targets else None

        if not isinstance(labels_node, (ast.List, ast.Tuple)):
            continue
        if not isinstance(target, (ast.List, ast.Tuple)):
            continue

        labels = [
            item.value
            for item in labels_node.elts
            if isinstance(item, ast.Constant)
            and isinstance(item.value, str)
        ]
        variables = [
            item.id
            for item in target.elts
            if isinstance(item, ast.Name)
        ]

        if (
            len(labels) == len(variables)
            and "データ" in labels
            and ("地図" in labels or "地図とプロフィール" in labels)
        ):
            return labels, variables

    raise AssertionError("メインタブ定義が見つかりません")


def call_name(call: ast.Call) -> str:
    function = call.func
    if isinstance(function, ast.Name):
        return function.id
    if isinstance(function, ast.Attribute):
        return function.attr
    return ""


class DemoRenderTest(unittest.TestCase):
    def test_demo_inputs_load(self) -> None:
        current_data, history = load_demo_inputs_from_files()
        self.assertEqual(current_data["自治体"].nunique(), 23)
        self.assertEqual(history["自治体"].nunique(), 23)

    def test_demo_tab_is_connected_once(self) -> None:
        text = APP_PATH.read_text(encoding="utf-8")
        tree = ast.parse(text)
        labels, variables = main_tabs(tree)

        self.assertEqual(labels.count("デモ"), 1)
        demo_variable = variables[labels.index("デモ")]

        matches = 0
        for node in tree.body:
            if not isinstance(node, ast.With):
                continue

            context_names = {
                item.id
                for item in ast.walk(node.items[0].context_expr)
                if isinstance(item, ast.Name)
            }
            if demo_variable not in context_names:
                continue

            names = {
                call_name(item)
                for item in ast.walk(node)
                if isinstance(item, ast.Call)
            }
            if "render_demo_tab_from_files" in names:
                matches += 1

        self.assertEqual(matches, 1)

    def test_no_argumentless_original_call(self) -> None:
        text = APP_PATH.read_text(encoding="utf-8")
        tree = ast.parse(text)

        bad_calls = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if (
                call_name(node) == "render_demo_tab"
                and not node.args
                and not node.keywords
            ):
                bad_calls.append(node)

        self.assertEqual(bad_calls, [])

    def test_markers_exist(self) -> None:
        self.assertEqual(
            APP_PATH.read_text(encoding="utf-8").count(
                "DEMO_RENDER_FROM_FILES_V1"
            ),
            1,
        )
        self.assertEqual(
            DEMO_PATH.read_text(encoding="utf-8").count(
                "DEMO_FILE_ENTRYPOINT_V1"
            ),
            1,
        )


if __name__ == "__main__":
    unittest.main()
