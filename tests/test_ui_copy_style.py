from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

UI_FILES = [
    ROOT / "app.py",
    ROOT / "guided_demo_tab.py",
    ROOT / "population_factors_tab.py",
    ROOT / "project_portfolio_tab.py",
]

BANNED_PHRASES = [
    "を追跡",
    "確認できます",
    "収録しています",
    "ことができます",
    "発見につながる",
    "分析体験",
    "このアプリの考え方",
]


class UiCopyStyleTest(unittest.TestCase):
    def test_ai_like_phrases_are_not_used(self) -> None:
        violations: list[str] = []

        for path in UI_FILES:
            if not path.exists():
                continue

            text = path.read_text(encoding="utf-8")
            for phrase in BANNED_PHRASES:
                if phrase in text:
                    violations.append(f"{path.name}: {phrase}")

        self.assertEqual(
            violations,
            [],
            "UI文言ガイドに合わない表現があります: "
            + ", ".join(violations),
        )


if __name__ == "__main__":
    unittest.main()
