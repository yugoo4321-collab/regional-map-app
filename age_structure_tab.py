from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import altair as alt
import pandas as pd
import pydeck as pdk
import streamlit as st


DATA_PATH = (
    Path(__file__).resolve().parent
    / "data"
    / "tokyo_age_structure_2026.csv"
)
GEOJSON_PATH = (
    Path(__file__).resolve().parent
    / "data"
    / "tokyo_wards.geojson"
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
/* AGE_ATLAS_V1 */
.age-atlas-head {
    display: flex;
    align-items: end;
    justify-content: space-between;
    gap: 1rem;
    padding-top: 0.2rem;
}
.age-atlas-kicker {
    color: #315F7B;
    font-size: 0.7rem;
    font-weight: 800;
    letter-spacing: 0.08em;
}
.age-atlas-title {
    color: #17263A;
    font-size: clamp(1.45rem, 2.6vw, 2rem);
    font-weight: 820;
    letter-spacing: -0.035em;
    margin-top: 0.18rem;
}
.age-atlas-note {
    max-width: 640px;
    color: #5B697B;
    font-size: 0.82rem;
    line-height: 1.65;
    text-align: right;
}
.age-atlas-summary {
    padding: 0.78rem 0.9rem;
    margin: 0.7rem 0 0.9rem;
    border: 1px solid #D4DCE5;
    border-left: 4px solid #315F7B;
    border-radius: 7px;
    background: #FFFFFF;
    color: #3E4D60;
    line-height: 1.7;
}
.age-atlas-rank-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.65rem;
    margin: 0.7rem 0 1rem;
}
.age-atlas-rank-card {
    position: relative;
    min-height: 112px;
    overflow: hidden;
    padding: 0.8rem 0.86rem;
    border: 1px solid #D4DCE5;
    border-radius: 8px 11px 8px 10px;
    background: linear-gradient(145deg, #FFFFFF, #F6F8FA);
}
.age-atlas-rank-card::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0.82rem;
    width: 34px;
    height: 3px;
    border-radius: 0 0 3px 3px;
    background: #315F7B;
}
.age-atlas-rank-card:nth-child(2)::before {
    background: #A55D39;
}
.age-atlas-rank-card:nth-child(3)::before {
    background: #6D648D;
}
.age-atlas-rank {
    color: #7A8595;
    font-size: 0.68rem;
    font-weight: 760;
}
.age-atlas-ward {
    color: #17263A;
    font-size: 1.06rem;
    font-weight: 820;
    margin-top: 0.24rem;
}
.age-atlas-value {
    color: #566477;
    font-size: 0.79rem;
    line-height: 1.55;
    margin-top: 0.24rem;
}
@media (max-width: 760px) {
    .age-atlas-head {
        display: block;
    }
    .age-atlas-note {
        margin-top: 0.35rem;
        text-align: left;
    }
    .age-atlas-rank-grid {
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


@st.cache_data(show_spinner=False)
def load_age_geojson() -> dict:
    with GEOJSON_PATH.open(encoding="utf-8") as file:
        geojson = json.load(file)

    features = geojson.get("features", [])
    if len(features) != 23:
        raise ValueError(
            f"行政区域が23件ではなく{len(features)}件です"
        )
    return geojson


@st.cache_data(show_spinner=False)
def age_atlas_data(age_data: pd.DataFrame) -> pd.DataFrame:
    working = age_data.copy()
    totals = working.groupby("自治体")["総数"].transform("sum")
    working["構成比"] = (
        working["総数"]
        / totals.where(totals.ne(0))
        * 100
    )
    band_average = (
        working.groupby("年齢階級")["構成比"]
        .transform("mean")
    )
    working["23区平均差"] = (
        working["構成比"] - band_average
    )
    working["順位"] = (
        working.groupby("年齢階級")["構成比"]
        .rank(ascending=False, method="min")
        .astype(int)
    )
    return working


def selected_band_frame(
    age_data: pd.DataFrame,
    age_band: str,
) -> pd.DataFrame:
    selected = (
        age_atlas_data(age_data)
        .loc[lambda frame: frame["年齢階級"].eq(age_band)]
        .sort_values(["構成比", "自治体"], ascending=[False, True])
        .reset_index(drop=True)
    )
    if len(selected) != 23:
        raise ValueError(
            f"{age_band}のデータが23区ではなく{len(selected)}区です"
        )
    return selected


def _atlas_color(
    value: float,
    minimum: float,
    maximum: float,
) -> list[int]:
    denominator = max(maximum - minimum, 1e-9)
    ratio = min(max((value - minimum) / denominator, 0), 1)
    start = (228, 235, 242)
    end = (32, 90, 137)
    return [
        int(start[index] + (end[index] - start[index]) * ratio)
        for index in range(3)
    ] + [238]


def prepare_age_atlas_geojson(
    age_data: pd.DataFrame,
    age_band: str,
    selected_ward: str,
) -> dict:
    band = selected_band_frame(age_data, age_band)
    lookup = band.set_index("自治体コード").to_dict("index")
    minimum = float(band["構成比"].min())
    maximum = float(band["構成比"].max())

    prepared = copy.deepcopy(load_age_geojson())
    for feature in prepared["features"]:
        properties = feature.setdefault("properties", {})
        code = str(properties.get("N03_007", "")).zfill(5)
        row = lookup.get(code)

        if row is None:
            properties.update(
                {
                    "自治体": "不明",
                    "構成比表示": "—",
                    "平均との差表示": "—",
                    "順位表示": "—",
                    "fill_color": [224, 229, 235, 180],
                    "line_color": [255, 255, 255, 220],
                    "line_width": 1,
                }
            )
            continue

        ward = str(row["自治体"])
        is_selected = ward == selected_ward
        is_top_three = int(row["順位"]) <= 3

        properties.update(
            {
                "自治体": ward,
                "構成比表示": f"{float(row['構成比']):.2f}%",
                "平均との差表示": (
                    f"{float(row['23区平均差']):+.2f}pt"
                ),
                "順位表示": f"{int(row['順位'])}位",
                "fill_color": _atlas_color(
                    float(row["構成比"]),
                    minimum,
                    maximum,
                ),
                "line_color": (
                    [15, 23, 42, 255]
                    if is_selected
                    else (
                        [180, 83, 9, 255]
                        if is_top_three
                        else [255, 255, 255, 230]
                    )
                ),
                "line_width": (
                    5 if is_selected else (3 if is_top_three else 1)
                ),
            }
        )

    return prepared


def age_atlas_map(
    age_data: pd.DataFrame,
    age_band: str,
    selected_ward: str,
) -> pdk.Deck:
    layer = pdk.Layer(
        "GeoJsonLayer",
        data=prepare_age_atlas_geojson(
            age_data,
            age_band,
            selected_ward,
        ),
        pickable=True,
        stroked=True,
        filled=True,
        get_fill_color="properties.fill_color",
        get_line_color="properties.line_color",
        get_line_width="properties.line_width",
        line_width_min_pixels=1,
        auto_highlight=True,
        highlight_color=[245, 158, 11, 170],
    )
    return pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(
            latitude=35.69,
            longitude=139.745,
            zoom=10.45,
        ),
        layers=[layer],
        tooltip={
            "html": (
                "<div style='font-size:15px'><b>{自治体}</b></div>"
                "<div style='margin-top:6px'>構成比: "
                "<b>{構成比表示}</b></div>"
                "<div>23区平均差: {平均との差表示}</div>"
                "<div>{順位表示}</div>"
            )
        },
    )


def age_atlas_summary(
    age_data: pd.DataFrame,
    age_band: str,
    selected_ward: str,
) -> str:
    band = selected_band_frame(age_data, age_band)
    first = band.iloc[0]
    last = band.iloc[-1]
    selected = band.loc[
        band["自治体"].eq(selected_ward)
    ].iloc[0]
    gap = float(first["構成比"]) - float(last["構成比"])

    return (
        f"{age_band}の割合が最も高いのは"
        f"{first['自治体']}（{first['構成比']:.2f}%）。"
        f"最も低い{last['自治体']}との差は{gap:.2f}pt。"
        f"{selected_ward}は{int(selected['順位'])}位で、"
        f"23区平均より{float(selected['23区平均差']):+.2f}pt。"
    )


def age_atlas_cards_html(
    age_data: pd.DataFrame,
    age_band: str,
) -> str:
    top_three = selected_band_frame(
        age_data,
        age_band,
    ).head(3)
    cards: list[str] = []

    for index, row in top_three.iterrows():
        cards.append(
            '<article class="age-atlas-rank-card">'
            f'<div class="age-atlas-rank">{index + 1}</div>'
            f'<div class="age-atlas-ward">{row["自治体"]}</div>'
            f'<div class="age-atlas-value">'
            f'{float(row["構成比"]):.2f}% / '
            f'平均差 {float(row["23区平均差"]):+.2f}pt'
            "</div></article>"
        )

    return (
        '<div class="age-atlas-rank-grid">'
        + "".join(cards)
        + "</div>"
    )


def age_heatmap_chart(
    age_data: pd.DataFrame,
    selected_band: str,
) -> alt.Chart:
    working = age_atlas_data(age_data).copy()
    selected_order = (
        working.loc[
            working["年齢階級"].eq(selected_band)
        ]
        .sort_values("構成比", ascending=False)["自治体"]
        .tolist()
    )

    return (
        alt.Chart(working)
        .mark_rect(cornerRadius=2)
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
                "自治体:N",
                title=None,
                sort=selected_order,
            ),
            color=alt.Color(
                "23区平均差:Q",
                title="平均との差",
                scale=alt.Scale(
                    scheme="redblue",
                    reverse=True,
                    domainMid=0,
                ),
            ),
            tooltip=[
                alt.Tooltip("自治体:N"),
                alt.Tooltip("年齢階級:N"),
                alt.Tooltip("構成比:Q", format=".2f"),
                alt.Tooltip("23区平均差:Q", format="+.2f"),
                alt.Tooltip("順位:Q"),
            ],
        )
        .properties(height=520)
        .configure_view(strokeOpacity=0)
        .configure(background="transparent")
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


    st.divider()
    st.markdown(
        """
        <div class="age-atlas-head">
            <div>
                <div class="age-atlas-kicker">AGE ATLAS</div>
                <div class="age-atlas-title">年齢地図</div>
            </div>
            <div class="age-atlas-note">
                5歳階級を切り替え、区人口に占める割合を見る。
                色は人数ではなく構成比。
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    age_bands = (
        age_data[["年齢階級", "年齢開始"]]
        .drop_duplicates()
        .sort_values("年齢開始")["年齢階級"]
        .tolist()
    )
    default_band = age_bands[min(5, len(age_bands) - 1)]

    if (
        "age_atlas_band" not in st.session_state
        or st.session_state["age_atlas_band"] not in age_bands
    ):
        st.session_state["age_atlas_band"] = default_band

    current_index = age_bands.index(
        st.session_state["age_atlas_band"]
    )
    button_columns = st.columns([0.16, 0.16, 0.16, 0.52])

    with button_columns[0]:
        if st.button(
            "−5歳",
            use_container_width=True,
            disabled=current_index == 0,
            key="age_atlas_previous",
        ):
            st.session_state["age_atlas_band"] = age_bands[
                current_index - 1
            ]
            st.rerun()

    with button_columns[1]:
        if st.button(
            "＋5歳",
            use_container_width=True,
            disabled=current_index == len(age_bands) - 1,
            key="age_atlas_next",
        ):
            st.session_state["age_atlas_band"] = age_bands[
                current_index + 1
            ]
            st.rerun()

    with button_columns[2]:
        if st.button(
            "年代ガチャ",
            use_container_width=True,
            key="age_atlas_random",
        ):
            choices = [
                band
                for band in age_bands
                if band != st.session_state["age_atlas_band"]
            ]
            st.session_state["age_atlas_band"] = random.choice(
                choices
            )
            st.rerun()

    age_band = st.select_slider(
        "年齢階級",
        options=age_bands,
        key="age_atlas_band",
    )

    st.markdown(
        (
            '<div class="age-atlas-summary">'
            + age_atlas_summary(
                age_data,
                age_band,
                first_ward,
            )
            + "</div>"
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        age_atlas_cards_html(
            age_data,
            age_band,
        ),
        unsafe_allow_html=True,
    )

    atlas_map_column, atlas_heatmap_column = st.columns(
        [0.92, 1.08],
        gap="large",
    )
    with atlas_map_column:
        st.markdown(f"### {age_band}の分布")
        st.pydeck_chart(
            age_atlas_map(
                age_data,
                age_band,
                first_ward,
            ),
            use_container_width=True,
        )
        st.caption(
            "濃いほど構成比が高い。黒枠は見る区、茶色の枠は上位3区。"
        )

    with atlas_heatmap_column:
        st.markdown("### 23区×年齢階級")
        st.altair_chart(
            age_heatmap_chart(
                age_data,
                age_band,
            ),
            width="stretch",
        )
        st.caption(
            "各年齢階級の23区平均との差。"
            "選んだ年齢階級の順位で区を並べる。"
        )

    atlas_download = selected_band_frame(
        age_data,
        age_band,
    )[
        [
            "自治体コード",
            "自治体",
            "年齢階級",
            "総数",
            "構成比",
            "23区平均差",
            "順位",
        ]
    ]
    st.download_button(
        "この年代のデータを保存",
        data=atlas_download.to_csv(
            index=False
        ).encode("utf-8-sig"),
        file_name=f"tokyo23_age_atlas_{age_band}.csv",
        mime="text/csv",
        key="download_age_atlas",
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
