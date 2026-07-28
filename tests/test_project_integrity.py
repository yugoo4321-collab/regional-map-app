from __future__ import annotations

import json
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "tokyo_wards.csv"
HISTORY = ROOT / "data" / "tokyo_wards_history.csv"
FACTORS = ROOT / "data" / "tokyo_population_factors_2025.csv"
GEOJSON = ROOT / "data" / "tokyo_wards.geojson"


class ProjectIntegrityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.current = pd.read_csv(DATA, dtype={"自治体コード": str})
        cls.history = pd.read_csv(HISTORY, dtype={"自治体コード": str})
        cls.factors = pd.read_csv(FACTORS, dtype={"自治体コード": str})
        cls.geojson = json.loads(GEOJSON.read_text(encoding="utf-8"))

        for frame in (cls.current, cls.history, cls.factors):
            frame["自治体コード"] = frame["自治体コード"].str.zfill(5)

    def test_current_data_has_23_unique_wards(self) -> None:
        self.assertEqual(len(self.current), 23)
        self.assertEqual(self.current["自治体"].nunique(), 23)
        self.assertFalse(self.current["自治体コード"].duplicated().any())

    def test_history_is_complete_by_year(self) -> None:
        counts = self.history.groupby("年")["自治体"].nunique()
        self.assertTrue((counts == 23).all())
        self.assertFalse(
            self.history.duplicated(["自治体コード", "年"]).any()
        )

    def test_factor_equations(self) -> None:
        natural_error = (
            self.factors["出生数"]
            - self.factors["死亡数"]
            - self.factors["自然増減"]
        ).abs()
        total_error = (
            self.factors["社会増減"]
            + self.factors["自然増減"]
            + self.factors["その他増減"]
            - self.factors["人口増減"]
        ).abs()
        self.assertTrue((natural_error <= 2).all())
        self.assertTrue((total_error <= 1).all())

    def test_geojson_codes_match_current_data(self) -> None:
        geo_codes = {
            str(feature.get("properties", {}).get("N03_007", "")).zfill(5)
            for feature in self.geojson.get("features", [])
        }
        data_codes = set(self.current["自治体コード"])
        self.assertEqual(len(self.geojson.get("features", [])), 23)
        self.assertEqual(geo_codes, data_codes)

    def test_numeric_ranges(self) -> None:
        self.assertTrue((self.current["人口"] > 0).all())
        self.assertTrue(self.current["高齢化率"].between(0, 100).all())
        self.assertTrue((self.current["人口密度"] > 0).all())


if __name__ == "__main__":
    unittest.main()
