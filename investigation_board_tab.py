from __future__ import annotations

from pathlib import Path
from typing import Any

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
CURRENT_PATH = ROOT / "data" / "tokyo_wards.csv"
HISTORY_PATH = ROOT / "data" / "tokyo_wards_history.csv"
FACTORS_PATH = ROOT / "data" / "tokyo_population_factors_2025.csv"
AGE_PATH = ROOT / "data" / "tokyo_age_structure_2026.csv"


BOARD_STYLE = """
<style>
.board-head {
    padding: 0.15rem 0 1rem;
    border-bottom: 1px solid #D5DDE5;
    margin-bottom: 1rem;
}
.board-title {
    color: #17263A;
    font-size: clamp(1.8rem, 3vw, 2.45rem);
    letter-spacing: -0.04em;
    margin: 0;
}
.board-lead {
    max-width: 860px;
    color: #566477;
    line-height: 1.75;
    margin: 0.58rem 0 0;
}
.board-question {
    padding: 0.78rem 0.9rem;
    margin: 0.7rem 0 0.95rem;
    border: 1px solid #D2DBE4;
    border-left: 4px solid #315F7B;
    border-radius: 7px;
    background: #FFFFFF;
    color: #3D4C5F;
    line-height: 1.7;
}
.board-ward-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.72rem;
    margin: 0.75rem 0 1rem;
}
.board-ward-card {
    --board-accent: #315F7B;
    position: relative;
    min-height: 158px;
    overflow: hidden;
    padding: 0.92rem 0.95rem;
    border: 1px solid #D3DCE5;
    border-radius: 8px 12px 8px 11px;
    background: linear-gradient(145deg, #FFFFFF, #F6F8FA);
}
.board-ward-card:nth-child(2) {
    --board-accent: #A55D39;
}
.board-ward-card:nth-child(3) {
    --board-accent: #6D648D;
}
.board-ward-card:nth-child(4) {
    --board-accent: #39725D;
}
.board-ward-card::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0.88rem;
    width: 38px;
    height: 4px;
    border-radius: 0 0 4px 4px;
    background: var(--board-accent);
}
.board-ward-name {
    color: #17263A;
    font-size: 1.13rem;
    font-weight: 820;
    letter-spacing: -0.025em;
}
.board-ward-tag {
    display: inline-block;
    margin-top: 0.38rem;
    padding: 0.22rem 0.42rem;
    border: 1px solid #D5DDE5;
    border-radius: 4px 6px 4px 5px;
    background: #FFFFFF;
    color: var(--board-accent);
    font-size: 0.68rem;
    font-weight: 780;
}
.board-ward-lines {
    margin-top: 0.55rem;
    color: #566477;
    font-size: 0.76rem;
    line-height: 1.68;
}
.board-spread-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.65rem;
    margin: 0.7rem 0 1rem;
}
.board-spread-card {
    padding: 0.82rem 0.88rem;
    border: 1px solid #D4DCE5;
    border-radius: 8px;
    background: #FFFFFF;
}
.board-spread-rank {
    color: #7B8797;
    font-size: 0.68rem;
    font-weight: 760;
}
.board-spread-metric {
    color: #17263A;
    font-size: 1rem;
    font-weight: 800;
    margin-top: 0.22rem;
}
.board-spread-value {
    color: #566477;
    font-size: 0.76rem;
    line-height: 1.55;
    margin-top: 0.24rem;
}
.board-note {
    color: #627084;
    font-size: 0.78rem;
    line-height: 1.65;
}
@media (max-width: 1050px) {
    .board-ward-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}
@media (max-width: 720px) {
    .board-ward-grid,
    .board-spread-grid {
        grid-template-columns: 1fr;
    }
}
</style>
"""


METRIC_META: dict[str, dict[str, Any]] = {
    "人口": {
        "label": "人口",
        "unit": "人",
        "format": ",.0f",
        "higher": "人口が多い",
        "lower": "人口が少ない",
    },
    "高齢化率": {
        "label": "高齢化率",
        "unit": "%",
        "format": ".2f",
        "higher": "高齢化率が高い",
        "lower": "高齢化率が低い",
    },
    "人口密度": {
        "label": "人口密度",
        "unit": "人/km²",
        "format": ",.0f",
        "higher": "人口密度が高い",
        "lower": "人口密度が低い",
    },
    "人口増減率": {
        "label": "長期人口増減率",
        "unit": "%",
        "format": "+.2f",
        "higher": "人口増加が大きい",
        "lower": "人口減少が大きい",
    },
    "高齢化率変化": {
        "label": "高齢化率変化",
        "unit": "pt",
        "format": "+.2f",
        "higher": "高齢化率の上昇が大きい",
        "lower": "高齢化率の上昇が小さい",
    },
    "人口増減": {
        "label": "2025年の人口増減",
        "unit": "人",
        "format": "+,.0f",
        "higher": "直近の人口増が大きい",
        "lower": "直近の人口減が大きい",
    },
    "社会増減": {
        "label": "社会増減",
        "unit": "人",
        "format": "+,.0f",
        "higher": "転入超過が大きい",
        "lower": "転出超過が大きい",
    },
    "自然増減": {
        "label": "自然増減",
        "unit": "人",
        "format": "+,.0f",
        "higher": "自然減が小さい",
        "lower": "自然減が大きい",
    },
    "0–14歳割合": {
        "label": "0–14歳",
        "unit": "%",
        "format": ".2f",
        "higher": "子どもの割合が高い",
        "lower": "子どもの割合が低い",
    },
    "15–64歳割合": {
        "label": "15–64歳",
        "unit": "%",
        "format": ".2f",
        "higher": "生産年齢人口の割合が高い",
        "lower": "生産年齢人口の割合が低い",
    },
    "65歳以上割合": {
        "label": "65歳以上",
        "unit": "%",
        "format": ".2f",
        "higher": "65歳以上の割合が高い",
        "lower": "65歳以上の割合が低い",
    },
    "外国人割合": {
        "label": "外国人",
        "unit": "%",
        "format": ".2f",
        "higher": "外国人の割合が高い",
        "lower": "外国人の割合が低い",
    },
}


LENSES = {
    "全体": {
        "question": "規模、年齢、変化、人口移動を同じ画面で比べる。",
        "metrics": [
            "人口",
            "高齢化率",
            "人口密度",
            "人口増減率",
            "社会増減",
            "自然増減",
            "15–64歳割合",
            "外国人割合",
        ],
    },
    "若い世代": {
        "question": "子どもと働く世代が多い区は、人口変化や密度も似ているか。",
        "metrics": [
            "0–14歳割合",
            "15–64歳割合",
            "65歳以上割合",
            "人口増減率",
            "社会増減",
            "人口密度",
        ],
    },
    "人口の動き": {
        "question": "長期の増減と、2025年の社会増減・自然増減は同じ方向か。",
        "metrics": [
            "人口増減率",
            "人口増減",
            "社会増減",
            "自然増減",
            "高齢化率変化",
            "人口",
        ],
    },
    "高齢化": {
        "question": "高齢化率の現在値と変化は、人口増減や密度とどう重なるか。",
        "metrics": [
            "高齢化率",
            "65歳以上割合",
            "高齢化率変化",
            "人口増減率",
            "人口密度",
            "自然増減",
        ],
    },
    "国際性": {
        "question": "外国人割合が高い区は、働く世代・人口移動・密度に共通点があるか。",
        "metrics": [
            "外国人割合",
            "15–64歳割合",
            "社会増減",
            "人口増減率",
            "人口密度",
            "人口",
        ],
    },
}


@st.cache_data(show_spinner=False)
def load_board_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    current = pd.read_csv(
        CURRENT_PATH,
        dtype={"自治体コード": str},
    )
    history = pd.read_csv(
        HISTORY_PATH,
        dtype={"自治体コード": str},
    )
    factors = pd.read_csv(
        FACTORS_PATH,
        dtype={"自治体コード": str},
    )
    age = pd.read_csv(
        AGE_PATH,
        dtype={"自治体コード": str},
    )
    return current, history, factors, age


@st.cache_data(show_spinner=False)
def build_board_frame(
    current: pd.DataFrame,
    history: pd.DataFrame,
    factors: pd.DataFrame,
    age: pd.DataFrame,
) -> pd.DataFrame:
    ordered = history.sort_values(["自治体", "年"])
    first = (
        ordered.groupby("自治体", as_index=False)
        .first()[["自治体", "年", "人口", "高齢化率"]]
        .rename(
            columns={
                "年": "開始年",
                "人口": "開始人口",
                "高齢化率": "開始高齢化率",
            }
        )
    )
    last = (
        ordered.groupby("自治体", as_index=False)
        .last()[["自治体", "年", "人口", "高齢化率"]]
        .rename(
            columns={
                "年": "終了年",
                "人口": "終了人口",
                "高齢化率": "終了高齢化率",
            }
        )
    )
    changes = first.merge(
        last,
        on="自治体",
        validate="one_to_one",
    )
    changes["人口増減率"] = (
        (changes["終了人口"] - changes["開始人口"])
        / changes["開始人口"]
        * 100
    )
    changes["高齢化率変化"] = (
        changes["終了高齢化率"]
        - changes["開始高齢化率"]
    )

    age_working = age.copy()
    age_working["区分"] = pd.cut(
        age_working["年齢開始"],
        bins=[-1, 14, 64, 200],
        labels=["0–14歳", "15–64歳", "65歳以上"],
    )
    age_grouped = (
        age_working.groupby(
            ["自治体", "区分"],
            observed=True,
            as_index=False,
        )["総数"]
        .sum()
        .pivot(
            index="自治体",
            columns="区分",
            values="総数",
        )
        .reset_index()
    )
    age_totals = (
        age_working.groupby("自治体", as_index=False)
        .agg(
            年齢構成人口=("総数", "sum"),
            外国人=("外国人", "sum"),
        )
    )
    age_summary = age_grouped.merge(
        age_totals,
        on="自治体",
        validate="one_to_one",
    )
    for column in ["0–14歳", "15–64歳", "65歳以上"]:
        age_summary[f"{column}割合"] = (
            age_summary[column]
            / age_summary["年齢構成人口"]
            * 100
        )
    age_summary["外国人割合"] = (
        age_summary["外国人"]
        / age_summary["年齢構成人口"]
        * 100
    )

    frame = (
        current.merge(
            changes,
            on="自治体",
            how="left",
            validate="one_to_one",
            suffixes=("", "_経年"),
        )
        .merge(
            factors[
                [
                    "自治体",
                    "人口増減",
                    "社会増減",
                    "自然増減",
                    "その他増減",
                ]
            ],
            on="自治体",
            how="left",
            validate="one_to_one",
        )
        .merge(
            age_summary[
                [
                    "自治体",
                    "0–14歳割合",
                    "15–64歳割合",
                    "65歳以上割合",
                    "外国人割合",
                ]
            ],
            on="自治体",
            how="left",
            validate="one_to_one",
        )
    )
    return frame


def robust_scale(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    median = float(numeric.median())
    q1 = float(numeric.quantile(0.25))
    q3 = float(numeric.quantile(0.75))
    scale = q3 - q1
    if not np.isfinite(scale) or scale == 0:
        scale = float(numeric.std(ddof=0))
    if not np.isfinite(scale) or scale == 0:
        scale = 1.0
    return (numeric - median) / scale


def median_index_data(
    frame: pd.DataFrame,
    wards: list[str],
    metrics: list[str],
) -> pd.DataFrame:
    selected = frame.loc[
        frame["自治体"].isin(wards),
        ["自治体", *metrics],
    ].copy()
    rows: list[dict[str, Any]] = []

    for metric in metrics:
        median = float(frame[metric].median())
        if median == 0:
            scaled = robust_scale(frame[metric])
            lookup = pd.Series(
                scaled.values,
                index=frame["自治体"],
            )
            for ward in wards:
                rows.append(
                    {
                        "自治体": ward,
                        "指標": METRIC_META[metric]["label"],
                        "指数": 100 + float(lookup.loc[ward]) * 20,
                    }
                )
        else:
            for _, row in selected.iterrows():
                rows.append(
                    {
                        "自治体": row["自治体"],
                        "指標": METRIC_META[metric]["label"],
                        "指数": float(row[metric]) / median * 100,
                    }
                )

    return pd.DataFrame(rows)


def spread_table(
    frame: pd.DataFrame,
    wards: list[str],
    metrics: list[str],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    for metric in metrics:
        scaled = pd.Series(
            robust_scale(frame[metric]).values,
            index=frame["自治体"],
        )
        selected = scaled.loc[wards]
        max_ward = str(selected.idxmax())
        min_ward = str(selected.idxmin())
        rows.append(
            {
                "指標": metric,
                "表示名": METRIC_META[metric]["label"],
                "広がり": float(selected.max() - selected.min()),
                "最大区": max_ward,
                "最小区": min_ward,
                "最大値": float(
                    frame.loc[
                        frame["自治体"].eq(max_ward),
                        metric,
                    ].iloc[0]
                ),
                "最小値": float(
                    frame.loc[
                        frame["自治体"].eq(min_ward),
                        metric,
                    ].iloc[0]
                ),
            }
        )

    return (
        pd.DataFrame(rows)
        .sort_values(
            ["広がり", "表示名"],
            ascending=[False, True],
        )
        .reset_index(drop=True)
    )


def format_value(metric: str, value: float) -> str:
    meta = METRIC_META[metric]
    return (
        format(float(value), meta["format"])
        + meta["unit"]
    )


def ward_tag(
    frame: pd.DataFrame,
    ward: str,
    metrics: list[str],
) -> str:
    row = frame.loc[frame["自治体"].eq(ward)].iloc[0]
    scores = []
    for metric in metrics:
        scaled = robust_scale(frame[metric])
        value = float(
            pd.Series(
                scaled.values,
                index=frame["自治体"],
            ).loc[ward]
        )
        scores.append((abs(value), value, metric))

    _, direction, metric = max(scores)
    meta = METRIC_META[metric]
    return meta["higher"] if direction >= 0 else meta["lower"]


def ward_cards_html(
    frame: pd.DataFrame,
    wards: list[str],
    metrics: list[str],
) -> str:
    cards: list[str] = []

    for ward in wards:
        row = frame.loc[
            frame["自治体"].eq(ward)
        ].iloc[0]
        primary = metrics[:3]
        lines = "<br>".join(
            (
                f"{METRIC_META[metric]['label']} "
                f"{format_value(metric, row[metric])}"
            )
            for metric in primary
        )
        cards.append(
            '<article class="board-ward-card">'
            f'<div class="board-ward-name">{ward}</div>'
            f'<div class="board-ward-tag">'
            f'{ward_tag(frame, ward, metrics)}'
            "</div>"
            f'<div class="board-ward-lines">{lines}</div>'
            "</article>"
        )

    return (
        '<div class="board-ward-grid">'
        + "".join(cards)
        + "</div>"
    )


def spread_cards_html(
    frame: pd.DataFrame,
    wards: list[str],
    metrics: list[str],
) -> str:
    spreads = spread_table(
        frame,
        wards,
        metrics,
    ).head(3)
    cards: list[str] = []

    for index, row in spreads.iterrows():
        metric = str(row["指標"])
        cards.append(
            '<article class="board-spread-card">'
            f'<div class="board-spread-rank">差 {index + 1}</div>'
            f'<div class="board-spread-metric">{row["表示名"]}</div>'
            f'<div class="board-spread-value">'
            f'{row["最大区"]} {format_value(metric, row["最大値"])}<br>'
            f'{row["最小区"]} {format_value(metric, row["最小値"])}'
            "</div></article>"
        )

    return (
        '<div class="board-spread-grid">'
        + "".join(cards)
        + "</div>"
    )


def comparison_chart(
    frame: pd.DataFrame,
    wards: list[str],
    metrics: list[str],
) -> alt.Chart:
    chart_data = median_index_data(
        frame,
        wards,
        metrics,
    )
    baseline = (
        alt.Chart(pd.DataFrame({"基準": [100]}))
        .mark_rule(
            color="#7D8998",
            strokeDash=[5, 4],
        )
        .encode(x="基準:Q")
    )
    dots = (
        alt.Chart(chart_data)
        .mark_circle(
            size=145,
            stroke="#FFFFFF",
            strokeWidth=1.2,
        )
        .encode(
            x=alt.X(
                "指数:Q",
                title="23区中央値＝100",
                axis=alt.Axis(gridColor="#E7EBF0"),
            ),
            y=alt.Y(
                "指標:N",
                title=None,
                sort=[
                    METRIC_META[metric]["label"]
                    for metric in metrics
                ],
            ),
            color=alt.Color(
                "自治体:N",
                legend=alt.Legend(
                    title=None,
                    orient="top",
                ),
            ),
            tooltip=[
                alt.Tooltip("自治体:N"),
                alt.Tooltip("指標:N"),
                alt.Tooltip("指数:Q", format=".1f"),
            ],
        )
    )
    return (
        (dots + baseline)
        .properties(height=max(300, 46 * len(metrics)))
        .configure_view(strokeOpacity=0)
        .configure(background="transparent")
    )


def raw_table(
    frame: pd.DataFrame,
    wards: list[str],
    metrics: list[str],
) -> pd.DataFrame:
    selected = frame.loc[
        frame["自治体"].isin(wards),
        ["自治体", *metrics],
    ].copy()
    selected["自治体"] = pd.Categorical(
        selected["自治体"],
        categories=wards,
        ordered=True,
    )
    selected = selected.sort_values("自治体")
    selected = selected.rename(
        columns={
            metric: METRIC_META[metric]["label"]
            for metric in metrics
        }
    )
    return selected


def dataframe_to_markdown(frame: pd.DataFrame) -> str:
    """追加パッケージを使わずMarkdown表を作る。"""
    columns = [str(column) for column in frame.columns]

    def clean(value: object) -> str:
        if pd.isna(value):
            return ""
        return (
            str(value)
            .replace("|", "｜")
            .replace("\n", " ")
        )

    lines = [
        "| " + " | ".join(columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    for row in frame.itertuples(index=False, name=None):
        lines.append(
            "| " + " | ".join(clean(value) for value in row) + " |"
        )
    return "\n".join(lines)


def report_markdown(
    frame: pd.DataFrame,
    wards: list[str],
    lens: str,
    metrics: list[str],
    note: str,
) -> str:
    selected = raw_table(
        frame,
        wards,
        metrics,
    )
    spreads = spread_table(
        frame,
        wards,
        metrics,
    ).head(3)

    lines = [
        f"# 調査ボード：{lens}",
        "",
        f"対象：{' / '.join(wards)}",
        "",
        f"問い：{LENSES[lens]['question']}",
        "",
        "## 差が大きい指標",
        "",
    ]
    for _, row in spreads.iterrows():
        metric = str(row["指標"])
        lines.append(
            f"- {row['表示名']}："
            f"{row['最大区']} {format_value(metric, row['最大値'])} / "
            f"{row['最小区']} {format_value(metric, row['最小値'])}"
        )

    lines.extend(
        [
            "",
            "## 数値",
            "",
            dataframe_to_markdown(selected),
            "",
            "## メモ",
            "",
            note.strip() or "未記入",
            "",
            "## 注意",
            "",
            "- 中央値指数は23区中央値を100とした相対値。",
            "- 指標の差は因果や良し悪しを示さない。",
            "- 更新年はデータセットごとに異なる。",
        ]
    )
    return "\n".join(lines)


def render_investigation_board() -> None:
    st.markdown(
        BOARD_STYLE,
        unsafe_allow_html=True,
    )
    current, history, factors, age = load_board_data()
    frame = build_board_frame(
        current,
        history,
        factors,
        age,
    )
    ward_names = frame["自治体"].tolist()

    st.markdown(
        """
        <div class="board-head">
            <h2 class="board-title">調査ボード</h2>
            <p class="board-lead">
                2〜4区を固定し、見る指標だけを切り替える。
                差が大きい指標、共通点、元の数値を同じ画面に置く。
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "board_wards" not in st.session_state:
        st.session_state["board_wards"] = [
            "杉並区",
            "豊島区",
            "江東区",
        ]

    if st.button(
        "区を入れ替える",
        key="board_shuffle",
        help="現在と異なる3区を選びます",
    ):
        offset = int(
            st.session_state.get("board_shuffle_step", 0)
        )
        indexes = [
            (offset * 5 + 2) % 23,
            (offset * 5 + 9) % 23,
            (offset * 5 + 16) % 23,
        ]
        st.session_state["board_wards"] = [
            ward_names[index]
            for index in indexes
        ]
        st.session_state["board_shuffle_step"] = offset + 1
        st.rerun()

    control_columns = st.columns([1.05, 0.95], gap="large")
    with control_columns[0]:
        wards = st.multiselect(
            "比べる区",
            ward_names,
            key="board_wards",
            max_selections=4,
            help="2〜4区を選択",
        )
    with control_columns[1]:
        lens = st.radio(
            "見る切り口",
            list(LENSES),
            horizontal=True,
            key="board_lens",
        )

    if len(wards) < 2:
        st.info("2区以上を選ぶ。")
        return

    metrics = LENSES[lens]["metrics"]

    st.markdown(
        (
            '<div class="board-question">'
            + LENSES[lens]["question"]
            + "</div>"
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        ward_cards_html(
            frame,
            wards,
            metrics,
        ),
        unsafe_allow_html=True,
    )

    st.markdown("### 差が大きい指標")
    st.markdown(
        spread_cards_html(
            frame,
            wards,
            metrics,
        ),
        unsafe_allow_html=True,
    )

    chart_column, table_column = st.columns(
        [1.16, 0.84],
        gap="large",
    )
    with chart_column:
        st.markdown("### 23区中央値との距離")
        st.altair_chart(
            comparison_chart(
                frame,
                wards,
                metrics,
            ),
            width="stretch",
        )
        st.caption(
            "各指標の中央値を100とした相対値。"
            "単位の違う指標を直接足していない。"
        )

    with table_column:
        st.markdown("### 元の数値")
        table = raw_table(
            frame,
            wards,
            metrics,
        )
        st.dataframe(
            table,
            hide_index=True,
            width="stretch",
        )
        st.download_button(
            "比較データを保存",
            data=table.to_csv(
                index=False
            ).encode("utf-8-sig"),
            file_name=f"investigation_board_{lens}.csv",
            mime="text/csv",
            key="download_board_csv",
        )

    st.markdown("### 調査メモ")
    note = st.text_area(
        "気づいたこと",
        key="board_note",
        height=120,
        placeholder=(
            "例：人口規模は近いが、年齢構成と社会増減が違う。"
            "次は住宅費や世帯構成を確認する。"
        ),
        label_visibility="collapsed",
    )

    download_columns = st.columns([0.28, 0.72])
    with download_columns[0]:
        st.download_button(
            "ボードを保存",
            data=report_markdown(
                frame,
                wards,
                lens,
                metrics,
                note,
            ).encode("utf-8"),
            file_name=f"investigation_board_{lens}.md",
            mime="text/markdown",
            use_container_width=True,
            key="download_board_markdown",
        )
    with download_columns[1]:
        st.markdown(
            """
            <div class="board-note">
                メモはこのブラウザのセッション中だけ保持。
                保存ボタンでMarkdownへ書き出せる。
            </div>
            """,
            unsafe_allow_html=True,
        )
