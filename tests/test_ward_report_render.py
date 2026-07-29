from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"


def tab_variable_for_label(
    tree: ast.Module,
    label: str,
) -> str:
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

        if label in labels and len(labels) == len(variables):
            return variables[labels.index(label)]

    raise AssertionError(f"{label}のタブ変数が見つかりません")


def calls_render_ward_brief(node: ast.AST) -> bool:
    for item in ast.walk(node):
        if not isinstance(item, ast.Call):
            continue
        function = item.func
        if (
            isinstance(function, ast.Name)
            and function.id == "render_ward_brief_tab"
        ):
            return True
        if (
            isinstance(function, ast.Attribute)
            and function.attr == "render_ward_brief_tab"
        ):
            return True
    return False


class WardReportRenderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = APP_PATH.read_text(encoding="utf-8")
        self.tree = ast.parse(self.text)

    def test_ward_report_label_is_unique(self) -> None:
        label_count = 0
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
            if isinstance(labels_node, (ast.List, ast.Tuple)):
                label_count += sum(
                    1
                    for item in labels_node.elts
                    if isinstance(item, ast.Constant)
                    and item.value == "区レポート"
                )

        self.assertEqual(label_count, 1)

    def test_ward_report_renderer_is_connected_once(self) -> None:
        variable = tab_variable_for_label(
            self.tree,
            "区レポート",
        )
        matching_blocks = []

        for node in self.tree.body:
            if not isinstance(node, ast.With):
                continue
            if not calls_render_ward_brief(node):
                continue

            context_names = {
                item.id
                for item in ast.walk(node.items[0].context_expr)
                if isinstance(item, ast.Name)
            }
            if variable in context_names:
                matching_blocks.append(node)

        self.assertEqual(len(matching_blocks), 1)

    def test_renderer_import_exists(self) -> None:
        imports = []
        for node in self.tree.body:
            if not isinstance(node, ast.ImportFrom):
                continue
            for alias in node.names:
                imports.append(alias.name)

        self.assertIn("render_ward_brief_tab", imports)

    def test_render_marker_exists(self) -> None:
        self.assertIn("WARD_BRIEF_RENDER_V2", self.text)


if __name__ == "__main__":
    unittest.main()
