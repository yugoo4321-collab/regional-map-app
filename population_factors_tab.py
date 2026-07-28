from __future__ import annotations

import copy
from html import escape
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


FACTOR_COLUMNS = [
    "他県移動増減",
    "都内間移動増減",
    "自然増減",
    "その他増減",
]

FACTOR_COLORS = {
    "他県移動増減": "#24476B",
    "都内間移動増減": "#6E9FA3",
    "自然増減": "#B86B3D",
    "その他増減": "#9AA3AD",
}

LOCAL_STYLE = """
<style>
.factor-head {
    padding: 0.15rem 0 1.25rem;
    border-bottom: 1px solid rgba(15, 23, 42, 0.12);
    margin-bottom: 1.25rem;
}
.factor-kicker {
    font-size: 0.72rem;
    letter-spacing: 0.16em;
    font-weight: 700;
    color: #6B7280;
    margin-bottom: 0.45rem;
}
.factor-title {
    font-size: clamp(1.75rem, 3vw, 2.55rem);
    line-height: 1.12;
    letter-spacing: -0.04em;
    font-weight: 760;
    color: #111827;
    margin: 0;
}
.factor-lead {
    max-width: 780px;
    margin: 0.75rem 0 0;
    color: #596273;
    font-size: 0.96rem;
    line-height: 1.8;
}
.factor-kpi-grid {
    display: grid;
    grid-template-columns: 1.15fr 1.15fr 0.85fr 0.85fr;
    border-top: 1px solid #D7DEE8;
    border-bottom: 1px solid #D7DEE8;
    margin: 0.2rem 0 1.45rem;
}
.factor-kpi {
    padding: 1rem 1rem 0.95rem;
    border-right: 1px solid #D7DEE8;
}
.factor-kpi:last-child {
    border-right: 0;
}
.factor-kpi-label {
    font-size: 0.75rem;
    color: #6B7280;
    letter-spacing: 0.03em;
    margin-bottom: 0.25rem;
}
.factor-kpi-value {
    color: #111827;
    font-size: clamp(1.35rem, 2.2vw, 2rem);
    letter-spacing: -0.035em;
    line-height: 1.15;
    font-weight: 720;
}
.factor-selector-label {
    font-size: 0.78rem;
    color: #5E6877;
    font-weight: 700;
    margin-bottom: 0.3rem;
}
.factor-brief {
    padding: 0.9rem 1rem 0.9rem 1.15rem;
    border-left: 4px solid #24476B;
    background: rgba(255, 255, 255, 0.68);
    color: #263244;
    line-height: 1.75;
    margin: 0.55rem 0 1.35rem;
}
.factor-section {
    margin: 0.4rem 0 0.65rem;
}
.factor-section-number {
    color: #8A93A1;
    font-size: 0.72rem;
    letter-spacing: 0.14em;
    font-weight: 700;
}
.factor-section-title {
    color: #172033;
    font-size: 1.16rem;
    font-weight: 720;
    margin-top: 0.14rem;
}
.factor-section-note {
    color: #6B7280;
    font-size: 0.82rem;
    line-height: 1.6;
    margin-top: 0.2rem;
}
.factor-rank {
    border-top: 1px solid #D8DEE7;
}
.factor-rank-row {
    display: grid;
    grid-template-columns: 2rem 1fr auto;
    gap: 0.55rem;
    align-items: center;
    padding: 0.65rem 0.1rem;
    border-bottom: 1px solid #E3E7ED;
}
.factor-rank-no {
    color: #8B93A1;
    font-size: 0.78rem;
}
.factor-rank-name {
    color: #1F2937;
    font-weight: 650;
}
.factor-rank-value {
    color: #111827;
    font-variant-numeric: tabular-nums;
    font-weight: 700;
}
.factor-source {
    color: #727B88;
    font-size: 0.76rem;
    line-height: 1.7;
    margin-top: 1.2rem;
}
@media (max-width: 900px) {
    .factor-kpi-grid {
        grid-template-columns: 1fr 1fr;
    }
    .factor-kpi:nth-child(2) {
        border-right: 0;
    }
    .factor-kpi:nth-child(-n+2) {
        border-bottom: 1px solid #D7DEE8;
    }
}
</style>
"""


@st.cache_data(show_spinner=False)
def load_population_factors(path: str) -> pd.DataFrame:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(
            f"{source} が見つかりません。prepare_population_factors.pyを実行してください"
        )

    factors = pd.read_csv(source, dtype={"自治体コード": str})
    required = {
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
    }
    missing = required - set(factors.columns)
    if missing:
        raise ValueError(f"要因分析CSVに必要な列がありません: {sorted(missing)}")

    factors["自治体コード"] = factors["自治体コード"].str.zfill(5)
    for column in required - {"自治体コード", "自治体"}:
        factors[column] = pd.to_numeric(factors[column], errors="raise")

    if len(factors) != 23 or factors["自治体"].nunique() != 23:
        raise ValueError("要因分析データが23区ではありません")
    if factors["自治体コード"].duplicated().any():
        raise ValueError("要因分析データの自治体コードが重複しています")

    return factors.sort_values("自治体コード").reset_index(drop=True)


def _direction_word(value: float) -> str:
    if value > 0:
        return "増"
    if value < 0:
        return "減"
    return "横ばい"


def _factor_summary(row: pd.Series) -> str:
    total = int(row["人口増減"])
    social = int(row["社会増減"])
    natural = int(row["自然増減"])
    other = int(row["その他増減"])

    if social > 0 and natural < 0:
        interpretation = "転入超過が自然減を上回りました。"
    elif social > 0 and natural >= 0:
        interpretation = "社会増と自然増がともに人口を押し上げました。"
    elif social <= 0 and natural < 0:
        interpretation = "社会減と自然減が重なりました。"
    else:
        interpretation = "自然増が社会減を補いました。"

    return (
        f"<strong>{escape(str(row['自治体']))}</strong>の人口増減は"
        f"<strong>{total:+,}人</strong>。"
        f"社会{_direction_word(social)} {social:+,}人、"
        f"自然{_direction_word(natural)} {natural:+,}人、"
        f"その他 {other:+,}人。{interpretation}"
    )


def _section(number: str, title: str, note: str = "") -> None:
    note_html = (
        f'<div class="factor-section-note">{escape(note)}</div>'
        if note
        else ""
    )
    st.markdown(
        (
            '<div class="factor-section">'
            f'<div class="factor-section-number">{escape(number)}</div>'
            f'<div class="factor-section-title">{escape(title)}</div>'
            f"{note_html}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def _factor_bar(row: pd.Series) -> alt.Chart:
    chart_data = pd.DataFrame(
        {
            "要因": FACTOR_COLUMNS,
            "増減": [float(row[column]) for column in FACTOR_COLUMNS],
        }
    )

    bars = (
        alt.Chart(chart_data)
        .mark_bar(cornerRadiusEnd=3, height=24)
        .encode(
            x=alt.X(
                "増減:Q",
                title="人口への寄与（人）",
                axis=alt.Axis(gridColor="#E7EBF0", labelColor="#697386"),
            ),
            y=alt.Y(
                "要因:N",
                title=None,
                sort=FACTOR_COLUMNS,
                axis=alt.Axis(labelColor="#4B5563", labelFontSize=12),
            ),
            color=alt.Color(
                "要因:N",
                scale=alt.Scale(
                    domain=FACTOR_COLUMNS,
                    range=[FACTOR_COLORS[column] for column in FACTOR_COLUMNS],
                ),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("要因:N"),
                alt.Tooltip("増減:Q", format="+,.0f", title="寄与"),
            ],
        )
    )

    zero = (
        alt.Chart(pd.DataFrame({"基準": [0]}))
        .mark_rule(color="#788392", strokeDash=[4, 4])
        .encode(x="基準:Q")
    )

    return (
        (bars + zero)
        .properties(height=275)
        .configure_view(strokeOpacity=0)
        .configure(background="transparent")
    )


def _birth_death_chart(row: pd.Series) -> alt.Chart:
    chart_data = pd.DataFrame(
        {
            "項目": ["出生数", "死亡数"],
            "人数": [float(row["出生数"]), float(row["死亡数"])],
        }
    )

    return (
        alt.Chart(chart_data)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, width=72)
        .encode(
            x=alt.X(
                "項目:N",
                title=None,
                axis=alt.Axis(labelColor="#4B5563", labelFontSize=12),
            ),
            y=alt.Y(
                "人数:Q",
                title="人",
                axis=alt.Axis(gridColor="#E7EBF0", labelColor="#697386"),
            ),
            color=alt.Color(
                "項目:N",
                scale=alt.Scale(
                    domain=["出生数", "死亡数"],
                    range=["#6E9FA3", "#B86B3D"],
                ),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("項目:N"),
                alt.Tooltip("人数:Q", format=",.0f"),
            ],
        )
        .properties(height=275)
        .configure_view(strokeOpacity=0)
        .configure(background="transparent")
    )


def _scatter(factors: pd.DataFrame, selected_ward: str) -> alt.Chart:
    chart_data = factors.copy()
    chart_data["選択"] = chart_data["自治体"].eq(selected_ward)

    return (
        alt.Chart(chart_data)
        .mark_circle(opacity=0.82, stroke="#FFFFFF", strokeWidth=1)
        .encode(
            x=alt.X(
                "社会増減:Q",
                title="社会増減（人）",
                axis=alt.Axis(gridColor="#E8ECF1", labelColor="#697386"),
            ),
            y=alt.Y(
                "自然増減:Q",
                title="自然増減（人）",
                axis=alt.Axis(gridColor="#E8ECF1", labelColor="#697386"),
            ),
            size=alt.Size(
                "出生数:Q",
                scale=alt.Scale(range=[80, 650]),
                legend=None,
            ),
            color=alt.condition(
                alt.datum.選択,
                alt.value("#B86B3D"),
                alt.value("#4E7394"),
            ),
            tooltip=[
                alt.Tooltip("自治体:N", title="区"),
                alt.Tooltip("社会増減:Q", format="+,.0f"),
                alt.Tooltip("自然増減:Q", format="+,.0f"),
                alt.Tooltip("出生数:Q", format=",.0f"),
                alt.Tooltip("死亡数:Q", format=",.0f"),
                alt.Tooltip("人口増減:Q", format="+,.0f"),
            ],
        )
        .properties(height=430)
        .interactive()
        .configure_view(strokeOpacity=0)
        .configure(background="transparent")
    )


def _map_chart(
    geojson: dict,
    factors: pd.DataFrame,
    metric: str,
    selected_ward: str,
) -> alt.Chart:
    values = factors.set_index("自治体コード")[metric].to_dict()
    names = factors.set_index("自治体コード")["自治体"].to_dict()
    prepared = copy.deepcopy(geojson)
    feature_values: list[float] = []

    for feature in prepared.get("features", []):
        properties = feature.setdefault("properties", {})
        code = str(properties.get("N03_007", "")).zfill(5)
        value = values.get(code)
        ward = names.get(code)
        properties["自治体"] = ward
        properties["要因値"] = None if value is None else float(value)
        properties["選択"] = ward == selected_ward
        if value is not None:
            feature_values.append(float(value))

    minimum = min(feature_values)
    maximum = max(feature_values)
    absolute = max(abs(minimum), abs(maximum), 1)

    base = (
        alt.Chart(alt.Data(values=prepared["features"]))
        .mark_geoshape(stroke="#F8FAFC", strokeWidth=1)
        .encode(
            color=alt.Color(
                "properties.要因値:Q",
                title=f"{metric}（人）",
                scale=alt.Scale(
                    domain=[-absolute, 0, absolute],
                    range=["#B86B3D", "#F3F1EC", "#4E7394"],
                ),
                legend=alt.Legend(
                    orient="bottom",
                    direction="horizontal",
                    gradientLength=180,
                    titleLimit=220,
                ),
            ),
            tooltip=[
                alt.Tooltip("properties.自治体:N", title="区"),
                alt.Tooltip(
                    "properties.要因値:Q",
                    title=metric,
                    format="+,.0f",
                ),
            ],
        )
    )

    selected_features = [
        feature
        for feature in prepared["features"]
        if feature.get("properties", {}).get("選択")
    ]
    layers = [base]

    if selected_features:
        layers.append(
            alt.Chart(alt.Data(values=selected_features))
            .mark_geoshape(
                fillOpacity=0,
                stroke="#172033",
                strokeWidth=2.8,
            )
        )

    return (
        alt.layer(*layers)
        .project(type="mercator")
        .properties(height=430)
        .configure_view(
            stroke="#DCE2E8",
            strokeWidth=1,
            fill="#F8FAFC",
        )
        .configure(background="transparent")
    )


def _rank_html(frame: pd.DataFrame, metric: str) -> str:
    signed_metrics = {"人口増減", "社会増減", "自然増減"}
    rows: list[str] = []

    for rank, (_, row) in enumerate(frame.iterrows(), start=1):
        value = float(row[metric])
        value_text = (
            f"{value:+,.0f}人"
            if metric in signed_metrics
            else f"{value:,.0f}人"
        )
        rows.append(
            (
                '<div class="factor-rank-row">'
                f'<div class="factor-rank-no">{rank:02d}</div>'
                f'<div class="factor-rank-name">{escape(str(row["自治体"]))}</div>'
                f'<div class="factor-rank-value">{value_text}</div>'
                "</div>"
            )
        )

    return '<div class="factor-rank">' + "".join(rows) + "</div>"


def render_population_factors_tab(
    current_data: pd.DataFrame,
    geojson: dict,
    factor_path: str,
) -> None:
    st.markdown(LOCAL_STYLE, unsafe_allow_html=True)

    factors = load_population_factors(factor_path)
    merged = factors.merge(
        current_data[["自治体コード", "人口"]],
        on="自治体コード",
        how="left",
        validate="one_to_one",
    )
    year = int(merged["年"].iloc[0])

    total_social = int(merged["社会増減"].sum())
    total_natural = int(merged["自然増減"].sum())
    total_births = int(merged["出生数"].sum())
    total_deaths = int(merged["死亡数"].sum())

    st.markdown(
        (
            '<div class="factor-head">'
            '<div class="factor-kicker">TOKYO 23 区 / 2025</div>'
            '<h2 class="factor-title">人口変化の内訳</h2>'
            '<p class="factor-lead">'
            f"{year}年中の人口変化を、社会増減、自然増減、その他増減に分けて見る。"
            "区ごとに、増減の大きさだけでなく、その組み合わせを確認する。"
            "</p>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        (
            '<div class="factor-kpi-grid">'
            '<div class="factor-kpi">'
            '<div class="factor-kpi-label">23区の社会増減</div>'
            f'<div class="factor-kpi-value">{total_social:+,}人</div>'
            "</div>"
            '<div class="factor-kpi">'
            '<div class="factor-kpi-label">23区の自然増減</div>'
            f'<div class="factor-kpi-value">{total_natural:+,}人</div>'
            "</div>"
            '<div class="factor-kpi">'
            '<div class="factor-kpi-label">出生数</div>'
            f'<div class="factor-kpi-value">{total_births:,}人</div>'
            "</div>"
            '<div class="factor-kpi">'
            '<div class="factor-kpi-label">死亡数</div>'
            f'<div class="factor-kpi-value">{total_deaths:,}人</div>'
            "</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    ward_names = merged["自治体"].tolist()
    st.markdown(
        '<div class="factor-selector-label">区を選ぶ</div>',
        unsafe_allow_html=True,
    )
    selected_ward = st.selectbox(
        "区を選ぶ",
        ward_names,
        index=ward_names.index("杉並区") if "杉並区" in ward_names else 0,
        key="factor_selected_ward",
        label_visibility="collapsed",
    )
    selected = merged.loc[merged["自治体"] == selected_ward].iloc[0]

    st.markdown(
        f'<div class="factor-brief">{_factor_summary(selected)}</div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.12, 0.88], gap="large")
    with left:
        _section("", "人口増減の要因分解")
        st.altair_chart(_factor_bar(selected), width="stretch")

    with right:
        _section("", "出生と死亡")
        st.altair_chart(_birth_death_chart(selected), width="stretch")

    st.divider()

    map_column, scatter_column = st.columns([1, 1], gap="large")
    with map_column:
        _section(
            "",
            "23区の分布",
            "青は増加方向、茶は減少方向。色は評価ではなく方向と大きさを示す。",
        )
        map_metric = st.selectbox(
            "地図で見る要因",
            ["社会増減", "自然増減", "人口増減"],
            key="factor_map_metric",
            label_visibility="collapsed",
        )
        st.altair_chart(
            _map_chart(geojson, merged, map_metric, selected_ward),
            width="stretch",
        )

    with scatter_column:
        _section(
            "",
            "社会増減と自然増減",
            "右ほど社会増、上ほど自然増。点の大きさは出生数。",
        )
        st.altair_chart(
            _scatter(merged, selected_ward),
            width="stretch",
        )
        st.caption("位置関係は因果関係を直接示すものではありません。")

    st.divider()

    _section("", "区別ランキング")
    rank_metric = st.selectbox(
        "ランキング指標",
        ["人口増減", "社会増減", "自然増減", "出生数", "死亡数"],
        key="factor_rank_metric",
    )
    top = merged.nlargest(5, rank_metric)[["自治体", rank_metric]]
    bottom = merged.nsmallest(5, rank_metric)[["自治体", rank_metric]]

    rank_left, rank_right = st.columns(2, gap="large")
    with rank_left:
        st.markdown("**上位5区**")
        st.markdown(_rank_html(top, rank_metric), unsafe_allow_html=True)

    with rank_right:
        st.markdown("**下位5区**")
        st.markdown(_rank_html(bottom, rank_metric), unsafe_allow_html=True)

    with st.expander("定義と注意点"):
        st.markdown(
            "- **社会増減**：他県移動増減と都内間移動増減の合計\n"
            "- **自然増減**：出生数－死亡数\n"
            "- **人口増減**：社会増減＋自然増減＋その他増減\n"
            "- 1年間の集計であり、長期的な因果関係を断定するものではありません。"
        )

    st.markdown(
        (
            '<div class="factor-source">'
            "出典：東京都総務局統計部「人口の動き（令和7年中）」"
            "</div>"
        ),
        unsafe_allow_html=True,
    )
