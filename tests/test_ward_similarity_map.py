from __future__ import annotations

import unittest

from ward_brief_tab import (
    load_brief_data,
    merged_brief_frame,
    prepare_similarity_geojson,
    similarity_feature_data,
    similarity_map_frame,
    similarity_table,
)


class WardSimilarityMapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        current, history, factors, age = load_brief_data()
        cls.frame = merged_brief_frame(
            current,
            history,
            factors,
            age,
        )
        cls.ward = "杉並区"

    def test_map_frame_has_all_wards(self) -> None:
        result = similarity_map_frame(
            self.frame,
            self.ward,
        )
        self.assertEqual(len(result), 23)
        selected = result.loc[
            result["自治体"].eq(self.ward)
        ].iloc[0]
        self.assertEqual(float(selected["近さ"]), 100.0)
        self.assertTrue(result["地図指数"].between(0, 100).all())

    def test_geojson_has_23_colored_features(self) -> None:
        geojson = prepare_similarity_geojson(
            self.frame,
            self.ward,
        )
        self.assertEqual(len(geojson["features"]), 23)
        for feature in geojson["features"]:
            properties = feature["properties"]
            self.assertIn("fill_color", properties)
            self.assertIn("line_color", properties)

    def test_feature_explanation_is_transparent(self) -> None:
        closest = similarity_table(
            self.frame,
            self.ward,
        ).iloc[0]["自治体"]
        differences = similarity_feature_data(
            self.frame,
            self.ward,
            closest,
        )
        self.assertEqual(len(differences), 10)
        self.assertTrue((differences["標準化差"] >= 0).all())
        self.assertTrue(
            differences["標準化差"].is_monotonic_increasing
        )


if __name__ == "__main__":
    unittest.main()
