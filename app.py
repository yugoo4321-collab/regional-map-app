from __future__ import annotations

import copy
import json
from pathlib import Path

import altair as alt
import pandas as pd
import pydeck as pdk
import streamlit as st

DATA_PATH = Path("data/tokyo_wards.csv")
GEOJSON_PATH = Path("data/tokyo_wards.geojson")

METRICS = {
    "高齢化率": {
        "column": "高齢化率",
        "label": "65歳以上人口割合",
        "axis_title": "高齢化率（%）",
    },
    "人口": {
        "column": "人口",
        "label": "人口",
        "axis_title": "人口（人）",
    },
    "人口密度": {
        "column": "人口密度",
        "label": "人口密度",
        "axis_title": "人口密度（人/km²）",
    },
}

PALETTE = [
    [232, 240, 248, 190],
    [198, 219, 239, 200],
    [158, 202, 225, 210],
    [107, 174, 214, 220],
    [49, 130, 189, 230],
    [8, 81, 156, 240],
]

st.set_page_config(
    page_title="東京23区 人口・高齢化ダッシュボード",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        .block-container {
            max-width: 1320px;
            padding-top: 2.2rem;
            padding-bottom: 3.5rem;
        }
        h1 {
            letter-spacing: -0.035em;
        }
        [data-testid="stMetric"] {
            min-height: 132px;
        }
        .map-legend {
            display: flex;
            align-items: flex-start;
            gap: 6px;
            margin: 0.25rem 0 0.75rem 0;
            flex-wrap: wrap;
        }
        .map-legend-item {
            width: 92px;
            font-size: 0.76rem;
            color: #5f6368;
        }
        .map-legend-swatch {
            height: 10px;
            border-radius: 3px;
            margin-bottom: 4px;
        }
        .small-note {
            color: #6b7280;
            font-size: 0.9rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def format_value(metric: str, value: float) -> str:
    if metric == "高齢化率":
        return f"{value:.2f}%"
    if metric == "人口":
        return f"{value:,.0f}人"
    return f"{value:,.0f}人/km²"


def color_for_value(value: float, minimum: float, maximum: float) -> list[int]:
    if maximum == minimum:
        return PALETTE[len(PALETTE) // 2]

    ratio = (value - minimum) / (maximum - minimum)
    index = min(int(ratio * len(PALETTE)), len(PALETTE) - 1)
    return PALETTE[index]


def iter_points(value):
    if (
        isinstance(value, list)
        and len(value) >= 2
        and isinstance(value[0], (int, float))
        and isinstance(value[1], (int, float))
    ):
        yield float(value[0]), float(value[1])
        return

    if isinstance(value, list):
        for item in value:
            yield from iter_points(item)


def geometry_center(feature: dict) -> tuple[float, float]:
    points = list(iter_points(feature["geometry"]["coordinates"]))
    if not points:
        return 139.74, 35.69

    longitudes = [point[0] for point in points]
    latitudes = [point[1] for point in points]
    return (
        (min(longitudes) + max(longitudes)) / 2,
        (min(latitudes) + max(latitudes)) / 2,
    )


@st.cache_data
def load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"{DATA_PATH} が見つかりません")

    data = pd.read_csv(DATA_PATH, dtype={"自治体コード": str})
    required_columns = {
        "自治体コード",
        "都道府県",
        "自治体",
        "面積_km2",
        "人口",
        "高齢化率",
        "人口密度",
    }
    missing_columns = required_columns - set(data.columns)

    if missing_columns:
        raise ValueError(f"CSVに必要な列がありません: {sorted(missing_columns)}")
    if len(data) != 23:
        raise ValueError(f"23区ではなく{len(data)}件のデータがあります")
    if data["自治体コード"].duplicated().any():
        raise ValueError("自治体コードが重複しています")

    for column in ["面積_km2", "人口", "高齢化率", "人口密度"]:
        data[column] = pd.to_numeric(data[column], errors="raise")

    return data.sort_values("自治体コード").reset_index(drop=True)


@st.cache_data
def load_geojson() -> dict:
    if not GEOJSON_PATH.exists():
        raise FileNotFoundError(f"{GEOJSON_PATH} が見つかりません")

    with GEOJSON_PATH.open(encoding="utf-8") as file:
        geojson = json.load(file)

    features = geojson.get("features", [])
    if len(features) != 23:
        raise ValueError(f"行政境界が23件ではなく{len(features)}件あります")

    return geojson


def prepare_map_geojson(
    source_geojson: dict,
    data: pd.DataFrame,
    metric: str,
    selected_ward: str,
) -> dict:
    metric_column = METRICS[metric]["column"]
    values = data.set_index("自治体コード").to_dict("index")
    minimum = float(data[metric_column].min())
    maximum = float(data[metric_column].max())
    prepared = copy.deepcopy(source_geojson)

    for feature in prepared["features"]:
        properties = feature.setdefault("properties", {})
        code = str(properties.get("N03_007", "")).zfill(5)
        row = values.get(code)

        if row is None:
            properties["fill_color"] = [210, 210, 210, 120]
            properties["line_color"] = [120, 120, 120, 180]
            properties["line_width"] = 1
            continue

        value = float(row[metric_column])
        is_selected = selected_ward == row["自治体"]
        properties.update(
            {
                "自治体": row["自治体"],
                "表示指標": METRICS[metric]["label"],
                "表示値": format_value(metric, value),
                "人口表示": f"{row['人口']:,.0f}人",
                "高齢化率表示": f"{row['高齢化率']:.2f}%",
                "人口密度表示": f"{row['人口密度']:,.0f}人/km²",
                "fill_color": color_for_value(value, minimum, maximum),
                "line_color": [17, 24, 39, 255] if is_selected else [255, 255, 255, 225],
                "line_width": 4 if is_selected else 1,
            }
        )

    return prepared


def selected_view_state(geojson: dict, ward: str) -> pdk.ViewState:
    if ward == "23区全体":
        return pdk.ViewState(latitude=35.69, longitude=139.745, zoom=10.55)

    for feature in geojson["features"]:
        if feature.get("properties", {}).get("自治体") == ward:
            longitude, latitude = geometry_center(feature)
            return pdk.ViewState(latitude=latitude, longitude=longitude, zoom=11.85)

    return pdk.ViewState(latitude=35.69, longitude=139.745, zoom=10.55)


def legend_html(metric: str, minimum: float, maximum: float) -> str:
    values = [minimum + (maximum - minimum) * index / (len(PALETTE) - 1) for index in range(len(PALETTE))]
    items = []

    for color, value in zip(PALETTE, values):
        red, green, blue, _ = color
        items.append(
            "<div class='map-legend-item'>"
            f"<div class='map-legend-swatch' style='background: rgb({red}, {green}, {blue});'></div>"
            f"<div>{format_value(metric, value)}</div>"
            "</div>"
        )

    return "<div class='map-legend'>" + "".join(items) + "</div>"


def comparison_sentence(data: pd.DataFrame, ward: str, metric: str) -> str:
    column = METRICS[metric]["column"]
    value = float(data.loc[data["自治体"] == ward, column].iloc[0])
    median = float(data[column].median())
    difference = value - median
    direction = "上" if difference > 0 else "下" if difference < 0 else "同じ"

    if metric == "高齢化率":
        difference_text = f"{abs(difference):.2f}ポイント"
    elif metric == "人口":
        difference_text = f"{abs(difference):,.0f}人"
    else:
        difference_text = f"{abs(difference):,.0f}人/km²"

    if direction == "同じ":
        return f"{ward}は23区中央値と同じ水準です。"

    return f"{ward}は23区中央値より{difference_text}{direction}です。"


try:
    data = load_data()
    raw_geojson = load_geojson()
except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
    st.error(f"データを読み込めませんでした: {error}")
    st.stop()

st.title("東京23区 人口・高齢化ダッシュボード")
st.caption(
    "東京都の区市町村統計と行政境界データを組み合わせ、"
    "23区の人口構造を地図とグラフで比較します。"
)

control_left, control_right = st.columns([1.15, 0.85])
with control_left:
    selected_metric = st.radio(
        "地図・ランキングで見る指標",
        list(METRICS),
        horizontal=True,
    )
with control_right:
    selected_ward = st.selectbox(
        "注目する区",
        ["23区全体"] + data["自治体"].tolist(),
    )

metric_column = METRICS[selected_metric]["column"]
ranked = data.sort_values(metric_column, ascending=False).reset_index(drop=True)
ranked["順位"] = ranked.index + 1

total_population = int(data["人口"].sum())
weighted_aging_rate = float(
    (data["人口"] * data["高齢化率"]).sum() / total_population
)
highest_aging = data.loc[data["高齢化率"].idxmax()]
highest_density = data.loc[data["人口密度"].idxmax()]

if selected_ward == "23区全体":
    columns = st.columns(4)
    columns[0].metric("人口合計", f"{total_population:,}人", border=True)
    columns[1].metric("高齢化率（人口加重）", f"{weighted_aging_rate:.2f}%", border=True)
    columns[2].metric(
        "高齢化率が最も高い区",
        highest_aging["自治体"],
        delta=f"{highest_aging['高齢化率']:.2f}%",
        delta_color="off",
        border=True,
    )
    columns[3].metric(
        "人口密度が最も高い区",
        highest_density["自治体"],
        delta=f"{highest_density['人口密度']:,.0f}人/km²",
        delta_color="off",
        border=True,
    )
else:
    selected_row = data.loc[data["自治体"] == selected_ward].iloc[0]
    rank = int(ranked.loc[ranked["自治体"] == selected_ward, "順位"].iloc[0])

    columns = st.columns(4)
    columns[0].metric("人口", f"{selected_row['人口']:,.0f}人", border=True)
    columns[1].metric("高齢化率", f"{selected_row['高齢化率']:.2f}%", border=True)
    columns[2].metric("人口密度", f"{selected_row['人口密度']:,.0f}人/km²", border=True)
    columns[3].metric(
        f"{METRICS[selected_metric]['label']}の順位",
        f"23区中 {rank}位",
        border=True,
    )
    st.caption(comparison_sentence(data, selected_ward, selected_metric))

map_geojson = prepare_map_geojson(raw_geojson, data, selected_metric, selected_ward)
view_state = selected_view_state(map_geojson, selected_ward)

aging_top3 = data.nlargest(3, "高齢化率")["自治体"].tolist()
aging_bottom3 = data.nsmallest(3, "高齢化率")["自治体"].tolist()
density_aging_corr = float(data["人口密度"].corr(data["高齢化率"]))

with st.expander("データから読み取れる傾向"):
    st.write(
        f"高齢化率が高い3区は、{'・'.join(aging_top3)}です。"
        f"低い3区は、{'・'.join(aging_bottom3)}です。"
    )
    st.write(
        f"人口密度と高齢化率の相関係数は {density_aging_corr:.2f} です。"
        "相関は因果関係を示すものではないため、背景要因は別途確認する必要があります。"
    )

map_tab, comparison_tab, data_tab = st.tabs(["地図", "比較", "データ"])

with map_tab:
    st.subheader(f"{METRICS[selected_metric]['label']}の分布")
    st.caption(
        "区にカーソルを合わせると詳細を確認できます。"
        "注目する区は上の選択欄から変更できます。"
    )

    minimum = float(data[metric_column].min())
    maximum = float(data[metric_column].max())
    st.markdown(legend_html(selected_metric, minimum, maximum), unsafe_allow_html=True)

    layer = pdk.Layer(
        "GeoJsonLayer",
        data=map_geojson,
        pickable=True,
        stroked=True,
        filled=True,
        get_fill_color="properties.fill_color",
        get_line_color="properties.line_color",
        get_line_width="properties.line_width",
        line_width_min_pixels=1,
        auto_highlight=True,
        highlight_color=[245, 158, 11, 190],
    )

    deck = pdk.Deck(
        map_style=None,
        initial_view_state=view_state,
        layers=[layer],
        tooltip={
            "html": (
                "<b>{自治体}</b><br/>"
                "{表示指標}: {表示値}<br/>"
                "人口: {人口表示}<br/>"
                "高齢化率: {高齢化率表示}<br/>"
                "人口密度: {人口密度表示}"
            ),
            "style": {"backgroundColor": "#1f2937", "color": "white"},
        },
    )

    st.pydeck_chart(deck, width="stretch", height=560)
    st.caption(
        "統計値は2026年版、行政境界は2023年1月1日時点です。"
        "境界データは地理的な比較にのみ使用しています。"
    )

with comparison_tab:
    left, right = st.columns([1.03, 0.97])

    with left:
        st.subheader(f"{METRICS[selected_metric]['label']}ランキング")
        chart_data = data.sort_values(metric_column, ascending=False)
        median_value = float(data[metric_column].median())

        bars = (
            alt.Chart(chart_data)
            .mark_bar(cornerRadiusEnd=3)
            .encode(
                x=alt.X(
                    f"{metric_column}:Q",
                    title=METRICS[selected_metric]["axis_title"],
                ),
                y=alt.Y("自治体:N", sort="-x", title=None),
                color=alt.condition(
                    alt.datum.自治体 == selected_ward,
                    alt.value("#F59E0B"),
                    alt.value("#4C78A8"),
                ),
                tooltip=[
                    alt.Tooltip("自治体:N"),
                    alt.Tooltip("人口:Q", format=","),
                    alt.Tooltip("高齢化率:Q", format=".2f"),
                    alt.Tooltip("人口密度:Q", format=",.0f"),
                ],
            )
            .properties(height=620)
        )

        median_rule = (
            alt.Chart(pd.DataFrame({"中央値": [median_value]}))
            .mark_rule(color="#6B7280", strokeDash=[5, 4])
            .encode(x=alt.X("中央値:Q"))
        )
        st.altair_chart(bars + median_rule, width="stretch")
        st.caption("破線は23区の中央値です。")

    with right:
        st.subheader("人口密度と高齢化率")
        scatter = (
            alt.Chart(data)
            .mark_circle(opacity=0.84, stroke="white", strokeWidth=1)
            .encode(
                x=alt.X("人口密度:Q", title="人口密度（人/km²）"),
                y=alt.Y("高齢化率:Q", title="高齢化率（%）", scale=alt.Scale(zero=False)),
                size=alt.Size("人口:Q", title="人口", scale=alt.Scale(range=[80, 900])),
                color=alt.condition(
                    alt.datum.自治体 == selected_ward,
                    alt.value("#F59E0B"),
                    alt.value("#4C78A8"),
                ),
                tooltip=[
                    alt.Tooltip("自治体:N"),
                    alt.Tooltip("人口:Q", format=","),
                    alt.Tooltip("高齢化率:Q", format=".2f"),
                    alt.Tooltip("人口密度:Q", format=",.0f"),
                ],
            )
            .properties(height=500)
            .interactive()
        )
        st.altair_chart(scatter, width="stretch")
        st.caption(
            "円の大きさは人口を示します。人口密度と高齢化率の関係を、"
            "区ごとに確認できます。"
        )

with data_tab:
    st.subheader("23区の統計一覧")

    table_data = data[
        ["自治体", "面積_km2", "人口", "高齢化率", "人口密度"]
    ].sort_values(metric_column, ascending=False).copy()
    table_data.insert(0, "順位", range(1, len(table_data) + 1))

    st.dataframe(
        table_data,
        hide_index=True,
        width="stretch",
        column_config={
            "順位": st.column_config.NumberColumn("順位", format="%d"),
            "自治体": st.column_config.TextColumn("区"),
            "面積_km2": st.column_config.NumberColumn("面積", format="%.2f km²"),
            "人口": st.column_config.NumberColumn("人口", format="localized"),
            "高齢化率": st.column_config.NumberColumn("高齢化率", format="%.2f%%"),
            "人口密度": st.column_config.NumberColumn("人口密度", format="localized"),
        },
    )

    csv_data = table_data.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "表示データをCSVで保存",
        data=csv_data,
        file_name="tokyo_23wards_statistics.csv",
        mime="text/csv",
        width="content",
    )

    with st.expander("データの出典と計算方法"):
        st.markdown(
            "- 統計：東京都『区市町村統計表（2026年）』\n"
            "- 行政境界：国土交通省『国土数値情報（行政区域データ）』をもとに"
            "NIIが加工した2023年1月1日時点のGeoJSON\n"
            "- 人口密度：人口 ÷ 面積（km²）で算出\n"
            "- 独自の総合スコアは作らず、公表値と単純な派生指標だけを表示"
        )
        st.markdown(
            "[東京都 区市町村統計表](https://www.toukei.metro.tokyo.lg.jp/kurasi/2026/ku26-23.htm)  "
            "／ [行政境界データ](https://geoshape.ex.nii.ac.jp/city/choropleth/13_city.html)"
        )
