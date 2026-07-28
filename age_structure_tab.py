from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


DATA_PATH = (
    Path(__file__).resolve().parent
    / "data"
    / "tokyo_age_structure_2026.csv"
)

AGE_STYLE = """
<style>
.age-head {
    padding: 0.2rem 0 1rem;
    border-bottom: 1px solid #D5DDE5;
    margin-bottom: 1rem;
}
.age-title {
    color: #17263A;
    font-size: clamp(1.75rem, 3vw, 2.4rem);
    letter-spacing: -0.04em;
    margin: 0;
}
.age-lead {
    max-width: 850px;
    color: #566477;
    line-height: 1.75;
    margin: 0.6rem 0 0;
}
.age-note {
    padding: 0.82rem 0.95rem;
    border: 1px solid #D4DCE5;
    border-left: 4px solid #315F7B;
    border-radius: 7px;
    background: #FFFFFF;
    color: #3D4C5F;
    line-height: 1.7;
    margin: 0.75rem 0 1rem;
}
.age-difference-list {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.65rem;
    margin: 0.75rem 0 1rem;
}
.age-difference-card {
    position: relative;
    min-height: 108px;
    padding: 0.8rem 0.85rem;
    overflow: hidden;
    border: 1px solid #D4DCE5;
    border-radius: 8px 11px 8px 10px;
    background: linear-gradient(145deg, #FFFFFF, #F7F9FB);
}
.age-difference-card::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0.8rem;
    width: 34px;
    height: 3px;
    border-radius: 0 0 3px 3px;
    background: #315F7B;
}
.age-difference-card:nth-child(2)::before {
    background: #A55D39;
}
.age-difference-card:nth-child(3)::before {
    background: #6D648D;
}
.age-difference-label {
    color: #687487;
    font-size: 0.7rem;
    font-weight: 760;
}
.age-difference-band {
    color: #17263A;
    font-size: 1.03rem;
    font-weight: 800;
    margin-top: 0.28rem;
}
.age-difference-value {
    color: #4A586B;
    font-size: 0.78rem;
    line-height: 1.5;
    margin-top: 0.22rem;
}
@media (max-width: 760px) {
    .age-difference-list {
        grid-template-columns: 1fr;
    }
}
</style>
"""


@st.cache_data(show_spinner=False)
def load_age_data(path: str = str(DATA_PATH)) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype={"自治体コード": str})
    required = {
        "自治体コード",
        "自治体",
        "年",
        "年齢階級",
        "年齢開始",
        "総数",
        "男",
        "女",
        "日本人",
        "外国人",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(
            "年齢構成データの列が不足: "
            + ", ".join(sorted(missing))
        )
    return frame


@st.cache_data(show_spinner=False)
def build_age_summary(age_data: pd.DataFrame) -> pd.DataFrame:
    working = age_data.copy()
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
            総数=("総数", "sum"),
            外国人=("外国人", "sum"),
        )
    )
    summary = grouped.merge(
        totals,
        on="自治体",
        validate="one_to_one",
    )

    for column in ["0–14歳", "15–64歳", "65歳以上"]:
        summary[f"{column}割合"] = (
            summary[column] / summary["総数"] * 100
        )
    summary["外国人割合"] = (
        summary["外国人"] / summary["総数"] * 100
    )

    for column in [
        "0–14歳割合",
        "15–64歳割合",
        "65歳以上割合",
        "外国人割合",
    ]:
        summary[f"{column}順位"] = (
            summary[column]
            .rank(ascending=False, method="min")
            .astype(int)
        )

    return summary


@st.cache_data(show_spinner=False)
def age_share_data(age_data: pd.DataFrame) -> pd.DataFrame:
    working = age_data.copy()
    totals = working.groupby("自治体")["総数"].transform("sum")
    working["構成比"] = (
        working["総数"]
        / totals.where(totals.ne(0))
        * 100
    )
    return working


def pyramid_chart(
    age_data: pd.DataFrame,
    ward: str,
) -> alt.Chart:
    selected = (
        age_data.loc[age_data["自治体"].eq(ward)]
        .sort_values("年齢開始")
        .copy()
    )
    chart_data = pd.concat(
        [
            selected.assign(性別="男", 人口=-selected["男"]),
            selected.assign(性別="女", 人口=selected["女"]),
        ],
        ignore_index=True,
    )
    domain = selected["年齢階級"].tolist()

    bars = (
        alt.Chart(chart_data)
        .mark_bar(cornerRadiusEnd=3)
        .encode(
            x=alt.X(
                "人口:Q",
                title="人口（人）",
                axis=alt.Axis(
                    labelExpr="abs(datum.value)",
                    gridColor="#E7EBF0",
                ),
            ),
            y=alt.Y(
                "年齢階級:N",
                title=None,
                sort=domain,
            ),
            color=alt.Color(
                "性別:N",
                scale=alt.Scale(
                    domain=["男", "女"],
                    range=["#315F7B", "#A65F78"],
                ),
                legend=alt.Legend(title=None, orient="top"),
            ),
            tooltip=[
                alt.Tooltip("自治体:N"),
                alt.Tooltip("年齢階級:N"),
                alt.Tooltip("性別:N"),
                alt.Tooltip("人口:Q", format=",.0f"),
            ],
        )
    )
    zero = (
        alt.Chart(pd.DataFrame({"基準": [0]}))
        .mark_rule(color="#7B8795")
        .encode(x="基準:Q")
    )
    return (
        (bars + zero)
        .properties(height=570)
        .configure_view(strokeOpacity=0)
        .configure(background="transparent")
    )


def comparison_data(
    age_data: pd.DataFrame,
    first_ward: str,
    second_ward: str,
) -> pd.DataFrame:
    working = age_share_data(age_data)
    selected = working.loc[
        working["自治体"].isin([first_ward, second_ward]),
        ["自治体", "年齢階級", "年齢開始", "構成比"],
    ].copy()

    pivot = (
        selected.pivot(
            index=["年齢階級", "年齢開始"],
            columns="自治体",
            values="構成比",
        )
        .reset_index()
    )
    pivot["差"] = (
        pivot[first_ward]
        - pivot[second_ward]
    )
    return pivot.sort_values("年齢開始").reset_index(drop=True)


def composition_chart(
    age_data: pd.DataFrame,
    first_ward: str,
    second_ward: str,
) -> alt.Chart:
    working = age_share_data(age_data)
    selected = working.loc[
        working["自治体"].isin([first_ward, second_ward])
    ].copy()

    return (
        alt.Chart(selected)
        .mark_line(point=True, strokeWidth=2.4)
        .encode(
            x=alt.X(
                "年齢階級:N",
                title=None,
                sort=alt.SortField(
                    field="年齢開始",
                    order="ascending",
                ),
                axis=alt.Axis(labelAngle=-45),
            ),
            y=alt.Y(
                "構成比:Q",
                title="区人口に占める割合（%）",
                axis=alt.Axis(gridColor="#E7EBF0"),
            ),
            color=alt.Color(
                "自治体:N",
                scale=alt.Scale(
                    domain=[first_ward, second_ward],
                    range=["#315F7B", "#A55D39"],
                ),
                legend=alt.Legend(title=None, orient="top"),
            ),
            tooltip=[
                alt.Tooltip("自治体:N"),
                alt.Tooltip("年齢階級:N"),
                alt.Tooltip("構成比:Q", format=".2f"),
            ],
        )
        .properties(height=330)
        .configure_view(strokeOpacity=0)
        .configure(background="transparent")
    )


def difference_chart(
    age_data: pd.DataFrame,
    first_ward: str,
    second_ward: str,
) -> alt.Chart:
    chart_data = comparison_data(
        age_data,
        first_ward,
        second_ward,
    )
    return (
        alt.Chart(chart_data)
        .mark_bar(cornerRadiusEnd=3)
        .encode(
            x=alt.X(
                "年齢階級:N",
                title=None,
                sort=alt.SortField(
                    field="年齢開始",
                    order="ascending",
                ),
                axis=alt.Axis(labelAngle=-45),
            ),
            y=alt.Y(
                "差:Q",
                title=f"{first_ward} − {second_ward}（pt）",
                axis=alt.Axis(gridColor="#E7EBF0"),
            ),
            color=alt.condition(
                alt.datum.差 >= 0,
                alt.value("#315F7B"),
                alt.value("#A55D39"),
            ),
            tooltip=[
                alt.Tooltip("年齢階級:N"),
                alt.Tooltip(
                    first_ward,
                    type="quantitative",
                    format=".2f",
                ),
                alt.Tooltip(
                    second_ward,
                    type="quantitative",
                    format=".2f",
                ),
                alt.Tooltip("差:Q", format="+.2f"),
            ],
        )
        .properties(height=300)
        .configure_view(strokeOpacity=0)
        .configure(background="transparent")
    )


def nationality_chart(
    age_data: pd.DataFrame,
    first_ward: str,
    second_ward: str,
) -> alt.Chart:
    selected = (
        age_data.loc[
            age_data["自治体"].isin([first_ward, second_ward])
        ]
        .sort_values(["自治体", "年齢開始"])
        .copy()
    )
    selected["外国人割合"] = (
        selected["外国人"]
        / selected["総数"].where(selected["総数"].ne(0))
        * 100
    )

    return (
        alt.Chart(selected)
        .mark_line(point=True, strokeWidth=2.3)
        .encode(
            x=alt.X(
                "年齢階級:N",
                title=None,
                sort=alt.SortField(
                    field="年齢開始",
                    order="ascending",
                ),
                axis=alt.Axis(labelAngle=-45),
            ),
            y=alt.Y(
                "外国人割合:Q",
                title="年齢階級内の外国人割合（%）",
                axis=alt.Axis(gridColor="#E7EBF0"),
            ),
            color=alt.Color(
                "自治体:N",
                scale=alt.Scale(
                    domain=[first_ward, second_ward],
                    range=["#6D648D", "#B96A43"],
                ),
                legend=alt.Legend(title=None, orient="top"),
            ),
            tooltip=[
                alt.Tooltip("自治体:N"),
                alt.Tooltip("年齢階級:N"),
                alt.Tooltip("外国人割合:Q", format=".2f"),
                alt.Tooltip("外国人:Q", format=",.0f"),
            ],
        )
        .properties(height=310)
        .configure_view(strokeOpacity=0)
        .configure(background="transparent")
    )


def top_differences(
    age_data: pd.DataFrame,
    first_ward: str,
    second_ward: str,
    limit: int = 3,
) -> pd.DataFrame:
    comparison = comparison_data(
        age_data,
        first_ward,
        second_ward,
    ).copy()
    comparison["差の絶対値"] = comparison["差"].abs()
    return (
        comparison.nlargest(limit, "差の絶対値")
        .reset_index(drop=True)
    )


def difference_cards_html(
    age_data: pd.DataFrame,
    first_ward: str,
    second_ward: str,
) -> str:
    cards: list[str] = []
    for index, row in top_differences(
        age_data,
        first_ward,
        second_ward,
    ).iterrows():
        direction = (
            f"{first_ward}が多い"
            if row["差"] > 0
            else f"{second_ward}が多い"
        )
        cards.append(
            '<article class="age-difference-card">'
            f'<div class="age-difference-label">差 {index + 1}</div>'
            f'<div class="age-difference-band">{row["年齢階級"]}</div>'
            f'<div class="age-difference-value">'
            f'{direction}（{abs(float(row["差"])):.2f}pt）'
            "</div></article>"
        )
    return (
        '<div class="age-difference-list">'
        + "".join(cards)
        + "</div>"
    )


def finding_text(
    summary: pd.DataFrame,
    first_ward: str,
    second_ward: str,
) -> str:
    first = summary.loc[
        summary["自治体"].eq(first_ward)
    ].iloc[0]
    second = summary.loc[
        summary["自治体"].eq(second_ward)
    ].iloc[0]

    elderly_gap = (
        float(first["65歳以上割合"])
        - float(second["65歳以上割合"])
    )
    working_gap = (
        float(first["15–64歳割合"])
        - float(second["15–64歳割合"])
    )

    elderly_direction = (
        f"{first_ward}が{abs(elderly_gap):.1f}pt高い"
        if elderly_gap >= 0
        else f"{second_ward}が{abs(elderly_gap):.1f}pt高い"
    )
    working_direction = (
        f"{first_ward}が{abs(working_gap):.1f}pt高い"
        if working_gap >= 0
        else f"{second_ward}が{abs(working_gap):.1f}pt高い"
    )

    return (
        f"65歳以上は{elderly_direction}。"
        f"15–64歳は{working_direction}。"
        "下のグラフで、差が生まれる年代を5歳階級まで分ける。"
    )


def report_markdown(
    age_data: pd.DataFrame,
    summary: pd.DataFrame,
    first_ward: str,
    second_ward: str,
) -> str:
    first = summary.loc[
        summary["自治体"].eq(first_ward)
    ].iloc[0]
    second = summary.loc[
        summary["自治体"].eq(second_ward)
    ].iloc[0]
    differences = top_differences(
        age_data,
        first_ward,
        second_ward,
    )

    lines = [
        f"# 年齢構成比較：{first_ward} / {second_ward}",
        "",
        "基準日：2026年1月1日",
        "",
        "## 3区分",
        "",
        "| 指標 | " + first_ward + " | " + second_ward + " |",
        "|---|---:|---:|",
        (
            f"| 0–14歳 | {first['0–14歳割合']:.2f}%"
            f" | {second['0–14歳割合']:.2f}% |"
        ),
        (
            f"| 15–64歳 | {first['15–64歳割合']:.2f}%"
            f" | {second['15–64歳割合']:.2f}% |"
        ),
        (
            f"| 65歳以上 | {first['65歳以上割合']:.2f}%"
            f" | {second['65歳以上割合']:.2f}% |"
        ),
        (
            f"| 外国人 | {first['外国人割合']:.2f}%"
            f" | {second['外国人割合']:.2f}% |"
        ),
        "",
        "## 差が大きい年齢階級",
        "",
    ]

    for _, row in differences.iterrows():
        direction = (
            first_ward
            if row["差"] > 0
            else second_ward
        )
        lines.append(
            f"- {row['年齢階級']}："
            f"{direction}が{abs(float(row['差'])):.2f}pt多い"
        )

    lines.extend(
        [
            "",
            "## 注意",
            "",
            "- 構成比の差であり、良し悪しを示さない。",
            "- 年齢構成だけで人口変化の原因は断定しない。",
            "",
            "出典：東京都総務局統計部 "
            "「住民基本台帳による東京都の世帯と人口」第7表。",
        ]
    )
    return "\n".join(lines)


def render_age_structure_tab() -> None:
    st.markdown(AGE_STYLE, unsafe_allow_html=True)

    age_data = load_age_data()
    summary = build_age_summary(age_data)
    ward_names = summary["自治体"].tolist()

    st.markdown(
        """
        <div class="age-head">
            <h2 class="age-title">年齢構成</h2>
            <p class="age-lead">
                2026年1月1日の5歳階級別人口。
                2区の分布を、人数と構成比の両方で比べる。
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    select_columns = st.columns(2)
    with select_columns[0]:
        first_ward = st.selectbox(
            "見る区",
            ward_names,
            index=(
                ward_names.index("杉並区")
                if "杉並区" in ward_names
                else 0
            ),
            key="age_structure_first_ward",
        )
    with select_columns[1]:
        default_second = (
            ward_names.index("豊島区")
            if "豊島区" in ward_names
            else min(1, len(ward_names) - 1)
        )
        second_ward = st.selectbox(
            "比べる区",
            ward_names,
            index=default_second,
            key="age_structure_second_ward",
        )

    if first_ward == second_ward:
        st.info("異なる2区を選ぶ。")
        second_ward = next(
            ward for ward in ward_names
            if ward != first_ward
        )

    first = summary.loc[
        summary["自治体"].eq(first_ward)
    ].iloc[0]
    second = summary.loc[
        summary["自治体"].eq(second_ward)
    ].iloc[0]

    metric_columns = st.columns(4)
    for column, label in zip(
        [
            "0–14歳割合",
            "15–64歳割合",
            "65歳以上割合",
            "外国人割合",
        ],
        [
            "0–14歳",
            "15–64歳",
            "65歳以上",
            "外国人",
        ],
    ):
        index = [
            "0–14歳割合",
            "15–64歳割合",
            "65歳以上割合",
            "外国人割合",
        ].index(column)
        metric_columns[index].metric(
            label,
            f"{first[column]:.1f}%",
            f"{float(first[column]) - float(second[column]):+.1f}pt",
            help=f"差は{first_ward} − {second_ward}",
        )

    st.markdown(
        (
            '<div class="age-note">'
            + finding_text(
                summary,
                first_ward,
                second_ward,
            )
            + "</div>"
        ),
        unsafe_allow_html=True,
    )

    st.markdown("### どこが違う？")
    st.markdown(
        difference_cards_html(
            age_data,
            first_ward,
            second_ward,
        ),
        unsafe_allow_html=True,
    )

    first_column, second_column = st.columns(2, gap="large")
    with first_column:
        st.markdown(f"### {first_ward}の人口ピラミッド")
        st.altair_chart(
            pyramid_chart(age_data, first_ward),
            width="stretch",
        )
    with second_column:
        st.markdown(f"### {second_ward}の人口ピラミッド")
        st.altair_chart(
            pyramid_chart(age_data, second_ward),
            width="stretch",
        )

    st.divider()
    composition_column, difference_column = st.columns(
        2,
        gap="large",
    )
    with composition_column:
        st.markdown("### 年齢構成比")
        st.altair_chart(
            composition_chart(
                age_data,
                first_ward,
                second_ward,
            ),
            width="stretch",
        )
    with difference_column:
        st.markdown("### 構成比の差")
        st.altair_chart(
            difference_chart(
                age_data,
                first_ward,
                second_ward,
            ),
            width="stretch",
        )
        st.caption(
            f"青は{first_ward}が多く、"
            f"茶は{second_ward}が多い。"
            "良し悪しは示さない。"
        )

    st.markdown("### 年齢階級内の外国人割合")
    st.altair_chart(
        nationality_chart(
            age_data,
            first_ward,
            second_ward,
        ),
        width="stretch",
    )

    download_columns = st.columns([0.28, 0.72])
    with download_columns[0]:
        st.download_button(
            "比較メモを保存",
            data=report_markdown(
                age_data,
                summary,
                first_ward,
                second_ward,
            ).encode("utf-8"),
            file_name=(
                f"age_comparison_"
                f"{first_ward}_{second_ward}.md"
            ),
            mime="text/markdown",
            use_container_width=True,
            key="download_age_comparison_report",
        )
    with download_columns[1]:
        st.caption(
            "出典：東京都総務局統計部"
            "「住民基本台帳による東京都の世帯と人口」"
            "第7表（2026年1月1日現在）。"
        )
