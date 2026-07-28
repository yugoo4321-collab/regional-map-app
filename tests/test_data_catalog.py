from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from data_catalog_tab import DATASETS, INDICATORS, build_catalog


ROOT = Path(__file__).resolve().parents[1]


class DataCatalogTest(unittest.TestCase):
    def test_registry_has_unique_keys(self) -> None:
        keys = [item["path_key"] for item in DATASETS]
        self.assertEqual(len(keys), len(set(keys)))

    def test_indicator_names_are_unique(self) -> None:
        names = [item["指標"] for item in INDICATORS]
        self.assertEqual(len(names), len(set(names)))

    def test_catalog_reads_project_files(self) -> None:
        catalog = build_catalog(
            str(ROOT / "data" / "tokyo_wards.csv"),
            str(ROOT / "data" / "tokyo_wards_history.csv"),
            str(ROOT / "data" / "tokyo_population_factors_2025.csv"),
            str(ROOT / "data" / "tokyo_wards.geojson"),
        )
        self.assertEqual(len(catalog), 4)
        self.assertTrue((catalog["状態"] == "OK").all())
        self.assertTrue(
            (
                pd.to_numeric(
                    catalog["自治体数"],
                    errors="coerce",
                )
                == 23
            ).all()
        )


if __name__ == "__main__":
    unittest.main()
