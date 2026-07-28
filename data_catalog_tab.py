from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


CATALOG_STYLE = """
<style>
.catalog-head {
    padding: 0.2rem 0 1rem;
    border-bottom: 1px solid #D5DDE5;
    margin-bottom: 1rem;
}
.catalog-title {
    color: #17263A;
    font-size: clamp(1.7rem, 3vw, 2.3rem);
    letter-spacing: -0.035em;
    margin: 0;
}
.catalog-lead {
    max-width: 820px;
    color: #566477;
    line-height: 1.75;
    margin: 0.6rem 0 0;
}
.catalog-flow {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    border-top: 1px solid #CDD6DF;
    border-bottom: 1px solid #CDD6DF;
    margin: 0.7rem 0 1rem;
}
.catalog-flow-item {
    padding: 0.9rem 0.8rem;
    border-right: 1px solid #D8DFE6;
}
.catalog-flow-item:last-child {
    border-right: 0;
}
.catalog-flow-no {
    color: #8A95A4;
    font-size: 0.7rem;
    font-weight: 760;
}
.catalog-flow-name {
    color: #17263A;
    font-weight: 760;
    margin-top: 0.25rem;
}
.catalog-flow-note {
    color: #667487;
    font-size: 0.77rem;
    line-height: 1.55;
    margin-top: 0.25rem;
}
.catalog-status {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.58rem 0;
    border-bottom: 1px solid #E1E6EB;
    color: #3D4C5F;
    font-size: 0.86rem;
}
.catalog-status-dot {
    width: 0.62rem;
    height: 0.62rem;
    border-radius: 50%;
    background: #2E7D5B;
    flex: 0 0 auto;
}
.catalog-source {
    padding: 0.75rem 0;
    border-top: 1px solid #E1E6EB;
}
.catalog-source-name {
    color: #17263A;
    font-weight: 720;
}
.catalog-source-note {
    color: #657286;
    font-size: 0.8rem;
    line-height: 1.6;
    margin-top: 0.2rem;
}
@media (max-width: 850px) {
    .catalog-flow {
        grid-template-columns: 1fr 1fr;
    }
    .catalog-flow-item:nth-child(2) {
        border-right: 0;
    }
    .catalog-flow-item:nth-child(-n+2) {
        border-bottom: 1px solid #D8DFE6;
    }
}
</style>
"""


DATASETS = [
    {
        "name": "現在値",
        "path_key": "current",
        "coverage": "東京23区",
        "period": "最新値",
        "source": "東京都の公開統計",
        "source_url": "https://www.toukei.metro.tokyo.lg.jp/",
        "note": "人口、高齢化率、面積、人口密度。",
    },
    {
        "name": "経年データ",
        "path_key": "history",
        "coverage": "東京23区",
        "period": "2015–2026",
        "source": "東京都の公開統計",
        "source_url": "https://www.toukei.metro.tokyo.lg.jp/",
        "note": "人口と高齢化率の年次推移。",
    },
    {
        "name": "人口動態",
        "path_key": "factors",
        "coverage": "東京23区",
        "period": "2025年中",
        "source": "東京都総務局統計部「人口の動き」",
        "source_url": "https://www.toukei.metro.tokyo.lg.jp/jugoki/2025/ju25q10000.htm",
        "note": "社会増減、自然増減、出生、死亡、その他増減。",
    },
    {
        "name": "行政区域",
        "path_key": "geojson",
        "coverage": "東京23区",
        "period": "境界データ",
        "source": "国土数値情報 行政区域データ",
        "source_url": "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N03-v3_1.html",
        "note": "地図描画に使うGeoJSON。",
    },
]


INDICATORS = [
    {
        "指標": "人口",
        "単位": "人",
        "定義・計算": "各区の人口",
        "主な画面": "地図、比較、経年変化",
        "注意": "統計時点はデータ更新年に従う。",
    },
    {
        "指標": "高齢化率",
        "単位": "%",
        "定義・計算": "65歳以上人口 ÷ 総人口 × 100",
        "主な画面": "地図、構造分析、経年変化",
        "注意": "人口規模とは別の比率指標。",
    },
    {
        "指標": "人口密度",
        "単位": "人/km²",
        "定義・計算": "人口 ÷ 面積",
        "主な画面": "地図、比較、構造分析",
        "注意": "可住地面積ではなく行政区域面積を使用。",
    },
    {
        "指標": "社会増減",
        "単位": "人",
        "定義・計算": "他県移動増減 ＋ 都内間移動増減",
        "主な画面": "要因分析",
        "注意": "人の移動による増減。",
    },
    {
        "指標": "自然増減",
        "単位": "人",
        "定義・計算": "出生数 − 死亡数",
        "主な画面": "要因分析",
        "注意": "出生と死亡による増減。",
    },
    {
        "指標": "人口増減",
        "単位": "人",
        "定義・計算": "社会増減 ＋ 自然増減 ＋ その他増減",
        "主な画面": "要因分析",
        "注意": "1年間の人口動態。",
    },
    {
        "指標": "中央値指数",
        "単位": "指数",
        "定義・計算": "各区の値 ÷ 23区中央値 × 100",
        "主な画面": "2区比較",
        "注意": "単位が異なる指標を足さず、相対位置だけを比べる。",
    },
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()[:12]


def _csv_summary(path: Path) -> dict[str, Any]:
    frame = pd.read_csv(path)
    years = ""
    if "年" in frame.columns:
        numeric_years = pd.to_numeric(frame["年"], errors="coerce").dropna()
        if not numeric_years.empty:
            minimum = int(numeric_years.min())
            maximum = int(numeric_years.max())
            years = str(minimum) if minimum == maximum else f"{minimum}–{maximum}"

    wards = (
        int(frame["自治体"].nunique())
        if "自治体" in frame.columns
        else None
    )
    return {
        "rows": len(frame),
        "columns": len(frame.columns),
        "wards": wards,
        "years": years,
    }


def _geojson_summary(path: Path) -> dict[str, Any]:
    content = json.loads(path.read_text(encoding="utf-8"))
    features = content.get("features", [])
    return {
        "rows": len(features),
        "columns": "",
        "wards": len(features),
        "years": "",
    }


@st.cache_data(show_spinner=False)
def build_catalog(
    current_path: str,
    history_path: str,
    factor_path: str,
    geojson_path: str,
) -> pd.DataFrame:
    paths = {
        "current": Path(current_path),
        "history": Path(history_path),
        "factors": Path(factor_path),
        "geojson": Path(geojson_path),
    }

    rows: list[dict[str, Any]] = []
    for dataset in DATASETS:
        path = paths[dataset["path_key"]]
        if not path.exists():
            rows.append(
                {
                    "データ": dataset["name"],
                    "対象": dataset["coverage"],
                    "期間": dataset["period"],
                    "件数": "未取得",
                    "列数": "",
                    "自治体数": "",
                    "ファイル": str(path),
                    "指紋": "",
                    "状態": "不足",
                }
            )
            continue

        summary = (
            _geojson_summary(path)
            if path.suffix.lower() in {".json", ".geojson"}
            else _csv_summary(path)
        )
        rows.append(
            {
                "データ": dataset["name"],
                "対象": dataset["coverage"],
                "期間": summary["years"] or dataset["period"],
                "件数": summary["rows"],
                "列数": summary["columns"],
                "自治体数": summary["wards"],
                "ファイル": str(path),
                "指紋": _sha256(path),
                "状態": "OK",
            }
        )

    return pd.DataFrame(rows)


def _quality_checks(
    current_data: pd.DataFrame,
    history: pd.DataFrame,
    factors: pd.DataFrame,
    geojson_path: Path,
) -> list[tuple[str, bool]]:
    checks = [
        (
            "現在値が23区で、自治体コードに重複がない",
            len(current_data) == 23
            and current_data["自治体"].nunique() == 23
            and not current_data["自治体コード"].duplicated().any(),
        ),
        (
            "経年データの各年に23区がそろう",
            bool(
                (
                    history.groupby("年")["自治体"].nunique()
                    == 23
                ).all()
            ),
        ),
        (
            "経年データに自治体・年の重複がない",
            not history.duplicated(["自治体コード", "年"]).any(),
        ),
    ]

    if not factors.empty:
        natural_error = (
            factors["出生数"]
            - factors["死亡数"]
            - factors["自然増減"]
        ).abs()
        total_error = (
            factors["社会増減"]
            + factors["自然増減"]
            + factors["その他増減"]
            - factors["人口増減"]
        ).abs()
        checks.extend(
            [
                (
                    "自然増減＝出生数−死亡数",
                    bool((natural_error <= 2).all()),
                ),
                (
                    "人口増減＝社会増減＋自然増減＋その他増減",
                    bool((total_error <= 1).all()),
                ),
            ]
        )

    try:
        geojson = json.loads(geojson_path.read_text(encoding="utf-8"))
        feature_count = len(geojson.get("features", []))
    except Exception:
        feature_count = 0

    checks.append(("行政区域が23件", feature_count == 23))
    return checks


def render_data_catalog(
    current_data: pd.DataFrame,
    history: pd.DataFrame,
    current_path: str,
    history_path: str,
    factor_path: str,
    geojson_path: str,
) -> None:
    st.markdown(CATALOG_STYLE, unsafe_allow_html=True)

    factor_source = Path(factor_path)
    factors = (
        pd.read_csv(factor_source, dtype={"自治体コード": str})
        if factor_source.exists()
        else pd.DataFrame()
    )

    catalog = build_catalog(
        current_path,
        history_path,
        factor_path,
        geojson_path,
    )
    indicators = pd.DataFrame(INDICATORS)

    st.markdown(
        """
        <div class="catalog-head">
            <h2 class="catalog-title">データ台帳</h2>
            <p class="catalog-lead">
                どのファイルを、どの定義で、どの画面に使ったかをまとめる。
                件数、対象期間、ファイル指紋、検証結果もここで確認する。
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metric_columns = st.columns(4)
    metric_columns[0].metric("データセット", f"{len(catalog)}種類")
    metric_columns[1].metric("自治体", f"{current_data['自治体'].nunique()}区")
    metric_columns[2].metric(
        "収録期間",
        f"{int(history['年'].min())}–{int(history['年'].max())}",
    )
    metric_columns[3].metric(
        "経年レコード",
        f"{len(history):,}件",
    )

    st.markdown(
        """
        <div class="catalog-flow">
            <div class="catalog-flow-item">
                <div class="catalog-flow-no">1</div>
                <div class="catalog-flow-name">取得</div>
                <div class="catalog-flow-note">公開統計と行政区域データ</div>
            </div>
            <div class="catalog-flow-item">
                <div class="catalog-flow-no">2</div>
                <div class="catalog-flow-name">整形</div>
                <div class="catalog-flow-note">自治体コードで結合</div>
            </div>
            <div class="catalog-flow-item">
                <div class="catalog-flow-no">3</div>
                <div class="catalog-flow-name">検証</div>
                <div class="catalog-flow-note">件数、重複、値域、計算式</div>
            </div>
            <div class="catalog-flow-item">
                <div class="catalog-flow-no">4</div>
                <div class="catalog-flow-name">表示</div>
                <div class="catalog-flow-note">地図、比較、経年、要因分析</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### ファイル一覧")
    st.dataframe(
        catalog,
        hide_index=True,
        width="stretch",
        column_config={
            "ファイル": st.column_config.TextColumn(width="large"),
            "指紋": st.column_config.TextColumn(
                help="ファイル内容から作ったSHA-256の先頭12文字"
            ),
        },
    )

    st.download_button(
        "データ台帳を保存",
        data=catalog.to_csv(index=False).encode("utf-8-sig"),
        file_name="tokyo23_data_catalog.csv",
        mime="text/csv",
        key="download_data_catalog",
    )

    st.divider()
    dictionary_column, quality_column = st.columns([1.2, 0.8], gap="large")

    with dictionary_column:
        st.markdown("### 指標の定義")
        st.dataframe(
            indicators,
            hide_index=True,
            width="stretch",
        )
        st.download_button(
            "指標定義を保存",
            data=indicators.to_csv(index=False).encode("utf-8-sig"),
            file_name="tokyo23_indicator_dictionary.csv",
            mime="text/csv",
            key="download_indicator_dictionary",
        )

    with quality_column:
        st.markdown("### 検証結果")
        checks = _quality_checks(
            current_data,
            history,
            factors,
            Path(geojson_path),
        )
        for label, passed in checks:
            icon = "●" if passed else "×"
            color = "#2E7D5B" if passed else "#B74343"
            st.markdown(
                (
                    '<div class="catalog-status">'
                    f'<span class="catalog-status-dot" '
                    f'style="background:{color}"></span>'
                    f"<span>{icon} {label}</span>"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )

        passed_count = sum(int(passed) for _, passed in checks)
        st.caption(f"{passed_count}/{len(checks)}項目が正常")

    st.divider()
    st.markdown("### 出典")
    for dataset in DATASETS:
        st.markdown(
            (
                '<div class="catalog-source">'
                f'<div class="catalog-source-name">{dataset["source"]}</div>'
                f'<div class="catalog-source-note">'
                f'{dataset["name"]}：{dataset["note"]}'
                "</div></div>"
            ),
            unsafe_allow_html=True,
        )
        st.link_button(
            f'{dataset["name"]}の出典',
            dataset["source_url"],
            key=f'catalog_source_{dataset["path_key"]}',
        )

    with st.expander("更新と再現"):
        st.code(
            "\n".join(
                [
                    "source .venv/bin/activate",
                    "python prepare_history.py",
                    "python prepare_population_factors.py",
                    "python validate_project.py",
                    "python -m unittest discover -s tests -v",
                    "python -m streamlit run app.py",
                ]
            ),
            language="bash",
        )
        st.caption(
            "取得元の更新時期は資料ごとに異なる。更新後は検証とテストを再実行する。"
        )
