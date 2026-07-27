from __future__ import annotations

import copy
import json
from html import escape
from pathlib import Path

import altair as alt
import pandas as pd
import pydeck as pdk
import streamlit as st

DATA_PATH = Path("data/tokyo_wards.csv")
GEOJSON_PATH = Path("data/tokyo_wards.geojson")
LIVE_APP_URL = "https://teeqy5f9waeoacgwccu4yc.streamlit.app"

METRICS = {
    "高齢化率": {
        "column": "高齢化率",
        "label": "65歳以上人口割合",
        "short_label": "高齢化率",
        "axis_title": "高齢化率（%）",
        "unit": "%",
    },
    "人口": {
        "column": "人口",
        "label": "人口",
        "short_label": "人口",
        "axis_title": "人口（人）",
        "unit": "人",
    },
    "人口密度": {
        "column": "人口密度",
        "label": "人口密度",
        "short_label": "人口密度",
        "axis_title": "人口密度（人/km²）",
        "unit": "人/km²",
    },
}

PALETTE = [
    [235, 244, 252, 210],
    [198, 222, 241, 215],
    [153, 201, 230, 220],
    [96, 165, 214, 225],
    [42, 119, 189, 235],
    [10, 67, 136, 245],
]

QUADRANT_COLORS = {
    "高齢・高密度": "#C2415D",
    "高齢・低密度": "#D97706",
    "若年・高密度": "#2563EB",
    "若年・低密度": "#64748B",
}

st.set_page_config(
    page_title="東京23区 都市構造ダッシュボード",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        :root {
            --ink: #0f172a;
            --muted: #64748b;
            --line: #e2e8f0;
            --surface: #ffffff;
            --surface-soft: #f8fafc;
            --blue: #1d4ed8;
            --blue-dark: #153e75;
            --amber: #d97706;
        }
        .stApp {
            background: #f8fafc;
        }
        .block-container {
            max-width: 1380px;
            padding-top: 1.25rem;
            padding-bottom: 4rem;
        }
        h1, h2, h3 {
            letter-spacing: -0.035em;
            color: var(--ink);
        }
        [data-testid="stHeader"] {
            background: rgba(248, 250, 252, 0.86);
        }
        .hero {
            position: relative;
            overflow: hidden;
            border: 1px solid #dbe7f3;
            border-radius: 24px;
            padding: 2.1rem 2.25rem 1.85rem;
            margin: 0 0 1.15rem;
            background:
                radial-gradient(circle at 92% 10%, rgba(59, 130, 246, 0.16), transparent 32%),
                linear-gradient(135deg, #ffffff 0%, #f1f7fd 100%);
            box-shadow: 0 16px 50px rgba(15, 23, 42, 0.06);
        }
        .hero-eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.34rem 0.68rem;
            border: 1px solid #cfe0f2;
            border-radius: 999px;
            background: rgba(255,255,255,0.78);
            color: #31506f;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.03em;
            margin-bottom: 0.9rem;
        }
        .hero h1 {
            margin: 0;
            font-size: clamp(2.1rem, 4.5vw, 3.55rem);
            line-height: 1.08;
            max-width: 900px;
        }
        .hero p {
            color: #52667a;
            font-size: 1.02rem;
            line-height: 1.85;
            max-width: 880px;
            margin: 0.85rem 0 0;
        }
        .control-panel {
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 0.95rem 1.15rem 0.25rem;
            background: rgba(255,255,255,0.94);
            margin-bottom: 1rem;
        }
        .stat-card {
            height: 100%;
            min-height: 142px;
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 1.05rem 1.15rem 1rem;
            background: var(--surface);
            box-shadow: 0 7px 22px rgba(15, 23, 42, 0.035);
        }
        .stat-label {
            color: var(--muted);
            font-size: 0.84rem;
            font-weight: 700;
            margin-bottom: 0.55rem;
        }
        .stat-value {
            color: var(--ink);
            font-size: clamp(1.55rem, 2.8vw, 2.35rem);
            line-height: 1.13;
            font-weight: 780;
            letter-spacing: -0.04em;
            word-break: keep-all;
        }
        .stat-meta {
            color: #64748b;
            font-size: 0.82rem;
            margin-top: 0.5rem;
            line-height: 1.45;
        }
        .insight-strip {
            border: 1px solid #dbe7f3;
            border-left: 5px solid #2563eb;
            border-radius: 14px;
            padding: 0.95rem 1.1rem;
            margin: 1rem 0 1.15rem;
            background: #f7fbff;
            color: #334155;
            line-height: 1.75;
        }
        .insight-strip strong {
            color: #0f3f75;
        }
        .panel {
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 1.05rem 1.15rem;
            background: var(--surface);
            box-shadow: 0 8px 26px rgba(15, 23, 42, 0.035);
            margin-bottom: 1rem;
        }
        .profile-card {
            border: 1px solid #dbe7f3;
            border-radius: 18px;
            padding: 1.15rem 1.2rem;
            background: linear-gradient(180deg, #ffffff, #f8fbfe);
            min-height: 450px;
        }
        .profile-kicker {
            color: #2563eb;
            font-size: 0.78rem;
            font-weight: 750;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .profile-name {
            color: var(--ink);
            font-weight: 800;
            font-size: 2rem;
            letter-spacing: -0.045em;
            margin: 0.25rem 0 0.8rem;
        }
        .profile-summary {
            color: #475569;
            font-size: 0.94rem;
            line-height: 1.75;
            margin-bottom: 1rem;
        }
        .profile-row {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            gap: 1rem;
            border-top: 1px solid #e7edf4;
            padding: 0.72rem 0;
        }
        .profile-row span:first-child {
            color: #64748b;
            font-size: 0.84rem;
        }
        .profile-row span:last-child {
            color: #172033;
            font-size: 0.93rem;
            font-weight: 750;
            text-align: right;
        }
        .type-badge {
            display: inline-block;
            padding: 0.36rem 0.65rem;
            border-radius: 999px;
            background: #eaf2ff;
            color: #174ea6;
            font-size: 0.78rem;
            font-weight: 750;
            margin-bottom: 0.75rem;
        }
        .map-legend {
            display: grid;
            grid-template-columns: repeat(6, minmax(74px, 1fr));
            gap: 6px;
            margin: 0.25rem 0 0.85rem;
        }
        .map-legend-item {
            font-size: 0.72rem;
            color: #64748b;
        }
        .map-legend-swatch {
            height: 10px;
            border-radius: 3px;
            margin-bottom: 4px;
        }
        .section-intro {
            color: #64748b;
            font-size: 0.92rem;
            line-height: 1.7;
            margin-top: -0.35rem;
            margin-bottom: 0.7rem;
        }
        .comparison-callout {
            border-radius: 15px;
            padding: 0.95rem 1.05rem;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            color: #334155;
            line-height: 1.7;
            margin-bottom: 1rem;
        }
        .rank-chip {
            display: inline-block;
            border: 1px solid #dbe7f3;
            background: #f8fbff;
            border-radius: 999px;
            padding: 0.22rem 0.55rem;
            font-size: 0.75rem;
            color: #31506f;
            margin-right: 0.3rem;
            margin-bottom: 0.35rem;
        }
        [data-baseweb="tab-list"] {
            gap: 0.35rem;
            border-bottom: 1px solid #dfe7ef;
        }
        [data-baseweb="tab"] {
            height: 3.1rem;
            padding: 0 1.05rem;
            font-weight: 700;
        }
        [data-testid="stDataFrame"] {
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            overflow: hidden;
        }
        .source-note {
            color: #64748b;
            font-size: 0.82rem;
            line-height: 1.65;
        }
        @media (max-width: 900px) {
            .hero { padding: 1.45rem 1.25rem; border-radius: 18px; }
            .map-legend { grid-template-columns: repeat(3, 1fr); }
            .stat-card { min-height: 118px; }
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


def format_difference(metric: str, value: float) -> str:
    sign = "+" if value > 0 else "−" if value < 0 else "±"
    absolute = abs(value)
    if metric == "高齢化率":
        return f"{sign}{absolute:.2f}pt"
    if metric == "人口":
        return f"{sign}{absolute:,.0f}人"
    return f"{sign}{absolute:,.0f}人/km²"


def stat_card(label: str, value: str, meta: str) -> None:
    st.markdown(
        f"""
        <div class="stat-card">
            <div class="stat-label">{escape(label)}</div>
            <div class="stat-value">{escape(value)}</div>
            <div class="stat-meta">{escape(meta)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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


def add_derived_columns(data: pd.DataFrame) -> pd.DataFrame:
    enriched = data.copy()
    for metric_name, config in METRICS.items():
        column = config["column"]
        enriched[f"{metric_name}順位"] = enriched[column].rank(
            method="min", ascending=False
        ).astype(int)
        median = float(enriched[column].median())
        enriched[f"{metric_name}中央値差"] = enriched[column] - median
        enriched[f"{metric_name}指数"] = enriched[column] / median * 100
    aging_median = float(enriched["高齢化率"].median())
    density_median = float(enriched["人口密度"].median())
    enriched["都市タイプ"] = enriched.apply(
        lambda row: (
            ("高齢" if row["高齢化率"] >= aging_median else "若年")
            + "・"
            + ("高密度" if row["人口密度"] >= density_median else "低密度")
        ),
        axis=1,
    )
    return enriched


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
                "面積表示": f"{row['面積_km2']:.2f}km²",
                "都市タイプ": row["都市タイプ"],
                "fill_color": color_for_value(value, minimum, maximum),
                "line_color": [217, 119, 6, 255]
                if is_selected
                else [255, 255, 255, 225],
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
            return pdk.ViewState(latitude=latitude, longitude=longitude, zoom=11.75)
    return pdk.ViewState(latitude=35.69, longitude=139.745, zoom=10.55)


def legend_html(metric: str, minimum: float, maximum: float) -> str:
    values = [
        minimum + (maximum - minimum) * index / (len(PALETTE) - 1)
        for index in range(len(PALETTE))
    ]
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


def selected_summary(row: pd.Series, data: pd.DataFrame) -> str:
    aging_diff = float(row["高齢化率"] - data["高齢化率"].median())
    density_diff = float(row["人口密度"] - data["人口密度"].median())
    aging_phrase = "高い" if aging_diff > 0 else "低い" if aging_diff < 0 else "同水準"
    density_phrase = "高い" if density_diff > 0 else "低い" if density_diff < 0 else "同水準"
    return (
        f"{row['自治体']}は、23区中央値と比べて高齢化率が{aging_phrase}、"
        f"人口密度が{density_phrase}区です。"
        f"中央値を基準にした便宜的な分類では「{row['都市タイプ']}型」に位置します。"
    )


def comparison_text(row_a: pd.Series, row_b: pd.Series) -> str:
    aging_gap = float(row_a["高齢化率"] - row_b["高齢化率"])
    density_gap = float(row_a["人口密度"] - row_b["人口密度"])
    population_gap = float(row_a["人口"] - row_b["人口"])
    return (
        f"{row_a['自治体']}は{row_b['自治体']}と比べ、"
        f"高齢化率が{format_difference('高齢化率', aging_gap)}、"
        f"人口密度が{format_difference('人口密度', density_gap)}、"
        f"人口が{format_difference('人口', population_gap)}です。"
        "指標の単位が異なるため、下の指数グラフでは23区中央値を100として比較します。"
    )


def correlation_description(value: float) -> str:
    strength = abs(value)
    if strength < 0.2:
        phrase = "ほとんど関係が見られません"
    elif strength < 0.4:
        phrase = "弱い関係が見られます"
    elif strength < 0.7:
        phrase = "中程度の関係が見られます"
    else:
        phrase = "比較的強い関係が見られます"
    direction = "正の" if value > 0 else "負の" if value < 0 else ""
    return f"相関係数は {value:.2f} で、{direction}{phrase}。"


def overview_insight(data: pd.DataFrame) -> str:
    top_aging = data.nlargest(1, "高齢化率").iloc[0]
    bottom_aging = data.nsmallest(1, "高齢化率").iloc[0]
    top_density = data.nlargest(1, "人口密度").iloc[0]
    largest = data.nlargest(1, "人口").iloc[0]
    corr = float(data["人口密度"].corr(data["高齢化率"]))
    return (
        f"<strong>全体像：</strong>高齢化率は{top_aging['自治体']}が最も高く、"
        f"{bottom_aging['自治体']}が最も低いです。人口密度は{top_density['自治体']}、"
        f"人口規模は{largest['自治体']}が最大です。"
        f"人口密度と高齢化率の相関係数は {corr:.2f} で、"
        "密度だけでは高齢化の違いを十分に説明できないことが分かります。"
    )


def profile_html(row: pd.Series, data: pd.DataFrame, metric: str) -> str:
    metric_rank = int(row[f"{metric}順位"])
    metric_diff = float(row[f"{metric}中央値差"])
    return f"""
    <div class="profile-card">
        <div class="profile-kicker">Selected ward profile</div>
        <div class="profile-name">{escape(str(row['自治体']))}</div>
        <div class="type-badge">中央値分類：{escape(str(row['都市タイプ']))}型</div>
        <div class="profile-summary">{escape(selected_summary(row, data))}</div>
        <div class="profile-row"><span>人口</span><span>{row['人口']:,.0f}人（{int(row['人口順位'])}位）</span></div>
        <div class="profile-row"><span>高齢化率</span><span>{row['高齢化率']:.2f}%（{int(row['高齢化率順位'])}位）</span></div>
        <div class="profile-row"><span>人口密度</span><span>{row['人口密度']:,.0f}人/km²（{int(row['人口密度順位'])}位）</span></div>
        <div class="profile-row"><span>面積</span><span>{row['面積_km2']:.2f}km²</span></div>
        <div class="profile-row"><span>{escape(METRICS[metric]['short_label'])}の中央値差</span><span>{escape(format_difference(metric, metric_diff))}</span></div>
        <div class="profile-row"><span>選択指標の順位</span><span>23区中 {metric_rank}位</span></div>
    </div>
    """


def make_map(
    geojson: dict,
    data: pd.DataFrame,
    metric: str,
    selected_ward: str,
) -> pdk.Deck:
    prepared = prepare_map_geojson(geojson, data, metric, selected_ward)
    layer = pdk.Layer(
        "GeoJsonLayer",
        data=prepared,
        pickable=True,
        stroked=True,
        filled=True,
        get_fill_color="properties.fill_color",
        get_line_color="properties.line_color",
        get_line_width="properties.line_width",
        line_width_min_pixels=1,
        auto_highlight=True,
        highlight_color=[217, 119, 6, 185],
    )
    return pdk.Deck(
        map_style=None,
        initial_view_state=selected_view_state(prepared, selected_ward),
        layers=[layer],
        tooltip={
            "html": (
                "<div style='font-size:15px'><b>{自治体}</b></div>"
                "<div style='margin-top:6px'>{表示指標}: <b>{表示値}</b></div>"
                "<div>人口: {人口表示}</div>"
                "<div>高齢化率: {高齢化率表示}</div>"
                "<div>人口密度: {人口密度表示}</div>"
                "<div>面積: {面積表示}</div>"
                "<div style='margin-top:5px;color:#cbd5e1'>{都市タイプ}型</div>"
            ),
            "style": {
                "backgroundColor": "#0f172a",
                "color": "white",
                "borderRadius": "10px",
                "padding": "10px",
            },
        },
    )


def make_ranking_chart(data: pd.DataFrame, metric: str, selected_ward: str) -> alt.Chart:
    column = METRICS[metric]["column"]
    chart_data = data.sort_values(column, ascending=False)
    median_value = float(data[column].median())
    bars = (
        alt.Chart(chart_data)
        .mark_bar(cornerRadiusEnd=4, height=18)
        .encode(
            x=alt.X(f"{column}:Q", title=METRICS[metric]["axis_title"]),
            y=alt.Y("自治体:N", sort="-x", title=None),
            color=alt.condition(
                alt.datum.自治体 == selected_ward,
                alt.value("#D97706"),
                alt.value("#2F6FA8"),
            ),
            tooltip=[
                alt.Tooltip("自治体:N"),
                alt.Tooltip("人口:Q", format=","),
                alt.Tooltip("高齢化率:Q", format=".2f"),
                alt.Tooltip("人口密度:Q", format=",.0f"),
            ],
        )
        .properties(height=610)
    )
    median_rule = (
        alt.Chart(pd.DataFrame({"中央値": [median_value]}))
        .mark_rule(color="#94A3B8", strokeDash=[5, 4], strokeWidth=2)
        .encode(x=alt.X("中央値:Q"))
    )
    return bars + median_rule


def make_scatter_chart(data: pd.DataFrame, selected_ward: str) -> alt.Chart:
    aging_median = float(data["高齢化率"].median())
    density_median = float(data["人口密度"].median())
    points = (
        alt.Chart(data)
        .mark_circle(opacity=0.9, stroke="white", strokeWidth=1.3)
        .encode(
            x=alt.X(
                "人口密度:Q",
                title="人口密度（人/km²）",
                scale=alt.Scale(zero=False),
            ),
            y=alt.Y(
                "高齢化率:Q",
                title="高齢化率（%）",
                scale=alt.Scale(zero=False),
            ),
            size=alt.Size(
                "人口:Q",
                title="人口",
                scale=alt.Scale(range=[100, 1000]),
            ),
            color=alt.Color(
                "都市タイプ:N",
                title="中央値分類",
                scale=alt.Scale(
                    domain=list(QUADRANT_COLORS),
                    range=list(QUADRANT_COLORS.values()),
                ),
            ),
            opacity=alt.condition(
                alt.datum.自治体 == selected_ward,
                alt.value(1),
                alt.value(0.78),
            ),
            strokeWidth=alt.condition(
                alt.datum.自治体 == selected_ward,
                alt.value(4),
                alt.value(1.2),
            ),
            tooltip=[
                alt.Tooltip("自治体:N"),
                alt.Tooltip("都市タイプ:N"),
                alt.Tooltip("人口:Q", format=","),
                alt.Tooltip("高齢化率:Q", format=".2f"),
                alt.Tooltip("人口密度:Q", format=",.0f"),
            ],
        )
    )
    vertical = (
        alt.Chart(pd.DataFrame({"人口密度中央値": [density_median]}))
        .mark_rule(color="#94A3B8", strokeDash=[5, 5])
        .encode(x="人口密度中央値:Q")
    )
    horizontal = (
        alt.Chart(pd.DataFrame({"高齢化率中央値": [aging_median]}))
        .mark_rule(color="#94A3B8", strokeDash=[5, 5])
        .encode(y="高齢化率中央値:Q")
    )
    labels = (
        alt.Chart(data)
        .mark_text(dx=9, dy=-7, fontSize=10, color="#334155")
        .encode(
            x="人口密度:Q",
            y="高齢化率:Q",
            text=alt.condition(
                (alt.datum.自治体 == selected_ward)
                | (alt.datum["高齢化率順位"] <= 2)
                | (alt.datum["人口密度順位"] <= 2),
                "自治体:N",
                alt.value(""),
            ),
        )
    )
    return (points + vertical + horizontal + labels).properties(height=520).interactive()


def make_comparison_index_chart(
    row_a: pd.Series,
    row_b: pd.Series,
) -> alt.Chart:
    records = []
    for metric in METRICS:
        records.extend(
            [
                {
                    "指標": METRICS[metric]["short_label"],
                    "区": row_a["自治体"],
                    "指数": row_a[f"{metric}指数"],
                },
                {
                    "指標": METRICS[metric]["short_label"],
                    "区": row_b["自治体"],
                    "指数": row_b[f"{metric}指数"],
                },
            ]
        )
    frame = pd.DataFrame(records)
    bars = (
        alt.Chart(frame)
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            x=alt.X("指数:Q", title="23区中央値＝100"),
            y=alt.Y("指標:N", title=None, sort=["人口", "高齢化率", "人口密度"]),
            yOffset="区:N",
            color=alt.Color(
                "区:N",
                title=None,
                scale=alt.Scale(range=["#1D4ED8", "#D97706"]),
            ),
            tooltip=[
                alt.Tooltip("区:N"),
                alt.Tooltip("指標:N"),
                alt.Tooltip("指数:Q", format=".1f"),
            ],
        )
        .properties(height=280)
    )
    rule = (
        alt.Chart(pd.DataFrame({"中央値": [100]}))
        .mark_rule(color="#64748B", strokeDash=[5, 4])
        .encode(x="中央値:Q")
    )
    return bars + rule


try:
    data = add_derived_columns(load_data())
    raw_geojson = load_geojson()
except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
    st.error(f"データを読み込めませんでした: {error}")
    st.stop()

st.markdown(
    """
    <section class="hero">
        <div class="hero-eyebrow">TOKYO 23 WARDS · OPEN DATA</div>
        <h1>東京23区 都市構造ダッシュボード</h1>
        <p>
            人口・高齢化率・人口密度を、地図で俯瞰し、2区比較で違いを捉え、
            散布図で都市構造を読み解きます。東京都の公開統計を、意思決定に使える形へ整理しました。
        </p>
    </section>
    """,
    unsafe_allow_html=True,
)

with st.container(border=True):
    control_left, control_right = st.columns([1.08, 0.92])
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
total_population = int(data["人口"].sum())
weighted_aging_rate = float(
    (data["人口"] * data["高齢化率"]).sum() / total_population
)
highest_aging = data.loc[data["高齢化率"].idxmax()]
highest_density = data.loc[data["人口密度"].idxmax()]
largest_population = data.loc[data["人口"].idxmax()]

summary_columns = st.columns(4)
with summary_columns[0]:
    stat_card(
        "23区の人口合計",
        f"{total_population:,}人",
        f"最大は{largest_population['自治体']}・{largest_population['人口']:,.0f}人",
    )
with summary_columns[1]:
    stat_card(
        "高齢化率（人口加重）",
        f"{weighted_aging_rate:.2f}%",
        f"23区中央値は{data['高齢化率'].median():.2f}%",
    )
with summary_columns[2]:
    stat_card(
        "高齢化率が最も高い区",
        str(highest_aging["自治体"]),
        f"{highest_aging['高齢化率']:.2f}%・中央値より{highest_aging['高齢化率'] - data['高齢化率'].median():+.2f}pt",
    )
with summary_columns[3]:
    stat_card(
        "人口密度が最も高い区",
        str(highest_density["自治体"]),
        f"{highest_density['人口密度']:,.0f}人/km²",
    )

st.markdown(
    f'<div class="insight-strip">{overview_insight(data)}</div>',
    unsafe_allow_html=True,
)

map_tab, compare_tab, analysis_tab, data_tab = st.tabs(
    ["地図とプロフィール", "2区比較", "構造分析", "データ"]
)

with map_tab:
    left, right = st.columns([1.65, 0.75], gap="large")
    with left:
        st.subheader(f"{METRICS[selected_metric]['label']}の分布")
        st.markdown(
            '<div class="section-intro">色が濃いほど値が高くなります。区にカーソルを合わせると、複数指標を同時に確認できます。</div>',
            unsafe_allow_html=True,
        )
        minimum = float(data[metric_column].min())
        maximum = float(data[metric_column].max())
        st.markdown(legend_html(selected_metric, minimum, maximum), unsafe_allow_html=True)
        st.pydeck_chart(
            make_map(raw_geojson, data, selected_metric, selected_ward),
            width="stretch",
            height=600,
        )
    with right:
        if selected_ward == "23区全体":
            representative = data.loc[data[metric_column].idxmax()]
            st.markdown(
                f"""
                <div class="profile-card">
                    <div class="profile-kicker">Tokyo 23 wards overview</div>
                    <div class="profile-name">23区全体</div>
                    <div class="type-badge">選択指標：{escape(METRICS[selected_metric]['short_label'])}</div>
                    <div class="profile-summary">
                        地図とランキングは同じ指標に連動します。区を選ぶと、順位・中央値差・都市タイプまで詳細表示に切り替わります。
                    </div>
                    <div class="profile-row"><span>選択指標の最大</span><span>{escape(str(representative['自治体']))}</span></div>
                    <div class="profile-row"><span>最大値</span><span>{escape(format_value(selected_metric, float(representative[metric_column])))}</span></div>
                    <div class="profile-row"><span>中央値</span><span>{escape(format_value(selected_metric, float(data[metric_column].median())))}</span></div>
                    <div class="profile-row"><span>最小値</span><span>{escape(format_value(selected_metric, float(data[metric_column].min())))}</span></div>
                    <div class="profile-row"><span>データ件数</span><span>23区</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            selected_row = data.loc[data["自治体"] == selected_ward].iloc[0]
            st.markdown(
                profile_html(selected_row, data, selected_metric),
                unsafe_allow_html=True,
            )
    st.markdown(
        '<p class="source-note">統計値は2026年版、行政境界は2023年1月1日時点です。境界データは地理的比較のために使用しています。</p>',
        unsafe_allow_html=True,
    )

with compare_tab:
    st.subheader("2つの区を、同じ基準で比較する")
    st.markdown(
        '<div class="section-intro">絶対値と、23区中央値を100とした指数の両方を表示します。単位の異なる指標を無理に合算しません。</div>',
        unsafe_allow_html=True,
    )
    selector_a, selector_b = st.columns(2)
    ward_names = data["自治体"].tolist()
    default_a = ward_names.index("足立区") if "足立区" in ward_names else 0
    with selector_a:
        ward_a = st.selectbox("比較する区 A", ward_names, index=default_a, key="ward_a")
    options_b = [ward for ward in ward_names if ward != ward_a]
    default_b = options_b.index("豊島区") if "豊島区" in options_b else 0
    with selector_b:
        ward_b = st.selectbox("比較する区 B", options_b, index=default_b, key="ward_b")
    row_a = data.loc[data["自治体"] == ward_a].iloc[0]
    row_b = data.loc[data["自治体"] == ward_b].iloc[0]
    st.markdown(
        f'<div class="comparison-callout">{escape(comparison_text(row_a, row_b))}</div>',
        unsafe_allow_html=True,
    )
    card_a, card_b = st.columns(2, gap="large")
    with card_a:
        st.markdown(
            f"""
            <div class="panel">
                <h3 style="margin-top:0">{escape(ward_a)}</h3>
                <span class="rank-chip">人口 {int(row_a['人口順位'])}位</span>
                <span class="rank-chip">高齢化率 {int(row_a['高齢化率順位'])}位</span>
                <span class="rank-chip">人口密度 {int(row_a['人口密度順位'])}位</span>
                <div class="profile-row"><span>人口</span><span>{row_a['人口']:,.0f}人</span></div>
                <div class="profile-row"><span>高齢化率</span><span>{row_a['高齢化率']:.2f}%</span></div>
                <div class="profile-row"><span>人口密度</span><span>{row_a['人口密度']:,.0f}人/km²</span></div>
                <div class="profile-row"><span>中央値分類</span><span>{escape(str(row_a['都市タイプ']))}型</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with card_b:
        st.markdown(
            f"""
            <div class="panel">
                <h3 style="margin-top:0">{escape(ward_b)}</h3>
                <span class="rank-chip">人口 {int(row_b['人口順位'])}位</span>
                <span class="rank-chip">高齢化率 {int(row_b['高齢化率順位'])}位</span>
                <span class="rank-chip">人口密度 {int(row_b['人口密度順位'])}位</span>
                <div class="profile-row"><span>人口</span><span>{row_b['人口']:,.0f}人</span></div>
                <div class="profile-row"><span>高齢化率</span><span>{row_b['高齢化率']:.2f}%</span></div>
                <div class="profile-row"><span>人口密度</span><span>{row_b['人口密度']:,.0f}人/km²</span></div>
                <div class="profile-row"><span>中央値分類</span><span>{escape(str(row_b['都市タイプ']))}型</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.altair_chart(make_comparison_index_chart(row_a, row_b), width="stretch")
    st.caption("破線の100が23区中央値です。100を上回るほど、中央値より高いことを示します。")

with analysis_tab:
    st.subheader("人口密度と高齢化率から、23区の構造を読む")
    st.markdown(
        '<div class="section-intro">中央値の縦線・横線で4タイプに分けています。分類は発見を補助するための便宜的なもので、政策的な優劣を示しません。</div>',
        unsafe_allow_html=True,
    )
    analysis_left, analysis_right = st.columns([1.35, 0.65], gap="large")
    with analysis_left:
        st.altair_chart(make_scatter_chart(data, selected_ward), width="stretch")
    with analysis_right:
        corr = float(data["人口密度"].corr(data["高齢化率"]))
        st.markdown(
            f"""
            <div class="panel">
                <div class="profile-kicker">Relationship</div>
                <div class="profile-name" style="font-size:1.75rem">r = {corr:.2f}</div>
                <div class="profile-summary">{escape(correlation_description(corr))}相関は因果関係を示さないため、住宅構成・年齢移動・土地利用などの背景要因は別途検討が必要です。</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        type_counts = data["都市タイプ"].value_counts()
        for label in QUADRANT_COLORS:
            count = int(type_counts.get(label, 0))
            st.markdown(
                f"""
                <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #e2e8f0;padding:.63rem .2rem">
                    <span><span style="display:inline-block;width:10px;height:10px;border-radius:999px;background:{QUADRANT_COLORS[label]};margin-right:8px"></span>{label}型</span>
                    <strong>{count}区</strong>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.divider()
    rank_left, rank_right = st.columns([1.25, 0.75], gap="large")
    with rank_left:
        st.subheader(f"{METRICS[selected_metric]['label']}ランキング")
        st.altair_chart(
            make_ranking_chart(data, selected_metric, selected_ward),
            width="stretch",
        )
        st.caption("破線は23区中央値です。注目する区を選ぶとオレンジ色で強調されます。")
    with rank_right:
        st.subheader("上位・下位")
        top = data.nlargest(5, metric_column)[["自治体", metric_column]]
        bottom = data.nsmallest(5, metric_column)[["自治体", metric_column]]
        st.markdown("**上位5区**")
        for _, row in top.iterrows():
            st.markdown(f"- **{row['自治体']}**　{format_value(selected_metric, float(row[metric_column]))}")
        st.markdown("**下位5区**")
        for _, row in bottom.iterrows():
            st.markdown(f"- **{row['自治体']}**　{format_value(selected_metric, float(row[metric_column]))}")

with data_tab:
    st.subheader("23区の統計一覧")
    st.markdown(
        '<div class="section-intro">並び順は上部で選択した指標に連動します。順位・中央値差・都市タイプまで含めてCSV保存できます。</div>',
        unsafe_allow_html=True,
    )
    table_columns = [
        "自治体",
        "面積_km2",
        "人口",
        "高齢化率",
        "人口密度",
        f"{selected_metric}順位",
        f"{selected_metric}中央値差",
        "都市タイプ",
    ]
    table_data = data[table_columns].sort_values(metric_column, ascending=False).copy()
    table_data = table_data.rename(
        columns={
            f"{selected_metric}順位": "順位",
            f"{selected_metric}中央値差": "中央値差",
        }
    )
    st.dataframe(
        table_data,
        hide_index=True,
        width="stretch",
        column_config={
            "自治体": st.column_config.TextColumn("区"),
            "面積_km2": st.column_config.NumberColumn("面積", format="%.2f km²"),
            "人口": st.column_config.NumberColumn("人口", format="localized"),
            "高齢化率": st.column_config.NumberColumn("高齢化率", format="%.2f%%"),
            "人口密度": st.column_config.NumberColumn("人口密度", format="localized"),
            "順位": st.column_config.NumberColumn(f"{selected_metric}順位", format="%d"),
            "中央値差": st.column_config.NumberColumn("中央値差", format="localized"),
            "都市タイプ": st.column_config.TextColumn("中央値分類"),
        },
    )
    csv_data = table_data.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "表示データをCSVで保存",
        data=csv_data,
        file_name="tokyo_23wards_contest_dashboard.csv",
        mime="text/csv",
        width="content",
    )
    with st.expander("データの出典・設計方針・注意点"):
        st.markdown(
            "- 統計：東京都『区市町村統計表（2026年）』\n"
            "- 行政境界：国土交通省『国土数値情報（行政区域データ）』をもとにNIIが加工した2023年1月1日時点のGeoJSON\n"
            "- 人口密度：人口 ÷ 面積（km²）で算出\n"
            "- 指数：各指標の23区中央値を100として算出。異なる単位の比較補助にのみ使用\n"
            "- 都市タイプ：高齢化率と人口密度の各中央値で4分類した便宜的ラベル\n"
            "- 独自の総合スコアは作らず、公表値と透明な派生指標だけを表示"
        )
        st.markdown(
            "[東京都 区市町村統計表](https://www.toukei.metro.tokyo.lg.jp/kurasi/2026/ku26-23.htm)  "
            "／ [行政境界データ](https://geoshape.ex.nii.ac.jp/city/choropleth/13_city.html)"
        )

st.divider()
st.markdown(
    f"""
    <p class="source-note">
        公開アプリ：<a href="{LIVE_APP_URL}" target="_blank">{LIVE_APP_URL}</a><br>
        本ダッシュボードは公開統計の探索・比較を目的とし、政策判断には追加のデータ検証が必要です。
    </p>
    """,
    unsafe_allow_html=True,
)
