from __future__ import annotations

from math import exp
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
CURRENT_PATH = ROOT / "data" / "tokyo_wards.csv"
HISTORY_PATH = ROOT / "data" / "tokyo_wards_history.csv"
FACTORS_PATH = ROOT / "data" / "tokyo_population_factors_2025.csv"
AGE_PATH = ROOT / "data" / "tokyo_age_structure_2026.csv"


BRIEF_STYLE = """
<style>
.brief-head {
    padding: 0.15rem 0 1rem;
    border-bottom: 1px solid #D5DDE5;
    margin-bottom: 1rem;
}
.brief-title {
    color: #17263A;
    font-size: clamp(1.8rem, 3vw, 2.45rem);
    letter-spacing: -0.04em;
    margin: 0;
}
.brief-lead {
    max-width: 850px;
    color: #566477;
    line-height: 1.75;
    margin: 0.58rem 0 0;
}
.brief-three-lines {
    margin: 0.8rem 0 1.1rem;
    padding: 0.95rem 1rem;
    border: 1px solid #D1DAE3;
    border-left: 4px solid #315F7B;
    border-radius: 7px;
    background: #FFFFFF;
}
.brief-three-lines p {
    margin: 0.26rem 0;
    color: #344357;
    line-height: 1.65;
}
.brief-three-lines strong {
    color: #17263A;
}
.brief-similar-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.7rem;
    margin: 0.65rem 0 1rem;
}
.brief-similar-card {
    position: relative;
    min-height: 116px;
    padding: 0.82rem 0.9rem;
    overflow: hidden;
    border: 1px solid #D3DCE5;
    border-radius: 8px 11px 8px 10px;
    background:
        linear-gradient(145deg, #FFFFFF, #F6F8FA);
}
.brief-similar-card::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0.85rem;
    width: 34px;
    height: 3px;
    background: #315F7B;
    border-radius: 0 0 3px 3px;
}
.brief-similar-card:nth-child(2)::before {
    background: #A55D39;
}
.brief-similar-card:nth-child(3)::before {
    background: #6D648D;
}
.brief-similar-rank {
    color: #788496;
    font-size: 0.68rem;
    font-weight: 760;
}
.brief-similar-name {
    color: #17263A;
    font-size: 1.05rem;
    font-weight: 800;
    margin-top: 0.25rem;
}
.brief-similar-note {
    color: #59687B;
    font-size: 0.78rem;
    line-height: 1.55;
    margin-top: 0.28rem;
}
.brief-caution {
    padding: 0.75rem 0.9rem;
    border-top: 1px solid #D7DFE7;
    border-bottom: 1px solid #D7DFE7;
    color: #5C6A7C;
    font-size: 0.82rem;
    line-height: 1.7;
    margin-top: 1rem;
}
@media (max-width: 760px) {
    .brief-similar-grid {
        grid-template-columns: 1fr;
    }
}
</style>
"""


@st.cache_data(show_spinner=False)
def load_brief_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    current = pd.read_csv(CURRENT_PATH, dtype={"自治体コード": str})
    history = pd.read_csv(HISTORY_PATH, dtype={"自治体コード": str})
    factors = pd.read_csv(FACTORS_PATH, dtype={"自治体コード": str})
    age = pd.read_csv(AGE_PATH, dtype={"自治体コード": str})
    return current, history, factors, age


@st.cache_data(show_spinner=False)
def history_summary(history: pd.DataFrame) -> pd.DataFrame:
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
    result = first.merge(last, on="自治体", validate="one_to_one")
    result["人口増減率"] = (
        (result["終了人口"] - result["開始人口"])
        / result["開始人口"]
        * 100
    )
    result["高齢化率変化"] = (
        result["終了高齢化率"] - result["開始高齢化率"]
    )
    return result


@st.cache_data(show_spinner=False)
def age_summary(age: pd.DataFrame) -> pd.DataFrame:
    working = age.copy()
    working["区分"] = pd.cut(
        working["年齢開始"],
        bins=[-1, 14, 64, 200],
        labels=["0–14歳", "15–64歳", "65歳以上"],
    )
    grouped = (
        working.groupby(
            ["自治体", "区分"],
            observed=True,
            as_index=False,
        )["総数"]
        .sum()
        .pivot(index="自治体", columns="区分", values="総数")
        .reset_index()
    )
    totals = (
        working.groupby("自治体", as_index=False)
        .agg(
            年齢構成人口=("総数", "sum"),
            外国人=("外国人", "sum"),
        )
    )
    result = grouped.merge(
        totals,
        on="自治体",
        validate="one_to_one",
    )
    for column in ["0–14歳", "15–64歳", "65歳以上"]:
        result[f"{column}割合"] = (
            result[column] / result["年齢構成人口"] * 100
        )
    result["外国人割合"] = (
        result["外国人"] / result["年齢構成人口"] * 100
    )
    return result


@st.cache_data(show_spinner=False)
def merged_brief_frame(
    current: pd.DataFrame,
    history: pd.DataFrame,
    factors: pd.DataFrame,
    age: pd.DataFrame,
) -> pd.DataFrame:
    frame = (
        current.merge(
            history_summary(history),
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
                    "出生数",
                    "死亡数",
                ]
            ],
            on="自治体",
            how="left",
            validate="one_to_one",
        )
        .merge(
            age_summary(age),
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


def similarity_table(frame: pd.DataFrame, ward: str) -> pd.DataFrame:
    features = [
        "人口",
        "高齢化率",
        "人口密度",
        "人口増減率",
        "高齢化率変化",
        "社会増減",
        "自然増減",
        "15–64歳割合",
        "65歳以上割合",
        "外国人割合",
    ]
    working = frame[["自治体", *features]].copy()
    scaled = pd.DataFrame(
        {
            feature: robust_scale(working[feature])
            for feature in features
        }
    )
    scaled.insert(0, "自治体", working["自治体"].values)

    target = scaled.loc[scaled["自治体"].eq(ward), features].iloc[0]
    scaled["距離"] = np.sqrt(
        ((scaled[features] - target) ** 2).sum(axis=1)
    )
    scaled["近さ"] = scaled["距離"].map(
        lambda value: round(100 * exp(-float(value) / 3), 0)
    )
    return (
        scaled.loc[~scaled["自治体"].eq(ward)]
        .sort_values(["距離", "自治体"])
        .reset_index(drop=True)
    )


def median_index_chart(frame: pd.DataFrame, ward: str) -> alt.Chart:
    row = frame.loc[frame["自治体"].eq(ward)].iloc[0]
    metrics = [
        ("人口", "人口"),
        ("高齢化率", "高齢化率"),
        ("人口密度", "人口密度"),
        ("15–64歳割合", "15–64歳"),
        ("外国人割合", "外国人"),
    ]
    rows = []
    for column, label in metrics:
        median = float(frame[column].median())
        rows.append(
            {
                "指標": label,
                "指数": float(row[column]) / median * 100,
            }
        )
    chart_data = pd.DataFrame(rows)

    bars = (
        alt.Chart(chart_data)
        .mark_bar(cornerRadiusEnd=4, height=28)
        .encode(
            x=alt.X(
                "指数:Q",
                title="23区中央値＝100",
                axis=alt.Axis(gridColor="#E7EBF0"),
            ),
            y=alt.Y(
                "指標:N",
                title=None,
                sort=[label for _, label in metrics],
            ),
            color=alt.condition(
                alt.datum.指数 >= 100,
                alt.value("#315F7B"),
                alt.value("#A55D39"),
            ),
            tooltip=[
                alt.Tooltip("指標:N"),
                alt.Tooltip("指数:Q", format=".1f"),
            ],
        )
    )
    baseline = (
        alt.Chart(pd.DataFrame({"基準": [100]}))
        .mark_rule(color="#7D8998", strokeDash=[5, 4])
        .encode(x="基準:Q")
    )
    return (
        (bars + baseline)
        .properties(height=300)
        .configure_view(strokeOpacity=0)
        .configure(background="transparent")
    )


def population_history_chart(history: pd.DataFrame, ward: str) -> alt.Chart:
    selected = (
        history.loc[history["自治体"].eq(ward)]
        .sort_values("年")
        .copy()
    )
    first_population = float(selected["人口"].iloc[0])
    selected["人口指数"] = selected["人口"] / first_population * 100

    return (
        alt.Chart(selected)
        .mark_line(point=True, strokeWidth=2.6, color="#315F7B")
        .encode(
            x=alt.X("年:O", title=None),
            y=alt.Y(
                "人口指数:Q",
                title=f"{int(selected['年'].min())}年＝100",
                axis=alt.Axis(gridColor="#E7EBF0"),
            ),
            tooltip=[
                alt.Tooltip("年:O"),
                alt.Tooltip("人口:Q", format=",.0f"),
                alt.Tooltip("人口指数:Q", format=".1f"),
            ],
        )
        .properties(height=260)
        .configure_view(strokeOpacity=0)
        .configure(background="transparent")
    )


def aging_history_chart(history: pd.DataFrame, ward: str) -> alt.Chart:
    selected = (
        history.loc[history["自治体"].eq(ward)]
        .sort_values("年")
        .copy()
    )
    return (
        alt.Chart(selected)
        .mark_line(point=True, strokeWidth=2.6, color="#A55D39")
        .encode(
            x=alt.X("年:O", title=None),
            y=alt.Y(
                "高齢化率:Q",
                title="高齢化率（%）",
                scale=alt.Scale(zero=False),
                axis=alt.Axis(gridColor="#E7EBF0"),
            ),
            tooltip=[
                alt.Tooltip("年:O"),
                alt.Tooltip("高齢化率:Q", format=".2f"),
            ],
        )
        .properties(height=260)
        .configure_view(strokeOpacity=0)
        .configure(background="transparent")
    )


def factor_chart(frame: pd.DataFrame, ward: str) -> alt.Chart:
    row = frame.loc[frame["自治体"].eq(ward)].iloc[0]
    chart_data = pd.DataFrame(
        {
            "要因": ["社会増減", "自然増減", "その他増減"],
            "人数": [
                float(row["社会増減"]),
                float(row["自然増減"]),
                float(row["その他増減"]),
            ],
        }
    )
    bars = (
        alt.Chart(chart_data)
        .mark_bar(cornerRadiusEnd=4, height=30)
        .encode(
            x=alt.X(
                "人数:Q",
                title="人口への寄与（人）",
                axis=alt.Axis(gridColor="#E7EBF0"),
            ),
            y=alt.Y(
                "要因:N",
                title=None,
                sort=["社会増減", "自然増減", "その他増減"],
            ),
            color=alt.condition(
                alt.datum.人数 >= 0,
                alt.value("#315F7B"),
                alt.value("#A55D39"),
            ),
            tooltip=[
                alt.Tooltip("要因:N"),
                alt.Tooltip("人数:Q", format="+,.0f"),
            ],
        )
    )
    zero = (
        alt.Chart(pd.DataFrame({"基準": [0]}))
        .mark_rule(color="#7D8998", strokeDash=[4, 4])
        .encode(x="基準:Q")
    )
    return (
        (bars + zero)
        .properties(height=270)
        .configure_view(strokeOpacity=0)
        .configure(background="transparent")
    )


def age_composition_chart(frame: pd.DataFrame, ward: str) -> alt.Chart:
    row = frame.loc[frame["自治体"].eq(ward)].iloc[0]
    chart_data = pd.DataFrame(
        {
            "区分": ["0–14歳", "15–64歳", "65歳以上"],
            "割合": [
                float(row["0–14歳割合"]),
                float(row["15–64歳割合"]),
                float(row["65歳以上割合"]),
            ],
            "順序": [1, 2, 3],
        }
    )
    return (
        alt.Chart(chart_data)
        .mark_bar(cornerRadius=4)
        .encode(
            x=alt.X("割合:Q", title="構成比（%）", stack="normalize"),
            y=alt.value(24),
            color=alt.Color(
                "区分:N",
                scale=alt.Scale(
                    domain=["0–14歳", "15–64歳", "65歳以上"],
                    range=["#6D92B0", "#315F7B", "#A55D39"],
                ),
                legend=alt.Legend(title=None, orient="top"),
            ),
            order=alt.Order("順序:Q"),
            tooltip=[
                alt.Tooltip("区分:N"),
                alt.Tooltip("割合:Q", format=".2f"),
            ],
        )
        .properties(height=120)
        .configure_view(strokeOpacity=0)
        .configure(background="transparent")
    )


def three_lines(frame: pd.DataFrame, ward: str) -> tuple[str, str, str]:
    row = frame.loc[frame["自治体"].eq(ward)].iloc[0]
    medians = frame.median(numeric_only=True)

    aging_position = (
        "高め"
        if row["高齢化率"] > medians["高齢化率"]
        else "低め"
    )
    density_position = (
        "高め"
        if row["人口密度"] > medians["人口密度"]
        else "低め"
    )
    population_direction = (
        "増加"
        if row["人口増減率"] > 0
        else "減少"
    )
    factor_direction = (
        "社会増が自然減を上回る"
        if row["社会増減"] > 0
        and row["自然増減"] < 0
        and row["人口増減"] > 0
        else (
            "社会増が人口を押し上げる"
            if row["社会増減"] > 0
            else "社会減が人口を押し下げる"
        )
    )

    first = (
        f"現在：高齢化率は23区中央値より{aging_position}、"
        f"人口密度は{density_position}。"
    )
    second = (
        f"長期：{int(row['開始年'])}→{int(row['終了年'])}年で"
        f"人口は{population_direction}{abs(float(row['人口増減率'])):.1f}%。"
    )
    third = (
        f"直近：2025年は{factor_direction}。"
        f"人口増減は{float(row['人口増減']):+,.0f}人。"
    )
    return first, second, third


def similar_cards_html(
    frame: pd.DataFrame,
    ward: str,
) -> str:
    similar = similarity_table(frame, ward).head(3)
    cards = []
    for index, row in similar.iterrows():
        source = frame.loc[
            frame["自治体"].eq(row["自治体"])
        ].iloc[0]
        cards.append(
            '<article class="brief-similar-card">'
            f'<div class="brief-similar-rank">{index + 1}</div>'
            f'<div class="brief-similar-name">{row["自治体"]}</div>'
            f'<div class="brief-similar-note">'
            f'近さ {int(row["近さ"])} / '
            f'高齢化率 {source["高齢化率"]:.1f}% / '
            f'人口増減率 {source["人口増減率"]:+.1f}%'
            "</div></article>"
        )
    return '<div class="brief-similar-grid">' + "".join(cards) + "</div>"


def report_markdown(
    frame: pd.DataFrame,
    ward: str,
) -> str:
    row = frame.loc[frame["自治体"].eq(ward)].iloc[0]
    lines = three_lines(frame, ward)
    similar = similarity_table(frame, ward).head(3)

    result = [
        f"# {ward} 区レポート",
        "",
        "## 3行で読む",
        "",
        *[f"- {line}" for line in lines],
        "",
        "## 現在値",
        "",
        f"- 人口：{row['人口']:,.0f}人",
        f"- 高齢化率：{row['高齢化率']:.2f}%",
        f"- 人口密度：{row['人口密度']:,.0f}人/km²",
        f"- 15–64歳：{row['15–64歳割合']:.2f}%",
        f"- 65歳以上：{row['65歳以上割合']:.2f}%",
        f"- 外国人：{row['外国人割合']:.2f}%",
        "",
        "## 長期変化",
        "",
        (
            f"- 人口：{row['開始人口']:,.0f}人 → "
            f"{row['終了人口']:,.0f}人"
        ),
        f"- 人口増減率：{row['人口増減率']:+.2f}%",
        (
            f"- 高齢化率：{row['開始高齢化率']:.2f}% → "
            f"{row['終了高齢化率']:.2f}%"
        ),
        f"- 高齢化率変化：{row['高齢化率変化']:+.2f}pt",
        "",
        "## 2025年の人口動態",
        "",
        f"- 人口増減：{row['人口増減']:+,.0f}人",
        f"- 社会増減：{row['社会増減']:+,.0f}人",
        f"- 自然増減：{row['自然増減']:+,.0f}人",
        f"- その他増減：{row['その他増減']:+,.0f}人",
        "",
        "## 近い3区",
        "",
    ]
    for _, similar_row in similar.iterrows():
        result.append(
            f"- {similar_row['自治体']}（近さ {int(similar_row['近さ'])}）"
        )
    result.extend(
        [
            "",
            "## 注意",
            "",
            "- 近さは10指標の距離から作った探索用の値。",
            "- 相関、分類、近さは因果や良し悪しを示さない。",
            "- 更新年はデータセットごとに異なる。",
        ]
    )
    return "\n".join(result)


def render_ward_brief_tab() -> None:
    st.markdown(BRIEF_STYLE, unsafe_allow_html=True)
    current, history, factors, age = load_brief_data()
    frame = merged_brief_frame(
        current,
        history,
        factors,
        age,
    )
    ward_names = frame["自治体"].tolist()

    st.markdown(
        """
        <div class="brief-head">
            <h2 class="brief-title">区レポート</h2>
            <p class="brief-lead">
                現在値、長期変化、人口動態、年齢構成を1ページにまとめる。
                似た区は10指標の距離から探す。
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    ward = st.selectbox(
        "区",
        ward_names,
        index=ward_names.index("杉並区") if "杉並区" in ward_names else 0,
        key="ward_brief_selected_ward",
    )
    row = frame.loc[frame["自治体"].eq(ward)].iloc[0]

    metrics = st.columns(4)
    metrics[0].metric("人口", f"{row['人口']:,.0f}人")
    metrics[1].metric("高齢化率", f"{row['高齢化率']:.2f}%")
    metrics[2].metric(
        "人口増減率",
        f"{row['人口増減率']:+.2f}%",
        f"{int(row['開始年'])}→{int(row['終了年'])}",
    )
    metrics[3].metric(
        "2025年の増減",
        f"{row['人口増減']:+,.0f}人",
    )

    first, second, third = three_lines(frame, ward)
    st.markdown(
        (
            '<section class="brief-three-lines">'
            f"<p><strong>1</strong>　{first}</p>"
            f"<p><strong>2</strong>　{second}</p>"
            f"<p><strong>3</strong>　{third}</p>"
            "</section>"
        ),
        unsafe_allow_html=True,
    )

    index_column, age_column = st.columns([1.08, 0.92], gap="large")
    with index_column:
        st.markdown("### 23区の中でどこにいるか")
        st.altair_chart(
            median_index_chart(frame, ward),
            width="stretch",
        )
    with age_column:
        st.markdown("### 年齢3区分")
        st.altair_chart(
            age_composition_chart(frame, ward),
            width="stretch",
        )
        st.caption(
            f"0–14歳 {row['0–14歳割合']:.1f}% / "
            f"15–64歳 {row['15–64歳割合']:.1f}% / "
            f"65歳以上 {row['65歳以上割合']:.1f}%"
        )

        st.markdown("### 2025年の人口動態")
        st.altair_chart(
            factor_chart(frame, ward),
            width="stretch",
        )

    st.divider()
    population_column, aging_column = st.columns(2, gap="large")
    with population_column:
        st.markdown("### 人口の推移")
        st.altair_chart(
            population_history_chart(history, ward),
            width="stretch",
        )
    with aging_column:
        st.markdown("### 高齢化率の推移")
        st.altair_chart(
            aging_history_chart(history, ward),
            width="stretch",
        )

    st.markdown("### 近い3区")
    st.markdown(
        similar_cards_html(frame, ward),
        unsafe_allow_html=True,
    )
    st.caption(
        "人口、密度、高齢化、長期変化、人口動態、年齢構成の10指標を使用。"
    )

    download_columns = st.columns([0.28, 0.72])
    with download_columns[0]:
        st.download_button(
            "区レポートを保存",
            data=report_markdown(frame, ward).encode("utf-8"),
            file_name=f"ward_brief_{ward}.md",
            mime="text/markdown",
            use_container_width=True,
            key="download_ward_brief",
        )
    with download_columns[1]:
        st.markdown(
            """
            <div class="brief-caution">
                相関、分類、近さは因果や良し悪しを示さない。
                更新年はデータセットごとに異なる。
            </div>
            """,
            unsafe_allow_html=True,
        )
