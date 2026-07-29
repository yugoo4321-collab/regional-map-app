from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_URL = "https://teeqy5f9waeoacgwccu4yc.streamlit.app"
REQUIRED_FILES = [
    "app.py",
    "README.md",
    "requirements.txt",
    "SUBMISSION_BRIEF.md",
    "PORTFOLIO_TALK_TRACK.md",
    "FINAL_CHECKLIST.md",
    "data/tokyo_wards.csv",
    "data/tokyo_wards_history.csv",
    "data/tokyo_population_factors_2025.csv",
    "data/tokyo_age_structure_2026.csv",
]


def run(arguments: list[str]) -> None:
    subprocess.run(
        arguments,
        cwd=ROOT,
        check=True,
        text=True,
    )


def check_files() -> None:
    missing = [
        item
        for item in REQUIRED_FILES
        if not (ROOT / item).exists()
    ]
    if missing:
        raise SystemExit(
            "不足ファイル: " + ", ".join(missing)
        )


def check_app_structure() -> None:
    text = (ROOT / "app.py").read_text(encoding="utf-8")
    tree = ast.parse(text)

    labels: list[str] = []
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
        if isinstance(labels_node, (ast.List, ast.Tuple)):
            candidate = [
                item.value
                for item in labels_node.elts
                if isinstance(item, ast.Constant)
                and isinstance(item.value, str)
            ]
            if "地図" in candidate and "データ" in candidate:
                labels = candidate
                break

    if not labels:
        raise SystemExit("メインタブを確認できません")
    if len(labels) != len(set(labels)):
        raise SystemExit("重複タブがあります")
    if labels.count("区レポート") != 1:
        raise SystemExit("区レポートが1個ではありません")


def check_readme() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if PUBLIC_URL not in readme:
        raise SystemExit("READMEに公開URLがありません")


def main() -> None:
    check_files()
    check_app_structure()
    check_readme()

    run([
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "tests",
        "-v",
    ])

    run(["git", "status", "--short"])

    print()
    print("最終監査: PASS")
    print("- 必須ファイル")
    print("- メインタブ")
    print("- 区レポート")
    print("- README公開URL")
    print("- 全自動テスト")
    print(PUBLIC_URL)


if __name__ == "__main__":
    main()
