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
</style>
"""


@st.cache_data(show_spinner=False)
def load_age_data(path: str = str(DATA_PATH)) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype={"自治体コード": str})
    required = {
        "自治体コード", "自治体", "年", "年齢階級", "年齢開始",
        "総数", "男", "女", "日本人", "外国人",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(
            "年齢構成データの列が不足: " + ", ".join(sorted(missing))
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
        .agg(総数=("総数", "sum"), 外国人=("外国人", "sum"))
    )
    summary = grouped.merge(totals, on="自治体", validate="one_to_one")

    for column in ["0–14歳", "15–64歳", "65歳以上"]:
        summary[f"{column}割合"] = summary[column] / summary["総数"] * 100
    summary["外国人割合"] = summary["外国人"] / summary["総数"] * 100

    for column in [
        "0–14歳割合", "15–64歳割合", "65歳以上割合", "外国人割合",
    ]:
        summary[f"{column}順位"] = (
            summary[column].rank(ascending=False, method="min").astype(int)
        )

    return summary


def pyramid_chart(age_data: pd.DataFrame, ward: str) -> alt.Chart:
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
            y=alt.Y("年齢階級:N", title=None, sort=domain),
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


def share_gap_data(age_data: pd.DataFrame, ward: str) -> pd.DataFrame:
    working = age_data.copy()
    totals = working.groupby("自治体")["総数"].transform("sum")
    working["構成比"] = working["総数"] / totals * 100

    selected = (
        working.loc[
            working["自治体"].eq(ward),
            ["年齢階級", "年齢開始", "構成比"],
        ]
        .rename(columns={"構成比": "選択区"})
    )
    averages = (
        working.groupby(
            ["年齢階級", "年齢開始"],
            as_index=False,
        )["構成比"]
        .mean()
        .rename(columns={"構成比": "23区平均"})
    )
    result = selected.merge(
        averages,
        on=["年齢階級", "年齢開始"],
        validate="one_to_one",
    )
    result["差"] = result["選択区"] - result["23区平均"]
    return result


def share_gap_chart(age_data: pd.DataFrame, ward: str) -> alt.Chart:
    chart_data = share_gap_data(age_data, ward)
    return (
        alt.Chart(chart_data)
        .mark_bar(cornerRadiusEnd=3)
        .encode(
            x=alt.X(
                "年齢階級:N",
                title=None,
                sort=alt.SortField(field="年齢開始", order="ascending"),
                axis=alt.Axis(labelAngle=-45),
            ),
            y=alt.Y(
                "差:Q",
                title="23区平均との差（pt）",
                axis=alt.Axis(gridColor="#E7EBF0"),
            ),
            color=alt.condition(
                alt.datum.差 >= 0,
                alt.value("#315F7B"),
                alt.value("#B96A43"),
            ),
            tooltip=[
                alt.Tooltip("年齢階級:N"),
                alt.Tooltip("選択区:Q", format=".2f"),
                alt.Tooltip("23区平均:Q", format=".2f"),
                alt.Tooltip("差:Q", format="+.2f"),
            ],
        )
        .properties(height=330)
        .configure_view(strokeOpacity=0)
        .configure(background="transparent")
    )


def nationality_chart(age_data: pd.DataFrame, ward: str) -> alt.Chart:
    selected = (
        age_data.loc[age_data["自治体"].eq(ward)]
        .sort_values("年齢開始")
        .copy()
    )
    selected["外国人割合"] = (
        selected["外国人"]
        / selected["総数"].where(selected["総数"].ne(0))
        * 100
    )
    return (
        alt.Chart(selected)
        .mark_line(point=True, strokeWidth=2.5, color="#6D648D")
        .encode(
            x=alt.X(
                "年齢階級:N",
                title=None,
                sort=alt.SortField(field="年齢開始", order="ascending"),
                axis=alt.Axis(labelAngle=-45),
            ),
            y=alt.Y(
                "外国人割合:Q",
                title="年齢階級内の外国人割合（%）",
                axis=alt.Axis(gridColor="#E7EBF0"),
            ),
            tooltip=[
                alt.Tooltip("年齢階級:N"),
                alt.Tooltip("外国人割合:Q", format=".2f"),
                alt.Tooltip("外国人:Q", format=",.0f"),
            ],
        )
        .properties(height=300)
        .configure_view(strokeOpacity=0)
        .configure(background="transparent")
    )


def finding_text(
    age_data: pd.DataFrame,
    summary: pd.DataFrame,
    ward: str,
) -> str:
    selected = summary.loc[summary["自治体"].eq(ward)].iloc[0]
    gaps = share_gap_data(age_data, ward)
    strongest = gaps.loc[gaps["差"].abs().idxmax()]
    direction = "多い" if strongest["差"] > 0 else "少ない"

    return (
        f"{ward}は、15–64歳が{selected['15–64歳割合']:.1f}%、"
        f"65歳以上が{selected['65歳以上割合']:.1f}%"
        f"（23区中{int(selected['65歳以上割合順位'])}位）。"
        f"平均との差が最も大きいのは{strongest['年齢階級']}で、"
        f"{abs(float(strongest['差'])):.2f}pt{direction}。"
    )


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
                男女の分布、23区平均との差、外国人割合を見る。
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    ward = st.selectbox(
        "区",
        ward_names,
        index=ward_names.index("杉並区") if "杉並区" in ward_names else 0,
        key="age_structure_ward",
    )
    selected = summary.loc[summary["自治体"].eq(ward)].iloc[0]

    columns = st.columns(4)
    columns[0].metric(
        "0–14歳",
        f"{selected['0–14歳割合']:.1f}%",
        f"23区中 {int(selected['0–14歳割合順位'])}位",
    )
    columns[1].metric(
        "15–64歳",
        f"{selected['15–64歳割合']:.1f}%",
        f"23区中 {int(selected['15–64歳割合順位'])}位",
    )
    columns[2].metric(
        "65歳以上",
        f"{selected['65歳以上割合']:.1f}%",
        f"23区中 {int(selected['65歳以上割合順位'])}位",
    )
    columns[3].metric(
        "外国人",
        f"{selected['外国人割合']:.1f}%",
        f"23区中 {int(selected['外国人割合順位'])}位",
    )

    st.markdown(
        f'<div class="age-note">{finding_text(age_data, summary, ward)}</div>',
        unsafe_allow_html=True,
    )

    pyramid_column, detail_column = st.columns([1.05, 0.95], gap="large")
    with pyramid_column:
        st.markdown("### 人口ピラミッド")
        st.altair_chart(pyramid_chart(age_data, ward), width="stretch")

    with detail_column:
        st.markdown("### 23区平均との差")
        st.altair_chart(share_gap_chart(age_data, ward), width="stretch")
        st.caption("青は平均より多く、茶は少ない。良し悪しは示さない。")

        st.markdown("### 年齢階級内の外国人割合")
        st.altair_chart(nationality_chart(age_data, ward), width="stretch")

    st.caption(
        "出典：東京都総務局統計部「住民基本台帳による東京都の世帯と人口」"
        "第7表（2026年1月1日現在）。"
    )
