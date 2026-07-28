from __future__ import annotations

from html import escape
from itertools import combinations
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


DEMO_STYLE = """
<style>
.demo-head {
    padding: 0.3rem 0 1rem;
    border-bottom: 1px solid #D4DCE5;
    margin-bottom: 1rem;
}
.demo-title {
    color: #17263A;
    font-size: clamp(1.8rem, 3vw, 2.45rem);
    letter-spacing: -0.04em;
    margin: 0;
}
.demo-lead {
    max-width: 820px;
    color: #566477;
    line-height: 1.75;
    margin: 0.65rem 0 0;
}
.demo-progress {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.45rem;
    margin: 0.9rem 0 1.15rem;
}
.demo-progress-item {
    padding: 0.55rem 0.65rem;
    border-top: 3px solid #D5DDE5;
    color: #758193;
    font-size: 0.76rem;
    line-height: 1.35;
}
.demo-progress-item.active {
    border-top-color: #315F7B;
    color: #18364A;
    font-weight: 760;
}
.demo-question {
    display: inline-block;
    padding: 0.32rem 0.58rem;
    margin-bottom: 0.58rem;
    border: 1px solid #BFCBD5;
    border-radius: 5px 7px 5px 6px;
    background: #FFFDF8;
    color: #315F7B;
    font-size: 0.76rem;
    font-weight: 760;
    transform: rotate(-0.5deg);
}
.demo-finding {
    padding: 0.95rem 1.05rem;
    margin: 0.65rem 0 1rem;
    border: 1px solid #D2DAE3;
    border-left: 4px solid #315F7B;
    border-radius: 7px;
    background: #FFFFFF;
    color: #314155;
    line-height: 1.75;
}
.demo-finding strong {
    color: #17263A;
}
.demo-ward-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.7rem;
    margin: 0.65rem 0 0.85rem;
}
.demo-ward {
    padding: 0.9rem 0.95rem;
    border: 1px solid #D4DCE5;
    border-radius: 9px;
    background: linear-gradient(145deg, #FFFFFF, #F6F8FA);
}
.demo-ward-name {
    color: #17263A;
    font-size: 1.3rem;
    font-weight: 790;
}
.demo-ward-value {
    color: #566477;
    font-size: 0.82rem;
    line-height: 1.65;
    margin-top: 0.35rem;
}
.demo-script {
    padding: 0.8rem 0.95rem;
    border: 1px dashed #B7C4CF;
    border-radius: 7px;
    background: #FAFBFC;
    color: #465568;
    line-height: 1.7;
}
.demo-script-label {
    color: #315F7B;
    font-size: 0.72rem;
    font-weight: 800;
    margin-bottom: 0.25rem;
}
.demo-pipeline {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    border-top: 1px solid #CDD6DF;
    border-bottom: 1px solid #CDD6DF;
    margin: 0.7rem 0 1rem;
}
.demo-pipeline-item {
    position: relative;
    padding: 0.9rem 0.75rem;
    border-right: 1px solid #D8DFE6;
}
.demo-pipeline-item:last-child {
    border-right: 0;
}
.demo-pipeline-no {
    color: #8A95A4;
    font-size: 0.7rem;
    font-weight: 760;
}
.demo-pipeline-name {
    color: #17263A;
    font-weight: 760;
    margin-top: 0.25rem;
}
.demo-pipeline-note {
    color: #667487;
    font-size: 0.76rem;
    line-height: 1.55;
    margin-top: 0.25rem;
}
.demo-nav {
    margin-top: 0.8rem;
}
@media (max-width: 850px) {
    .demo-progress {
        grid-template-columns: 1fr 1fr;
    }
    .demo-ward-grid {
        grid-template-columns: 1fr;
    }
    .demo-pipeline {
        grid-template-columns: 1fr 1fr;
    }
    .demo-pipeline-item:nth-child(2) {
        border-right: 0;
    }
    .demo-pipeline-item:nth-child(-n+2) {
        border-bottom: 1px solid #D8DFE6;
    }
}
</style>
"""


STEP_LABELS = [
    "同じ規模でも違う",
    "変化は一方向ではない",
    "自然減でも増える",
    "実装と検証",
]


@st.cache_data(show_spinner=False)
def load_demo_factors(path: str) -> pd.DataFrame:
    source = Path(path)
    if not source.exists():
        return pd.DataFrame()

    frame = pd.read_csv(source, dtype={"自治体コード": str})
    frame["自治体コード"] = frame["自治体コード"].str.zfill(5)
    return frame


def find_similar_population_pair(data: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """人口規模が近く、高齢化率の差が大きい2区を選ぶ。"""
    candidates: list[tuple[float, pd.Series, pd.Series]] = []

    for first_index, second_index in combinations(data.index, 2):
        first = data.loc[first_index]
        second = data.loc[second_index]

        mean_population = (
            float(first["人口"]) + float(second["人口"])
        ) / 2
        population_gap_rate = (
            abs(float(first["人口"]) - float(second["人口"]))
            / mean_population
        )
        aging_gap = abs(
            float(first["高齢化率"])
            - float(second["高齢化率"])
        )

        if population_gap_rate <= 0.18:
            score = aging_gap / (population_gap_rate + 0.025)
            candidates.append((score, first, second))

    if not candidates:
        ordered = data.sort_values("人口")
        return ordered.iloc[0], ordered.iloc[1]

    _, first, second = max(candidates, key=lambda item: item[0])
    return first, second


def history_changes(history: pd.DataFrame) -> pd.DataFrame:
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
    changes = first.merge(last, on="自治体", validate="one_to_one")
    changes["人口増減率"] = (
        (changes["終了人口"] - changes["開始人口"])
        / changes["開始人口"]
        * 100
    )
    changes["高齢化率変化"] = (
        changes["終了高齢化率"]
        - changes["開始高齢化率"]
    )
    return changes


def find_offset_ward(factors: pd.DataFrame) -> pd.Series | None:
    if factors.empty:
        return None

    candidates = factors.loc[
        (factors["社会増減"] > 0)
        & (factors["自然増減"] < 0)
        & (factors["人口増減"] > 0)
    ].copy()

    if candidates.empty:
        return None

    candidates["補填余力"] = (
        candidates["社会増減"]
        - candidates["自然増減"].abs()
    )
    return candidates.nlargest(1, "補填余力").iloc[0]


def pair_index_chart(
    data: pd.DataFrame,
    first: pd.Series,
    second: pd.Series,
) -> alt.Chart:
    medians = {
        "人口": float(data["人口"].median()),
        "高齢化率": float(data["高齢化率"].median()),
        "人口密度": float(data["人口密度"].median()),
    }

    rows: list[dict[str, object]] = []
    for row in (first, second):
        for metric in ("人口", "高齢化率", "人口密度"):
            rows.append(
                {
                    "自治体": row["自治体"],
                    "指標": metric,
                    "指数": float(row[metric]) / medians[metric] * 100,
                }
            )

    chart_data = pd.DataFrame(rows)
    baseline = (
        alt.Chart(pd.DataFrame({"基準": [100]}))
        .mark_rule(color="#7D8998", strokeDash=[5, 4])
        .encode(x="基準:Q")
    )
    bars = (
        alt.Chart(chart_data)
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            x=alt.X(
                "指数:Q",
                title="23区中央値＝100",
                axis=alt.Axis(gridColor="#E7EBF0"),
            ),
            y=alt.Y("指標:N", title=None),
            color=alt.Color(
                "自治体:N",
                scale=alt.Scale(range=["#315F7B", "#A55D39"]),
                legend=alt.Legend(title=None, orient="top"),
            ),
            yOffset="自治体:N",
            tooltip=[
                alt.Tooltip("自治体:N"),
                alt.Tooltip("指標:N"),
                alt.Tooltip("指数:Q", format=".1f"),
            ],
        )
    )
    return (
        (bars + baseline)
        .properties(height=300)
        .configure_view(strokeOpacity=0)
        .configure(background="transparent")
    )


def change_scatter(
    changes: pd.DataFrame,
    highlighted_wards: list[str],
) -> alt.Chart:
    chart_data = changes.copy()
    chart_data["注目"] = chart_data["自治体"].isin(highlighted_wards)

    return (
        alt.Chart(chart_data)
        .mark_circle(stroke="#FFFFFF", strokeWidth=1.2, opacity=0.88)
        .encode(
            x=alt.X(
                "人口増減率:Q",
                title="人口増減率（%）",
                axis=alt.Axis(gridColor="#E8ECF1"),
            ),
            y=alt.Y(
                "高齢化率変化:Q",
                title="高齢化率変化（pt）",
                axis=alt.Axis(gridColor="#E8ECF1"),
            ),
            size=alt.condition(
                alt.datum.注目,
                alt.value(320),
                alt.value(95),
            ),
            color=alt.condition(
                alt.datum.注目,
                alt.value("#A55D39"),
                alt.value("#527997"),
            ),
            tooltip=[
                alt.Tooltip("自治体:N"),
                alt.Tooltip("人口増減率:Q", format="+.2f"),
                alt.Tooltip("高齢化率変化:Q", format="+.2f"),
            ],
        )
        .properties(height=390)
        .configure_view(strokeOpacity=0)
        .configure(background="transparent")
    )


def factor_chart(row: pd.Series) -> alt.Chart:
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
                axis=alt.Axis(gridColor="#E8ECF1"),
            ),
            y=alt.Y(
                "要因:N",
                title=None,
                sort=["社会増減", "自然増減", "その他増減"],
            ),
            color=alt.Color(
                "要因:N",
                scale=alt.Scale(
                    domain=["社会増減", "自然増減", "その他増減"],
                    range=["#315F7B", "#A55D39", "#8A95A4"],
                ),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("要因:N"),
                alt.Tooltip("人数:Q", format="+,.0f"),
            ],
        )
    )
    zero = (
        alt.Chart(pd.DataFrame({"基準": [0]}))
        .mark_rule(color="#6F7C8C", strokeDash=[4, 4])
        .encode(x="基準:Q")
    )
    return (
        (bars + zero)
        .properties(height=270)
        .configure_view(strokeOpacity=0)
        .configure(background="transparent")
    )


def progress_html(current_step: int) -> str:
    items = []
    for index, label in enumerate(STEP_LABELS):
        class_name = (
            "demo-progress-item active"
            if index == current_step
            else "demo-progress-item"
        )
        items.append(
            f'<div class="{class_name}">'
            f'{index + 1}. {escape(label)}</div>'
        )
    return '<div class="demo-progress">' + "".join(items) + "</div>"


def ward_cards_html(first: pd.Series, second: pd.Series) -> str:
    return f"""
    <div class="demo-ward-grid">
        <div class="demo-ward">
            <div class="demo-ward-name">{escape(str(first['自治体']))}</div>
            <div class="demo-ward-value">
                人口 {float(first['人口']):,.0f}人<br>
                高齢化率 {float(first['高齢化率']):.2f}%<br>
                人口密度 {float(first['人口密度']):,.0f}人/km²
            </div>
        </div>
        <div class="demo-ward">
            <div class="demo-ward-name">{escape(str(second['自治体']))}</div>
            <div class="demo-ward-value">
                人口 {float(second['人口']):,.0f}人<br>
                高齢化率 {float(second['高齢化率']):.2f}%<br>
                人口密度 {float(second['人口密度']):,.0f}人/km²
            </div>
        </div>
    </div>
    """


def render_step_one(data: pd.DataFrame) -> None:
    first, second = find_similar_population_pair(data)
    population_gap = abs(float(first["人口"]) - float(second["人口"]))
    aging_gap = abs(
        float(first["高齢化率"])
        - float(second["高齢化率"])
    )

    st.markdown(
        '<div class="demo-question">問い1：人口規模が近ければ、区の特徴も近いのか</div>',
        unsafe_allow_html=True,
    )
    st.markdown(ward_cards_html(first, second), unsafe_allow_html=True)
    st.altair_chart(
        pair_index_chart(data, first, second),
        width="stretch",
    )
    st.markdown(
        (
            '<div class="demo-finding">'
            f'<strong>{escape(str(first["自治体"]))}と'
            f'{escape(str(second["自治体"]))}</strong>は、'
            f"人口差が約{population_gap:,.0f}人ですが、"
            f"高齢化率には{aging_gap:.2f}ptの差があります。"
            "人口だけを見ても、都市構造の違いは十分に分かりません。"
            "</div>"
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        (
            '<div class="demo-script">'
            '<div class="demo-script-label">説明するときの一言</div>'
            "同じくらいの人口規模でも、高齢化率や人口密度は異なります。"
            "そこで本アプリは、実数と23区中央値を基準にした指数を併用しています。"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_step_two(history: pd.DataFrame) -> None:
    changes = history_changes(history)
    growth = changes.nlargest(1, "人口増減率").iloc[0]
    aging = changes.nlargest(1, "高齢化率変化").iloc[0]
    highlighted = list(
        dict.fromkeys([str(growth["自治体"]), str(aging["自治体"])])
    )

    st.markdown(
        '<div class="demo-question">問い2：人口増加と高齢化は、同じ方向に動くのか</div>',
        unsafe_allow_html=True,
    )
    st.altair_chart(
        change_scatter(changes, highlighted),
        width="stretch",
    )
    st.markdown(
        (
            '<div class="demo-finding">'
            f"人口増減率が最も高いのは"
            f'<strong>{escape(str(growth["自治体"]))}</strong>'
            f"（{float(growth['人口増減率']):+.2f}%）。"
            f"高齢化率の上昇幅が最も大きいのは"
            f'<strong>{escape(str(aging["自治体"]))}</strong>'
            f"（{float(aging['高齢化率変化']):+.2f}pt）です。"
            "人口変化と高齢化は一つの軸だけでは整理できません。"
            "</div>"
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        (
            '<div class="demo-script">'
            '<div class="demo-script-label">説明するときの一言</div>'
            "単年度の順位だけでは見えないため、同じ期間で人口と高齢化率の変化を並べました。"
            "散布図は因果を示すものではなく、次に調べる区を見つけるために使っています。"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_step_three(factors: pd.DataFrame) -> None:
    row = find_offset_ward(factors)

    st.markdown(
        '<div class="demo-question">問い3：自然減でも、人口は増えるのか</div>',
        unsafe_allow_html=True,
    )

    if row is None:
        st.warning("要因分析データから該当する区を抽出できませんでした。")
        return

    st.altair_chart(factor_chart(row), width="stretch")
    st.markdown(
        (
            '<div class="demo-finding">'
            f'<strong>{escape(str(row["自治体"]))}</strong>は、'
            f"自然増減が{float(row['自然増減']):+,.0f}人でも、"
            f"社会増減が{float(row['社会増減']):+,.0f}人となり、"
            f"人口全体では{float(row['人口増減']):+,.0f}人です。"
            "人口の増減は、出生・死亡だけでなく、人の移動を分けて見る必要があります。"
            "</div>"
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        (
            '<div class="demo-script">'
            '<div class="demo-script-label">説明するときの一言</div>'
            "人口が増えたという結果だけではなく、社会増減・自然増減・その他増減へ分解しました。"
            "自然増減＝出生－死亡などの整合式もコードで検証しています。"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_step_four() -> None:
    st.markdown(
        '<div class="demo-question">最後：どのように実装し、壊れた箇所を直したか</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="demo-pipeline">
            <div class="demo-pipeline-item">
                <div class="demo-pipeline-no">1</div>
                <div class="demo-pipeline-name">取得</div>
                <div class="demo-pipeline-note">東京都の公開統計と行政区域GeoJSON</div>
            </div>
            <div class="demo-pipeline-item">
                <div class="demo-pipeline-no">2</div>
                <div class="demo-pipeline-name">整形</div>
                <div class="demo-pipeline-note">自治体コードをキーにCSVを統合</div>
            </div>
            <div class="demo-pipeline-item">
                <div class="demo-pipeline-no">3</div>
                <div class="demo-pipeline-name">検証</div>
                <div class="demo-pipeline-note">欠損・重複・値域・増減式をテスト</div>
            </div>
            <div class="demo-pipeline-item">
                <div class="demo-pipeline-no">4</div>
                <div class="demo-pipeline-name">公開</div>
                <div class="demo-pipeline-note">Streamlit CloudとGitHub Actions</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="demo-finding">
            <strong>実装中に直した主な問題</strong><br>
            経年地図のポリゴン崩れは描画方式を変更し、類似区計算の型エラーは数値型を明示して修正しました。
            タブ切替時の遅さには、遅延読み込みとキャッシュを導入しました。
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="demo-script">
            <div class="demo-script-label">説明するときの一言</div>
            完成画面だけでなく、取得・検証・エラー修正・公開まで再現できる構成にしました。
            次は住宅、地価、年齢階級別人口を加え、人口変化の背景をさらに説明したいです。
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_demo_tab(
    current_data: pd.DataFrame,
    history: pd.DataFrame,
    factor_path: str,
) -> None:
    st.markdown(DEMO_STYLE, unsafe_allow_html=True)

    factors = load_demo_factors(factor_path)

    st.markdown(
        """
        <div class="demo-head">
            <h2 class="demo-title">3分で見る、このアプリの考え方</h2>
            <p class="demo-lead">
                画面を順番に説明するためのデモです。
                3つの問いを通して、比較・経年変化・人口増減要因を確認し、
                最後に実装と検証をまとめます。
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "demo_step" not in st.session_state:
        st.session_state["demo_step"] = 0

    selected_label = st.radio(
        "デモの項目",
        STEP_LABELS,
        index=int(st.session_state["demo_step"]),
        horizontal=True,
        label_visibility="collapsed",
        key="demo_step_radio",
    )
    step = STEP_LABELS.index(selected_label)
    st.session_state["demo_step"] = step

    st.markdown(progress_html(step), unsafe_allow_html=True)

    if step == 0:
        render_step_one(current_data)
    elif step == 1:
        render_step_two(history)
    elif step == 2:
        render_step_three(factors)
    else:
        render_step_four()

    previous_column, spacer, next_column = st.columns([0.2, 0.6, 0.2])
    with previous_column:
        if st.button(
            "← 前へ",
            disabled=step == 0,
            use_container_width=True,
            key="demo_previous",
        ):
            st.session_state["demo_step"] = max(0, step - 1)
            st.session_state["demo_step_radio"] = STEP_LABELS[
                st.session_state["demo_step"]
            ]
            st.rerun()

    with next_column:
        if st.button(
            "次へ →",
            disabled=step == len(STEP_LABELS) - 1,
            use_container_width=True,
            key="demo_next",
        ):
            st.session_state["demo_step"] = min(
                len(STEP_LABELS) - 1,
                step + 1,
            )
            st.session_state["demo_step_radio"] = STEP_LABELS[
                st.session_state["demo_step"]
            ]
            st.rerun()
