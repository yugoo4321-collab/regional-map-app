from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from guided_demo_tab import (
    find_offset_ward,
    find_similar_population_pair,
    history_changes,
)


ROOT = Path(__file__).resolve().parents[1]


class GuidedDemoLogicTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.current = pd.read_csv(
            ROOT / "data" / "tokyo_wards.csv",
            dtype={"自治体コード": str},
        )
        cls.history = pd.read_csv(
            ROOT / "data" / "tokyo_wards_history.csv",
            dtype={"自治体コード": str},
        )
        cls.factors = pd.read_csv(
            ROOT / "data" / "tokyo_population_factors_2025.csv",
            dtype={"自治体コード": str},
        )

    def test_pair_is_two_distinct_wards(self) -> None:
        first, second = find_similar_population_pair(self.current)
        self.assertNotEqual(first["自治体"], second["自治体"])

    def test_history_change_has_all_wards(self) -> None:
        changes = history_changes(self.history)
        self.assertEqual(changes["自治体"].nunique(), 23)
        self.assertTrue(changes["人口増減率"].notna().all())
        self.assertTrue(changes["高齢化率変化"].notna().all())

    def test_offset_story_is_consistent(self) -> None:
        row = find_offset_ward(self.factors)
        self.assertIsNotNone(row)
        assert row is not None
        self.assertGreater(row["社会増減"], 0)
        self.assertLess(row["自然増減"], 0)
        self.assertGreater(row["人口増減"], 0)


if __name__ == "__main__":
    unittest.main()
