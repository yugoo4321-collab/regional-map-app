from __future__ import annotations

import csv
import re
import ssl
import subprocess
import sys
import unicodedata
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
OUTPUT_PATH = PROJECT_DIR / "data" / "tokyo_wards_history.csv"
POPULATION_URL = "https://www.toukei.metro.tokyo.lg.jp/juukiy/jy26rv0200.csv"
AGING_SHARE_URL = "https://www.toukei.metro.tokyo.lg.jp/juukiy/jy26rv0906.csv"
START_YEAR = 2015
END_YEAR = 2026

WARD_CODES = {
    "千代田区": "13101", "中央区": "13102", "港区": "13103",
    "新宿区": "13104", "文京区": "13105", "台東区": "13106",
    "墨田区": "13107", "江東区": "13108", "品川区": "13109",
    "目黒区": "13110", "大田区": "13111", "世田谷区": "13112",
    "渋谷区": "13113", "中野区": "13114", "杉並区": "13115",
    "豊島区": "13116", "北区": "13117", "荒川区": "13118",
    "板橋区": "13119", "練馬区": "13120", "足立区": "13121",
    "葛飾区": "13122", "江戸川区": "13123",
}


def normalize(value: object) -> str:
    return unicodedata.normalize("NFKC", str(value or "")).replace("\u3000", " ").strip()


def download_file(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        context = ssl.create_default_context()
        with urlopen(request, timeout=60, context=context) as response:
            content = response.read()
        if len(content) < 1000:
            raise ValueError(f"取得したファイルが小さすぎます: {len(content)} bytes")
        path.write_bytes(content)
        return
    except Exception as first_error:
        print(f"Pythonでの取得に失敗したためcurlを試します: {first_error}")
    result = subprocess.run(
        ["curl", "-fL", "-A", "Mozilla/5.0", url, "-o", str(path)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not path.exists() or path.stat().st_size < 1000:
        raise RuntimeError(
            f"公式CSVを取得できませんでした: {url}\n{result.stderr.strip()}"
        )


def decode_csv(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "cp932", "shift_jis", "utf-8"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"文字コードを判定できませんでした: {path}")


def parse_year(value: str) -> int | None:
    text = normalize(value).replace(" ", "")
    match = re.search(r"(?<!\d)((?:19|20)\d{2})(?!\d)", text)
    if match:
        year = int(match.group(1))
        return year if 1985 <= year <= END_YEAR else None
    era_starts = {"昭和": 1925, "平成": 1988, "令和": 2018}
    for era, offset in era_starts.items():
        match = re.search(rf"{era}(元|\d{{1,2}})年?", text)
        if match:
            number = 1 if match.group(1) == "元" else int(match.group(1))
            year = offset + number
            return year if 1985 <= year <= END_YEAR else None
    short_eras = {"S": 1925, "H": 1988, "R": 2018}
    match = re.fullmatch(r"([SHR])(元|\d{1,2})", text, flags=re.IGNORECASE)
    if match:
        number = 1 if match.group(2) == "元" else int(match.group(2))
        return short_eras[match.group(1).upper()] + number
    return None


def parse_number(value: object) -> float | None:
    text = normalize(value)
    if not text or text in {"-", "－", "…", "...", "X", "x"}:
        return None
    text = text.replace(",", "").replace("%", "").replace("％", "")
    text = text.replace("人", "").replace(" ", "")
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    if not match:
        return None
    return float(match.group())


def header_score(rows: list[list[str]], column: int) -> int:
    context = " ".join(
        normalize(row[column]) for row in rows[:25] if column < len(row)
    )
    if any(label in context for label in ("総数", "男女計", "男女総数", "総計")):
        return 10
    if re.search(r"(^|\s)計($|\s)", context):
        return 8
    if any(label in context for label in ("男", "女")):
        return -3
    return 0


def detect_year_columns(rows: list[list[str]]) -> dict[int, int]:
    candidates: dict[int, list[int]] = {}
    for row in rows[:40]:
        for column, cell in enumerate(row):
            year = parse_year(cell)
            if year is not None:
                candidates.setdefault(year, []).append(column)

    # Handles two-level headers where era and year number are split across rows.
    for era_row_index, era_row in enumerate(rows[:20]):
        carried_era: str | None = None
        era_by_column: dict[int, str] = {}
        for column, cell in enumerate(era_row):
            text = normalize(cell)
            for era in ("昭和", "平成", "令和"):
                if era in text:
                    carried_era = era
                    break
            if carried_era:
                era_by_column[column] = carried_era
        if not era_by_column:
            continue
        for number_row in rows[era_row_index + 1 : era_row_index + 5]:
            for column, era in era_by_column.items():
                if column >= len(number_row):
                    continue
                number_text = normalize(number_row[column]).replace("年", "")
                if number_text == "元" or re.fullmatch(r"\d{1,2}", number_text):
                    year = parse_year(f"{era}{number_text}年")
                    if year is not None:
                        candidates.setdefault(year, []).append(column)

    selected: dict[int, int] = {}
    for year, columns in candidates.items():
        if START_YEAR <= year <= END_YEAR:
            unique_columns = sorted(set(columns))
            selected[year] = max(
                unique_columns,
                key=lambda column: (header_score(rows, column), -column),
            )
    expected = set(range(START_YEAR, END_YEAR + 1))
    missing = sorted(expected - set(selected))
    if missing:
        raise ValueError(
            "年次列を判定できませんでした。不足年: " + ", ".join(map(str, missing))
        )
    return dict(sorted(selected.items()))


def row_priority(row: list[str]) -> int:
    text = " ".join(normalize(cell) for cell in row[:12])
    if any(label in text for label in ("男女計", "男女総数", "総数", "総計")):
        return 20
    if re.search(r"(^|\s)計($|\s)", text):
        return 15
    if "男" in text or "女" in text:
        return -5
    return 0


def choose_candidate(candidates: list[tuple[int, list[float], dict[int, float]]], kind: str):
    if not candidates:
        return None
    highest_priority = max(item[0] for item in candidates)
    prioritized = [item for item in candidates if item[0] == highest_priority]
    if kind == "population":
        return max(prioritized, key=lambda item: sum(item[1]) / len(item[1]))
    # With no explicit total label, total rates normally lie between male and female rows.
    ordered = sorted(prioritized, key=lambda item: sum(item[1]) / len(item[1]))
    return ordered[len(ordered) // 2]


def extract_series(text: str, kind: str) -> dict[str, dict[int, float]]:
    rows = [list(row) for row in csv.reader(text.splitlines())]
    year_columns = detect_year_columns(rows)
    grouped: dict[str, list[tuple[int, list[float], dict[int, float]]]] = {
        ward: [] for ward in WARD_CODES
    }
    for row in rows:
        normalized_cells = [normalize(cell) for cell in row]
        ward = next((name for name in WARD_CODES if name in normalized_cells), None)
        if ward is None:
            continue
        values: dict[int, float] = {}
        for year, column in year_columns.items():
            if column >= len(row):
                continue
            number = parse_number(row[column])
            if number is not None:
                values[year] = number
        if len(values) < len(year_columns) - 1:
            continue
        ordered_values = [values[year] for year in sorted(values)]
        grouped[ward].append((row_priority(row), ordered_values, values))

    result: dict[str, dict[int, float]] = {}
    for ward, candidates in grouped.items():
        selected = choose_candidate(candidates, kind)
        if selected is None:
            raise ValueError(f"{ward}の{kind}時系列を取得できませんでした")
        result[ward] = selected[2]
    return result


def build_history(population_path: Path, aging_path: Path) -> pd.DataFrame:
    population = extract_series(decode_csv(population_path), "population")
    aging = extract_series(decode_csv(aging_path), "aging")
    records: list[dict[str, object]] = []
    for ward, code in WARD_CODES.items():
        for year in range(START_YEAR, END_YEAR + 1):
            pop_value = population[ward].get(year)
            aging_value = aging[ward].get(year)
            if pop_value is None or aging_value is None:
                raise ValueError(f"{ward}・{year}年の値が不足しています")
            # Some source tables may store ratios as 0-1 rather than 0-100.
            if 0 <= aging_value <= 1:
                aging_value *= 100
            records.append(
                {
                    "自治体コード": code,
                    "自治体": ward,
                    "年": year,
                    "人口": int(round(pop_value)),
                    "高齢化率": round(float(aging_value), 4),
                }
            )
    history = pd.DataFrame(records)
    expected_rows = len(WARD_CODES) * (END_YEAR - START_YEAR + 1)
    if len(history) != expected_rows:
        raise ValueError(f"経年データが{expected_rows}行ではなく{len(history)}行です")
    if not history["高齢化率"].between(5, 50).all():
        bad = history.loc[~history["高齢化率"].between(5, 50)].head()
        raise ValueError(f"高齢化率の値を確認してください:\n{bad.to_string(index=False)}")
    if not history["人口"].between(10_000, 2_000_000).all():
        bad = history.loc[~history["人口"].between(10_000, 2_000_000)].head()
        raise ValueError(f"人口の値を確認してください:\n{bad.to_string(index=False)}")
    return history.sort_values(["年", "自治体コード"]).reset_index(drop=True)


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    population_path = RAW_DIR / "tokyo_population_timeseries_1985_2026.csv"
    aging_path = RAW_DIR / "tokyo_aging_share_timeseries_1985_2026.csv"
    print("東京都公式の経年CSVを取得します。")
    download_file(POPULATION_URL, population_path)
    download_file(AGING_SHARE_URL, aging_path)
    print("2015〜2026年の東京23区データを整形します。")
    history = build_history(population_path, aging_path)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    history.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"作成: {OUTPUT_PATH}")
    print(f"自治体数: {history['自治体'].nunique()}区")
    print(f"年次: {history['年'].min()}〜{history['年'].max()}年")
    print(f"行数: {len(history)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"経年データの作成に失敗しました: {error}", file=sys.stderr)
        raise
