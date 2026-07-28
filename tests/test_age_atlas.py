from __future__ import annotations

import unittest
from pathlib import Path

from age_structure_tab import (
    age_atlas_data,
    load_age_data,
    prepare_age_atlas_geojson,
    selected_band_frame,
)


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "tokyo_age_structure_2026.csv"


class AgeAtlasTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load_age_data(str(DATA_PATH))
        cls.bands = (
            cls.data[["年齢階級", "年齢開始"]]
            .drop_duplicates()
            .sort_values("年齢開始")["年齢階級"]
            .tolist()
        )
        cls.band = cls.bands[min(5, len(cls.bands) - 1)]

    def test_each_band_has_23_wards(self) -> None:
        atlas = age_atlas_data(self.data)
        counts = atlas.groupby("年齢階級")["自治体"].nunique()
        self.assertTrue((counts == 23).all())

    def test_selected_band_ranking_is_complete(self) -> None:
        selected = selected_band_frame(
            self.data,
            self.band,
        )
        self.assertEqual(len(selected), 23)
        self.assertEqual(
            sorted(selected["順位"].tolist()),
            list(range(1, 24)),
        )
        self.assertTrue(selected["構成比"].is_monotonic_decreasing)

    def test_geojson_has_age_values(self) -> None:
        geojson = prepare_age_atlas_geojson(
            self.data,
            self.band,
            "杉並区",
        )
        self.assertEqual(len(geojson["features"]), 23)
        for feature in geojson["features"]:
            properties = feature["properties"]
            self.assertIn("構成比表示", properties)
            self.assertIn("fill_color", properties)


if __name__ == "__main__":
    unittest.main()
