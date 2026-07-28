from __future__ import annotations

import unittest

from ward_brief_tab import (
    load_brief_data,
    merged_brief_frame,
    report_markdown,
    similarity_table,
    three_lines,
)


class WardBriefTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        current, history, factors, age = load_brief_data()
        cls.frame = merged_brief_frame(
            current,
            history,
            factors,
            age,
        )

    def test_merged_frame_has_23_wards(self) -> None:
        self.assertEqual(len(self.frame), 23)
        self.assertEqual(self.frame["自治体"].nunique(), 23)

    def test_similarity_excludes_target(self) -> None:
        similar = similarity_table(self.frame, "杉並区")
        self.assertEqual(len(similar), 22)
        self.assertNotIn("杉並区", similar["自治体"].tolist())
        self.assertTrue((similar["距離"] >= 0).all())

    def test_three_lines_are_filled(self) -> None:
        lines = three_lines(self.frame, "杉並区")
        self.assertEqual(len(lines), 3)
        self.assertTrue(all(line.strip() for line in lines))

    def test_report_contains_core_sections(self) -> None:
        report = report_markdown(self.frame, "杉並区")
        self.assertIn("杉並区 区レポート", report)
        self.assertIn("長期変化", report)
        self.assertIn("2025年の人口動態", report)
        self.assertIn("近い3区", report)


if __name__ == "__main__":
    unittest.main()
