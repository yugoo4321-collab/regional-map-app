from __future__ import annotations

import unittest
from pathlib import Path

from age_structure_tab import (
    build_age_summary,
    comparison_data,
    load_age_data,
    report_markdown,
    top_differences,
)


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "tokyo_age_structure_2026.csv"


class AgeComparisonTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load_age_data(str(DATA_PATH))
        cls.summary = build_age_summary(cls.data)
        cls.first = "杉並区"
        cls.second = "豊島区"

    def test_age_share_difference_sums_to_zero(self) -> None:
        comparison = comparison_data(
            self.data,
            self.first,
            self.second,
        )
        self.assertAlmostEqual(
            float(comparison["差"].sum()),
            0.0,
            places=6,
        )

    def test_top_differences_returns_three_rows(self) -> None:
        rows = top_differences(
            self.data,
            self.first,
            self.second,
        )
        self.assertEqual(len(rows), 3)
        self.assertTrue((rows["差の絶対値"] > 0).all())

    def test_report_contains_both_wards(self) -> None:
        report = report_markdown(
            self.data,
            self.summary,
            self.first,
            self.second,
        )
        self.assertIn(self.first, report)
        self.assertIn(self.second, report)
        self.assertIn("差が大きい年齢階級", report)


if __name__ == "__main__":
    unittest.main()
