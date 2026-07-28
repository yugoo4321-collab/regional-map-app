from __future__ import annotations

import csv
import io
import re
import unicodedata
import urllib.request
from pathlib import Path


YEAR = 2025
BASE_URL = "https://www.toukei.metro.tokyo.lg.jp/jugoki/2025"
SOURCES = {
    "他県移動増減": f"{BASE_URL}/ju25qv0800.csv",
    "都内間移動増減": f"{BASE_URL}/ju25qv1100.csv",
    "自然増減": f"{BASE_URL}/ju25qv1400.csv",
    "出生数": f"{BASE_URL}/ju25qv1500.csv",
    "死亡数": f"{BASE_URL}/ju25qv1600.csv",
    "その他増減": f"{BASE_URL}/ju25qv1700.csv",
}
ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "data" / "raw" / "population_factors_2025"
OUTPUT_PATH = ROOT / "data" / "tokyo_population_factors_2025.csv"

WARDS = [
    "千代田区", "中央区", "港区", "新宿区", "文京区", "台東区",
    "墨田区", "江東区", "品川区", "目黒区", "大田区", "世田谷区",
    "渋谷区", "中野区", "杉並区", "豊島区", "北区", "荒川区",
    "板橋区", "練馬区", "足立区", "葛飾区", "江戸川区",
]


def normalize(value: str) -> str:
    return unicodedata.normalize("NFKC", value).replace("\u3000", " ").strip()


def decode_bytes(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "cp932", "shift_jis", "utf-8"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("CSVの文字コードを判定できませんでした")


def download(url: str, destination: Path) -> bytes:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/csv,text/plain,*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        raw = response.read()
    if len(raw) < 500:
        raise ValueError(f"取得したファイルが小さすぎます: {url}")
    destination.write_bytes(raw)
    return raw


def parse_number(value: str) -> int | None:
    cleaned = normalize(value)
    if not cleaned:
        return None
    negative = cleaned.startswith(("△", "▲"))
    cleaned = cleaned.lstrip("△▲")
    cleaned = cleaned.replace(",", "").replace(" ", "")
    cleaned = cleaned.replace("−", "-").replace("ー", "-").replace("―", "-")
    if cleaned in {"-", "…", "...", "x", "X"}:
        return None
    if not re.fullmatch(r"[+-]?\d+(?:\.0+)?", cleaned):
        return None
    number = int(float(cleaned))
    return -abs(number) if negative else number


def row_context(rows: list[list[str]], index: int, width: int = 10) -> str:
    start = max(0, index - width)
    return " ".join(
        cell
        for row in rows[start:index]
        for cell in row
        if cell
    )


def select_total_section_occurrences(
    rows: list[list[str]],
    ward: str,
) -> list[int]:
    occurrences = [
        index
        for index, row in enumerate(rows)
        if ward in row
    ]
    if len(occurrences) <= 1:
        return occurrences

    scored: list[tuple[int, int]] = []
    for index in occurrences:
        context = row_context(rows, index)
        score = 0
        if "総数" in context:
            score += 5
        if "15-1" in context or "16-1" in context or "14-1" in context:
            score += 2
        if "日本人" in context:
            score -= 4
        if "外国人" in context:
            score -= 4
        scored.append((score, index))

    best_score = max(score for score, _ in scored)
    return [index for score, index in scored if score == best_score]


def annual_value_from_row(row: list[str], ward: str) -> int:
    name_index = row.index(ward)
    values = [parse_number(cell) for cell in row[name_index + 1:]]

    # 12か月＋年間計の連続列を探す。
    for start in range(max(0, len(values) - 20), len(values)):
        window = values[start:start + 13]
        if len(window) < 13 or any(value is None for value in window):
            continue
        months = [int(value) for value in window[:12] if value is not None]
        total = int(window[12])
        if abs(sum(months) - total) <= 1:
            return total

    # 年間計がなく12か月だけの場合。
    non_missing = [int(value) for value in values if value is not None]
    if len(non_missing) >= 12:
        last_thirteen = non_missing[-13:]
        if len(last_thirteen) == 13 and abs(sum(last_thirteen[:12]) - last_thirteen[12]) <= 1:
            return last_thirteen[12]
        return sum(non_missing[-12:])

    raise ValueError(f"{ward}の年間値を判定できませんでした: {row}")


def extract_ward_values(raw: bytes, label: str) -> dict[str, int]:
    text = decode_bytes(raw)
    rows = [
        [normalize(cell) for cell in row]
        for row in csv.reader(io.StringIO(text))
    ]

    result: dict[str, int] = {}
    for ward in WARDS:
        candidate_indexes = select_total_section_occurrences(rows, ward)
        if not candidate_indexes:
            raise ValueError(f"{label}: {ward}が見つかりません")
        last_error: Exception | None = None
        for index in candidate_indexes:
            try:
                result[ward] = annual_value_from_row(rows[index], ward)
                break
            except Exception as error:
                last_error = error
        if ward not in result:
            raise ValueError(f"{label}: {ward}の値を取得できません") from last_error

    if len(result) != 23:
        raise ValueError(f"{label}: 23区ではなく{len(result)}区です")
    return result


def main() -> None:
    extracted: dict[str, dict[str, int]] = {}

    for label, url in SOURCES.items():
        destination = RAW_DIR / Path(url).name
        try:
            raw = download(url, destination)
        except Exception:
            if destination.exists():
                raw = destination.read_bytes()
            else:
                raise
        extracted[label] = extract_ward_values(raw, label)
        print(f"{label}: 23区取得")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8-sig", newline="") as file:
        fieldnames = [
            "年",
            "自治体コード",
            "自治体",
            "他県移動増減",
            "都内間移動増減",
            "社会増減",
            "出生数",
            "死亡数",
            "自然増減",
            "その他増減",
            "人口増減",
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for index, ward in enumerate(WARDS, start=101):
            other_prefecture = extracted["他県移動増減"][ward]
            within_tokyo = extracted["都内間移動増減"][ward]
            natural = extracted["自然増減"][ward]
            births = extracted["出生数"][ward]
            deaths = extracted["死亡数"][ward]
            other = extracted["その他増減"][ward]
            social = other_prefecture + within_tokyo
            total = social + natural + other

            # 公表されている自然増減と出生－死亡の整合を確認。
            if abs((births - deaths) - natural) > 2:
                raise ValueError(
                    f"{ward}: 自然増減の整合が取れません "
                    f"({births} - {deaths} != {natural})"
                )

            writer.writerow(
                {
                    "年": YEAR,
                    "自治体コード": f"13{index:03d}",
                    "自治体": ward,
                    "他県移動増減": other_prefecture,
                    "都内間移動増減": within_tokyo,
                    "社会増減": social,
                    "出生数": births,
                    "死亡数": deaths,
                    "自然増減": natural,
                    "その他増減": other,
                    "人口増減": total,
                }
            )

    print(f"{OUTPUT_PATH} を作成しました")
    print("自治体数: 23区")
    print(f"対象年: {YEAR}年中")


if __name__ == "__main__":
    main()
