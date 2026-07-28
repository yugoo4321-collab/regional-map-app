from __future__ import annotations

import py_compile
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {".git", ".venv", "backup", "__pycache__", ".logs"}


def run(arguments: list[str], label: str) -> float:
    print(f"\n=== {label} ===")
    started = time.perf_counter()
    subprocess.run(arguments, cwd=ROOT, check=True, text=True)
    elapsed = time.perf_counter() - started
    print(f"{label}: OK ({elapsed:.2f}秒)")
    return elapsed


def compile_project() -> float:
    print("\n=== Python構文 ===")
    started = time.perf_counter()
    files = []

    for path in ROOT.rglob("*.py"):
        if set(path.relative_to(ROOT).parts) & EXCLUDED:
            continue
        py_compile.compile(str(path), doraise=True)
        files.append(path)

    elapsed = time.perf_counter() - started
    print(f"Python構文: OK ({len(files)}ファイル / {elapsed:.2f}秒)")
    return elapsed


def main() -> None:
    timings = {
        "依存関係": run(
            [sys.executable, "-m", "pip", "check"],
            "依存関係",
        ),
        "Python構文": compile_project(),
    }

    validator = ROOT / "validate_project.py"
    if validator.exists():
        timings["データ検証"] = run(
            [sys.executable, str(validator)],
            "データ検証",
        )

    timings["自動テスト"] = run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-v",
        ],
        "自動テスト",
    )

    print("\n==============================")
    print("品質ゲート: PASS")
    print(f"合計: {sum(timings.values()):.2f}秒")
    for label, seconds in timings.items():
        print(f"- {label}: {seconds:.2f}秒")
    print("==============================")


if __name__ == "__main__":
    main()
