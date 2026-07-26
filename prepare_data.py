from pathlib import Path
import csv


source = Path("data/raw/tokyo_municipal_2026.csv")
output = Path("data/tokyo_wards.csv")

records = []

with source.open(encoding="utf-8-sig", newline="") as file:
    for row in csv.reader(file):
        if len(row) < 8:
            continue

        municipality_code = row[1].strip()
        name = row[2].strip()

        if not municipality_code.startswith("131"):
            continue

        if not name.endswith("区"):
            continue

        try:
            population = int(row[4].replace(",", ""))
            aging_rate = float(row[7].replace("%", ""))
        except ValueError:
            continue

        records.append(
            {
                "都道府県": "東京都",
                "自治体": name,
                "人口": population,
                "高齢化率": aging_rate,
            }
        )

if len(records) != 23:
    raise ValueError(
        f"23区のうち{len(records)}区しか取得できませんでした"
    )

with output.open("w", encoding="utf-8-sig", newline="") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=["都道府県", "自治体", "人口", "高齢化率"],
    )
    writer.writeheader()
    writer.writerows(records)

print(f"{output} を作成しました")
print(f"取得自治体数: {len(records)}")
