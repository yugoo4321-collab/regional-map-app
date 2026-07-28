from __future__ import annotations

import unittest

import numpy as np

from investigation_board_tab import (
    LENSES,
    build_board_frame,
    load_board_data,
    median_index_data,
    report_markdown,
    spread_table,
)


class InvestigationBoardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        current, history, factors, age = load_board_data()
        cls.frame = build_board_frame(
            current,
            history,
            factors,
            age,
        )
        cls.wards = ["杉並区", "豊島区", "江東区"]
        cls.metrics = LENSES["全体"]["metrics"]

    def test_board_frame_has_23_wards(self) -> None:
        self.assertEqual(len(self.frame), 23)
        self.assertEqual(
            self.frame["自治体"].nunique(),
            23,
        )
        self.assertTrue(
            self.frame[self.metrics].notna().all().all()
        )

    def test_index_data_has_all_pairs(self) -> None:
        result = median_index_data(
            self.frame,
            self.wards,
            self.metrics,
        )
        self.assertEqual(
            len(result),
            len(self.wards) * len(self.metrics),
        )
        self.assertTrue(
            np.isfinite(result["指数"]).all()
        )

    def test_spread_table_is_sorted(self) -> None:
        result = spread_table(
            self.frame,
            self.wards,
            self.metrics,
        )
        self.assertEqual(len(result), len(self.metrics))
        self.assertTrue(
            result["広がり"].is_monotonic_decreasing
        )

    def test_report_contains_wards_and_note(self) -> None:
        report = report_markdown(
            self.frame,
            self.wards,
            "全体",
            self.metrics,
            "次に住宅費を見る。",
        )
        for ward in self.wards:
            self.assertIn(ward, report)
        self.assertIn("次に住宅費を見る。", report)
        self.assertIn("| 自治体 |", report)


if __name__ == "__main__":
    unittest.main()
