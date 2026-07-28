from __future__ import annotations

import unittest
from pathlib import Path

from age_structure_tab import build_age_summary, load_age_data


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "tokyo_age_structure_2026.csv"


class AgeStructureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load_age_data(str(DATA_PATH))
        cls.summary = build_age_summary(cls.data)

    def test_all_wards_exist(self) -> None:
        self.assertEqual(self.data["自治体"].nunique(), 23)
        self.assertEqual(self.summary["自治体"].nunique(), 23)

    def test_age_bands_are_complete(self) -> None:
        counts = self.data.groupby("自治体")["年齢階級"].nunique()
        self.assertEqual(counts.nunique(), 1)
        self.assertGreaterEqual(int(counts.min()), 20)

    def test_sex_and_nationality_totals(self) -> None:
        sex_error = (
            self.data["男"] + self.data["女"] - self.data["総数"]
        ).abs()
        nationality_error = (
            self.data["日本人"] + self.data["外国人"] - self.data["総数"]
        ).abs()
        self.assertTrue((sex_error <= 2).all())
        self.assertTrue((nationality_error <= 2).all())

    def test_three_age_shares_sum_to_100(self) -> None:
        total = (
            self.summary["0–14歳割合"]
            + self.summary["15–64歳割合"]
            + self.summary["65歳以上割合"]
        )
        self.assertTrue(((total - 100).abs() < 0.01).all())


if __name__ == "__main__":
    unittest.main()
