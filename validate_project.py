from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
CURRENT_PATH = ROOT / "data" / "tokyo_wards.csv"
HISTORY_PATH = ROOT / "data" / "tokyo_wards_history.csv"
GEOJSON_PATH = ROOT / "data" / "tokyo_wards.geojson"
RAW_POPULATION_PATH = ROOT / "data" / "raw" / "tokyo_population_timeseries_1985_2026.csv"
RAW_AGING_PATH = ROOT / "data" / "raw" / "tokyo_aging_share_timeseries_1985_2026.csv"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_current() -> tuple[pd.DataFrame, list[str]]:
    require(CURRENT_PATH.exists(), f"{CURRENT_PATH} がありません")
    data = pd.read_csv(CURRENT_PATH, dtype={"自治体コード": str})
    required = {
        "自治体コード",
        "都道府県",
        "自治体",
        "面積_km2",
        "人口",
        "高齢化率",
        "人口密度",
    }
    require(required <= set(data.columns), "現況CSVに必要列がありません")
    data["自治体コード"] = data["自治体コード"].str.zfill(5)
    require(len(data) == 23, f"現況CSVが23行ではありません: {len(data)}")
    require(data["自治体"].nunique() == 23, "現況CSVの区名が23区ではありません")
    require(not data["自治体コード"].duplicated().any(), "現況CSVの自治体コードが重複")
    require(not data[list(required)].isna().any().any(), "現況CSVに欠損があります")
    require((data["人口"] > 0).all(), "現況人口に0以下があります")
    require(data["高齢化率"].between(0, 100).all(), "現況高齢化率が範囲外")
    require((data["面積_km2"] > 0).all(), "面積に0以下があります")
    require((data["人口密度"] > 0).all(), "人口密度に0以下があります")

    recalculated = data["人口"] / data["面積_km2"]
    relative_error = ((data["人口密度"] - recalculated).abs() / recalculated).max()
    require(relative_error < 0.01, f"人口密度の再計算誤差が大きいです: {relative_error:.3%}")
    return data, sorted(data["自治体コード"].tolist())


def validate_geojson(expected_codes: list[str]) -> None:
    require(GEOJSON_PATH.exists(), f"{GEOJSON_PATH} がありません")
    with GEOJSON_PATH.open(encoding="utf-8") as file:
        geojson = json.load(file)
    features = geojson.get("features", [])
    require(len(features) == 23, f"GeoJSONが23区ではありません: {len(features)}")
    codes = sorted(
        str(feature.get("properties", {}).get("N03_007", "")).zfill(5)
        for feature in features
    )
    require(codes == expected_codes, "GeoJSONと現況CSVの自治体コードが一致しません")


def validate_history() -> pd.DataFrame:
    require(HISTORY_PATH.exists(), f"{HISTORY_PATH} がありません")
    history = pd.read_csv(HISTORY_PATH, dtype={"自治体コード": str})
    required = {"自治体コード", "自治体", "年", "人口", "高齢化率"}
    require(required <= set(history.columns), "経年CSVに必要列がありません")
    history["自治体コード"] = history["自治体コード"].str.zfill(5)
    require(history["自治体"].nunique() == 23, "経年CSVが23区ではありません")
    require(
        not history.duplicated(["自治体コード", "年"]).any(),
        "経年CSVに自治体・年の重複があります",
    )
    require(not history[list(required)].isna().any().any(), "経年CSVに欠損があります")
    require((history["人口"] > 0).all(), "経年人口に0以下があります")
    require(history["高齢化率"].between(0, 100).all(), "経年高齢化率が範囲外")

    years = sorted(int(year) for year in history["年"].unique())
    require(years == list(range(min(years), max(years) + 1)), "経年データの年が連続していません")
    expected_rows = 23 * len(years)
    require(len(history) == expected_rows, f"経年CSVの行数が不正です: {len(history)} / {expected_rows}")

    counts = history.groupby("自治体コード")["年"].nunique()
    require((counts == len(years)).all(), "一部の区で年次が欠けています")
    require(RAW_POPULATION_PATH.exists(), "人口の元CSVがありません")
    require(RAW_AGING_PATH.exists(), "高齢化率の元CSVがありません")
    return history


def main() -> None:
    current, codes = validate_current()
    validate_geojson(codes)
    history = validate_history()
    years = sorted(history["年"].unique())
    print("品質チェックに合格しました")
    print(f"現況: {len(current)}行 / {current['自治体'].nunique()}区")
    print(
        f"経年: {len(history)}行 / {history['自治体'].nunique()}区 / "
        f"{years[0]}〜{years[-1]}年"
    )
    print("欠損: 0件 / 重複: 0件 / GeoJSON整合: OK")


if __name__ == "__main__":
    main()
