from __future__ import annotations

import argparse
import io
import re
import unicodedata
import urllib.request
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
RAW_PATH = ROOT / "data" / "raw" / "age_structure_2026" / "jy26qv0700.csv"
OUTPUT_PATH = ROOT / "data" / "tokyo_age_structure_2026.csv"
SOURCE_URL = "https://www.toukei.metro.tokyo.lg.jp/juukiy/2026/jy26qv0700.csv"

EXPECTED_COLUMNS = [
    "地域階層", "地域コード", "地域", "年齢階層", "年齢",
    "総数／計(人)", "総数／男(人)", "総数／女(人)",
    "日本人／計(人)", "日本人／男(人)", "日本人／女(人)",
    "外国人／計(人)", "外国人／男(人)", "外国人／女(人)",
]


def download(force: bool = False) -> bytes:
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    if RAW_PATH.exists() and not force:
        return RAW_PATH.read_bytes()

    request = urllib.request.Request(
        SOURCE_URL,
        headers={
            "User-Agent": "regional-map-app/age-structure",
            "Accept": "text/csv,*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        content = response.read()

    RAW_PATH.write_bytes(content)
    return content


def read_csv(content: bytes) -> pd.DataFrame:
    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "cp932", "shift_jis", "utf-8"):
        try:
            return pd.read_csv(io.BytesIO(content), encoding=encoding, dtype=str)
        except Exception as error:
            last_error = error
    raise RuntimeError(f"公式CSVを読めませんでした: {last_error}")


def normalize(value: object) -> str:
    return (
        unicodedata.normalize("NFKC", str(value))
        .replace("\\", "／")
        .replace("/", "／")
        .replace(" ", "")
        .replace("　", "")
    )


def canonicalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.rename(
        columns={column: normalize(column) for column in frame.columns}
    )
    lookup = {normalize(column): column for column in EXPECTED_COLUMNS}
    normalized = normalized.rename(
        columns={
            column: lookup.get(normalize(column), column)
            for column in normalized.columns
        }
    )
    missing = [
        column for column in EXPECTED_COLUMNS
        if column not in normalized.columns
    ]
    if missing:
        raise RuntimeError(
            "公式CSVの列を特定できません: "
            + ", ".join(missing)
            + " / 実際の列: "
            + ", ".join(map(str, normalized.columns))
        )
    return normalized[EXPECTED_COLUMNS].copy()


def numeric(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace("　", "", regex=False)
        .replace({"-": "0", "－": "0", "": pd.NA, "nan": pd.NA})
    )
    return pd.to_numeric(cleaned, errors="coerce")


def normalize_age(value: object) -> str:
    return (
        unicodedata.normalize("NFKC", str(value))
        .replace("~", "～")
        .replace("〜", "～")
        .replace("－", "～")
        .replace("-", "～")
        .replace(" ", "")
        .replace("　", "")
    )


def age_start(label: str) -> int | None:
    """0～4歳、0-4、100歳以上などから開始年齢を取る。"""
    match = re.search(r"(\d+)", label)
    return int(match.group(1)) if match else None


WARD_NAMES = {
    101: "千代田区",
    102: "中央区",
    103: "港区",
    104: "新宿区",
    105: "文京区",
    106: "台東区",
    107: "墨田区",
    108: "江東区",
    109: "品川区",
    110: "目黒区",
    111: "大田区",
    112: "世田谷区",
    113: "渋谷区",
    114: "中野区",
    115: "杉並区",
    116: "豊島区",
    117: "北区",
    118: "荒川区",
    119: "板橋区",
    120: "練馬区",
    121: "足立区",
    122: "葛飾区",
    123: "江戸川区",
}


def ward_code(value: object) -> int | None:
    """101、13101、131016のいずれでも区コードへ直す。"""
    digits = re.sub(r"\D", "", unicodedata.normalize("NFKC", str(value)))
    if not digits:
        return None

    if digits.startswith("13") and len(digits) >= 5:
        candidate = int(digits[2:5])
    else:
        candidate = int(digits[-3:])

    return candidate if candidate in WARD_NAMES else None


def prepare(frame: pd.DataFrame) -> pd.DataFrame:
    source = canonicalize_columns(frame)

    # 公式CSVの階層表現では、地域コードや地域名が空欄になる行もある。
    source["地域コード"] = source["地域コード"].replace("", pd.NA).ffill()
    source["地域"] = source["地域"].replace("", pd.NA).ffill()
    source["_区コード"] = source["地域コード"].map(ward_code)
    source["年齢"] = source["年齢"].map(normalize_age)

    wards = source.loc[source["_区コード"].isin(WARD_NAMES)].copy()
    wards["年齢開始"] = wards["年齢"].map(age_start)
    wards = wards.loc[wards["年齢開始"].notna()].copy()

    mapping = {
        "総数／計(人)": "総数",
        "総数／男(人)": "男",
        "総数／女(人)": "女",
        "日本人／計(人)": "日本人",
        "外国人／計(人)": "外国人",
    }
    for source_column, output_column in mapping.items():
        wards[output_column] = numeric(wards[source_column])

    wards["自治体コード"] = (
        "13" + wards["_区コード"].astype(int).astype(str).str.zfill(3)
    )
    wards["自治体"] = wards["_区コード"].map(WARD_NAMES)
    wards["年"] = 2026
    wards["年齢階級"] = wards["年齢"]
    wards["年齢開始"] = wards["年齢開始"].astype(int)

    output = (
        wards[
            [
                "自治体コード", "自治体", "年", "年齢階級", "年齢開始",
                "総数", "男", "女", "日本人", "外国人",
            ]
        ]
        .sort_values(["自治体コード", "年齢開始"])
        .reset_index(drop=True)
    )
    for column in ["総数", "男", "女", "日本人", "外国人"]:
        output[column] = output[column].fillna(0).astype(int)

    validate(output)
    return output


def validate(frame: pd.DataFrame) -> None:
    if frame["自治体"].nunique() != 23:
        raise RuntimeError(
            f"23区になっていません: {frame['自治体'].nunique()}区"
        )

    counts = frame.groupby("自治体")["年齢階級"].nunique()
    if counts.nunique() != 1 or int(counts.min()) < 20:
        raise RuntimeError(
            "年齢階級数が区ごとに一致しません: " + str(counts.to_dict())
        )

    if frame.duplicated(["自治体コード", "年齢階級"]).any():
        raise RuntimeError("自治体と年齢階級の重複があります")

    sex_error = (frame["男"] + frame["女"] - frame["総数"]).abs()
    nationality_error = (
        frame["日本人"] + frame["外国人"] - frame["総数"]
    ).abs()
    if not (sex_error <= 2).all():
        raise RuntimeError("男女計と総数が一致しません")
    if not (nationality_error <= 2).all():
        raise RuntimeError("日本人・外国人計と総数が一致しません")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    output = prepare(read_csv(download(force=args.force)))
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print("年齢構成データを作成しました。")
    print(f"- 自治体: {output['自治体'].nunique()}区")
    print(f"- 年齢階級: {output['年齢階級'].nunique()}区分")
    print(f"- レコード: {len(output):,}件")
    print(f"- 出力: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
