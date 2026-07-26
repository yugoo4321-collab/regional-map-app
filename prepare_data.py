from __future__ import annotations

import csv
from pathlib import Path

SOURCE = Path("data/raw/tokyo_municipal_2026.csv")
OUTPUT = Path("data/tokyo_wards.csv")
REQUIRED_WARD_CODES = {f"{code:05d}" for code in range(13101, 13124)}


def parse_number(value: str) -> str:
    return value.replace(",", "").replace("%", "").strip()


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(
            "data/raw/tokyo_municipal_2026.csv が見つかりません。"
        )

    records = []

    with SOURCE.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.reader(file):
            if len(row) < 8:
                continue

            municipality_code = row[1].strip()
            name = row[2].strip()

            if municipality_code not in REQUIRED_WARD_CODES:
                continue
            if not name.endswith("区"):
                continue

            try:
                area = float(parse_number(row[3]))
                population = int(parse_number(row[4]))
                aging_rate = float(parse_number(row[7]))
            except ValueError:
                continue

            if area <= 0 or population <= 0:
                raise ValueError(f"{name}の面積または人口が不正です")

            records.append(
                {
                    "自治体コード": municipality_code,
                    "都道府県": "東京都",
                    "自治体": name,
                    "面積_km2": round(area, 2),
                    "人口": population,
                    "高齢化率": round(aging_rate, 2),
                    "人口密度": round(population / area, 1),
                }
            )

    records.sort(key=lambda record: record["自治体コード"])
    found_codes = {record["自治体コード"] for record in records}

    if found_codes != REQUIRED_WARD_CODES:
        missing = sorted(REQUIRED_WARD_CODES - found_codes)
        extra = sorted(found_codes - REQUIRED_WARD_CODES)
        raise ValueError(
            f"23区を正しく取得できませんでした。missing={missing}, extra={extra}"
        )

    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "自治体コード",
                "都道府県",
                "自治体",
                "面積_km2",
                "人口",
                "高齢化率",
                "人口密度",
            ],
        )
        writer.writeheader()
        writer.writerows(records)

    print(f"{OUTPUT} を更新しました")
    print(f"取得自治体数: {len(records)}")


if __name__ == "__main__":
    main()
