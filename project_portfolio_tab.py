from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


STYLE = """
<style>
.project-head {
    padding: 0.25rem 0 1.15rem;
    border-bottom: 1px solid #D8DEE7;
    margin-bottom: 1.3rem;
}
.project-label {
    color: #6B7280;
    font-size: 0.73rem;
    font-weight: 700;
    letter-spacing: 0.13em;
    margin-bottom: 0.45rem;
}
.project-title {
    color: #172033;
    font-size: clamp(1.7rem, 3vw, 2.45rem);
    line-height: 1.15;
    letter-spacing: -0.035em;
    margin: 0;
}
.project-lead {
    color: #5D6675;
    max-width: 800px;
    line-height: 1.8;
    margin: 0.7rem 0 0;
}
.project-section {
    margin: 1.15rem 0 0.55rem;
}
.project-section-no {
    color: #8A93A1;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.13em;
}
.project-section-title {
    color: #172033;
    font-size: 1.15rem;
    font-weight: 720;
    margin-top: 0.12rem;
}
.project-flow {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    border-top: 1px solid #D8DEE7;
    border-bottom: 1px solid #D8DEE7;
    margin: 0.65rem 0 1.2rem;
}
.project-flow-item {
    padding: 1rem 0.9rem;
    border-right: 1px solid #D8DEE7;
}
.project-flow-item:last-child { border-right: 0; }
.project-flow-step {
    color: #8A93A1;
    font-size: 0.7rem;
    letter-spacing: 0.12em;
    font-weight: 700;
}
.project-flow-name {
    color: #172033;
    font-size: 0.98rem;
    font-weight: 700;
    margin-top: 0.3rem;
}
.project-flow-note {
    color: #697386;
    font-size: 0.79rem;
    line-height: 1.55;
    margin-top: 0.25rem;
}
.project-note {
    border-left: 3px solid #315B78;
    padding: 0.78rem 0 0.78rem 1rem;
    color: #334155;
    line-height: 1.75;
    background: rgba(255, 255, 255, 0.55);
    margin: 0.6rem 0;
}
.project-decision {
    border-top: 1px solid #DFE4EA;
    padding: 0.78rem 0.1rem;
}
.project-decision:last-child { border-bottom: 1px solid #DFE4EA; }
.project-decision strong {
    display: block;
    color: #172033;
    margin-bottom: 0.2rem;
}
.project-decision span {
    color: #667080;
    font-size: 0.87rem;
    line-height: 1.65;
}
.project-report {
    border: 1px solid #D8DEE7;
    background: #FFFFFF;
    padding: 1.1rem 1.15rem;
    border-radius: 10px;
}
.project-report h4 {
    margin: 0 0 0.6rem;
    color: #172033;
}
.project-report-row {
    display: grid;
    grid-template-columns: 9rem 1fr;
    gap: 0.75rem;
    padding: 0.48rem 0;
    border-top: 1px solid #E5E9EE;
}
.project-report-key {
    color: #6B7280;
    font-size: 0.82rem;
}
.project-report-value {
    color: #1F2937;
    font-size: 0.88rem;
    font-weight: 650;
}
.project-source {
    color: #737C89;
    font-size: 0.77rem;
    line-height: 1.7;
    margin-top: 1rem;
}
@media (max-width: 900px) {
    .project-flow { grid-template-columns: 1fr 1fr; }
    .project-flow-item:nth-child(2) { border-right: 0; }
    .project-flow-item:nth-child(-n+2) { border-bottom: 1px solid #D8DEE7; }
}
</style>
"""


def _section(number: str, title: str) -> None:
    st.markdown(
        (
            '<div class="project-section">'
            f'<div class="project-section-no">{escape(number)}</div>'
            f'<div class="project-section-title">{escape(title)}</div>'
            "</div>"
        ),
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def _load_factors(path: str) -> pd.DataFrame:
    source = Path(path)
    if not source.exists():
        return pd.DataFrame()
    frame = pd.read_csv(source, dtype={"自治体コード": str})
    frame["自治体コード"] = frame["自治体コード"].str.zfill(5)
    return frame


def _rank(data: pd.DataFrame, ward: str, column: str) -> int:
    ranked = data[column].rank(method="min", ascending=False).astype(int)
    return int(ranked.loc[data["自治体"].eq(ward)].iloc[0])


def _first_last(history: pd.DataFrame, ward: str) -> tuple[pd.Series, pd.Series]:
    selected = history.loc[history["自治体"].eq(ward)].sort_values("年")
    return selected.iloc[0], selected.iloc[-1]


def _signed(value: float, unit: str = "人") -> str:
    return f"{value:+,.0f}{unit}"


def _report_values(
    current_data: pd.DataFrame,
    history: pd.DataFrame,
    factors: pd.DataFrame,
    ward: str,
) -> dict[str, Any]:
    current = current_data.loc[current_data["自治体"].eq(ward)].iloc[0]
    first, last = _first_last(history, ward)

    population_change = float(last["人口"] - first["人口"])
    population_change_rate = population_change / float(first["人口"]) * 100
    aging_change = float(last["高齢化率"] - first["高齢化率"])

    values: dict[str, Any] = {
        "ward": ward,
        "start_year": int(first["年"]),
        "end_year": int(last["年"]),
        "population": float(current["人口"]),
        "population_rank": _rank(current_data, ward, "人口"),
        "aging": float(current["高齢化率"]),
        "aging_rank": _rank(current_data, ward, "高齢化率"),
        "density": float(current["人口密度"]),
        "density_rank": _rank(current_data, ward, "人口密度"),
        "population_change": population_change,
        "population_change_rate": population_change_rate,
        "aging_change": aging_change,
    }

    if not factors.empty and ward in set(factors["自治体"]):
        factor = factors.loc[factors["自治体"].eq(ward)].iloc[0]
        values.update(
            {
                "factor_year": int(factor["年"]),
                "social_change": float(factor["社会増減"]),
                "natural_change": float(factor["自然増減"]),
                "other_change": float(factor["その他増減"]),
                "births": float(factor["出生数"]),
                "deaths": float(factor["死亡数"]),
                "factor_total": float(factor["人口増減"]),
            }
        )
    return values


def _interpretation(values: dict[str, Any]) -> str:
    change = values["population_change"]
    aging = values["aging_change"]

    population_text = (
        "増加" if change > 0 else "減少" if change < 0 else "横ばい"
    )
    aging_text = (
        "上昇" if aging > 0 else "低下" if aging < 0 else "横ばい"
    )
    sentence = (
        f"{values['start_year']}年から{values['end_year']}年にかけて人口は"
        f"{population_text}し、高齢化率は{aging_text}しています。"
    )

    if "social_change" in values:
        social = values["social_change"]
        natural = values["natural_change"]
        if social > 0 and natural < 0:
            sentence += " 2025年は社会増が自然減を補う構造です。"
        elif social > 0 and natural >= 0:
            sentence += " 2025年は社会増と自然増がともに人口を押し上げています。"
        elif social <= 0 and natural < 0:
            sentence += " 2025年は社会減と自然減が重なっています。"
        else:
            sentence += " 2025年は自然増が社会減を補っています。"
    return sentence


def _report_html(values: dict[str, Any]) -> str:
    factor_rows = ""
    if "social_change" in values:
        factor_rows = f"""
        <tr><th>2025年の社会増減</th><td>{_signed(values['social_change'])}</td></tr>
        <tr><th>2025年の自然増減</th><td>{_signed(values['natural_change'])}</td></tr>
        <tr><th>2025年の出生・死亡</th><td>{values['births']:,.0f}人 / {values['deaths']:,.0f}人</td></tr>
        """

    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(values['ward'])} 都市データレポート</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Hiragino Sans", sans-serif; color:#172033; margin:0; background:#F5F7F9; }}
main {{ max-width:820px; margin:40px auto; background:white; padding:42px 48px; border:1px solid #D8DEE7; }}
small {{ color:#6B7280; letter-spacing:.08em; }}
h1 {{ margin:.4rem 0 .6rem; font-size:2rem; }}
.lead {{ color:#4B5563; line-height:1.8; border-left:3px solid #315B78; padding-left:1rem; }}
table {{ border-collapse:collapse; width:100%; margin-top:1.5rem; }}
th, td {{ padding:.75rem .3rem; border-top:1px solid #E2E6EB; text-align:left; }}
th {{ color:#6B7280; width:42%; font-weight:500; }}
td {{ font-weight:650; }}
.note {{ margin-top:1.5rem; color:#6B7280; font-size:.85rem; line-height:1.7; }}
</style>
</head>
<body>
<main>
<small>TOKYO 23 WARDS / WARD REPORT</small>
<h1>{escape(values['ward'])}</h1>
<p class="lead">{escape(_interpretation(values))}</p>
<table>
<tr><th>人口</th><td>{values['population']:,.0f}人（23区中 {values['population_rank']}位）</td></tr>
<tr><th>高齢化率</th><td>{values['aging']:.2f}%（23区中 {values['aging_rank']}位）</td></tr>
<tr><th>人口密度</th><td>{values['density']:,.0f}人/km²（23区中 {values['density_rank']}位）</td></tr>
<tr><th>{values['start_year']}〜{values['end_year']}年の人口増減</th><td>{_signed(values['population_change'])}（{values['population_change_rate']:+.2f}%）</td></tr>
<tr><th>{values['start_year']}〜{values['end_year']}年の高齢化率変化</th><td>{values['aging_change']:+.2f}pt</td></tr>
{factor_rows}
</table>
<p class="note">出典：東京都の公開統計。指標間の関係や増減要因は、因果関係を直接示すものではありません。</p>
</main>
</body>
</html>"""


def _preview(values: dict[str, Any]) -> str:
    rows = [
        ("人口", f"{values['population']:,.0f}人（23区中 {values['population_rank']}位）"),
        ("高齢化率", f"{values['aging']:.2f}%（23区中 {values['aging_rank']}位）"),
        ("人口密度", f"{values['density']:,.0f}人/km²（23区中 {values['density_rank']}位）"),
        (
            f"{values['start_year']}〜{values['end_year']}年",
            f"人口 {_signed(values['population_change'])} / 高齢化率 {values['aging_change']:+.2f}pt",
        ),
    ]
    if "social_change" in values:
        rows.append(
            (
                "2025年の要因",
                f"社会増減 {_signed(values['social_change'])} / "
                f"自然増減 {_signed(values['natural_change'])}",
            )
        )

    body = "".join(
        (
            '<div class="project-report-row">'
            f'<div class="project-report-key">{escape(key)}</div>'
            f'<div class="project-report-value">{escape(value)}</div>'
            "</div>"
        )
        for key, value in rows
    )
    return (
        '<div class="project-report">'
        f"<h4>{escape(values['ward'])}の要約</h4>"
        f'<div class="project-note">{escape(_interpretation(values))}</div>'
        f"{body}</div>"
    )


def render_project_tab(
    current_data: pd.DataFrame,
    history: pd.DataFrame,
    geojson: dict,
    factor_path: str,
    live_app_url: str = "",
) -> None:
    del geojson  # 境界データは構成説明で扱い、ここでは描画しない。
    st.markdown(STYLE, unsafe_allow_html=True)

    start_year = int(history["年"].min())
    end_year = int(history["年"].max())
    factors = _load_factors(factor_path)

    st.markdown(
        (
            '<div class="project-head">'
            '<div class="project-label">PROJECT OVERVIEW</div>'
            '<h2 class="project-title">このプロジェクトについて</h2>'
            '<p class="project-lead">'
            "東京都の公開統計を、区ごとの比較と時系列の両方から確認するために作成しました。"
            "数値を並べるだけでなく、地図、比較、構造、経年変化、人口増減要因まで"
            "同じ画面でたどれるようにしています。"
            "</p></div>"
        ),
        unsafe_allow_html=True,
    )

    _section("01 / PURPOSE", "解決したかったこと")
    st.markdown(
        (
            '<div class="project-note">'
            "公開統計は信頼できる一方、表が分かれており、区同士の違いや時間変化を"
            "一度に把握しにくいという課題があります。本アプリでは、"
            "「どの区が違うのか」「いつ変わったのか」「何が人口変化に寄与したのか」を"
            "順番に確認できる構成にしました。"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    _section("02 / PIPELINE", "データから画面まで")
    st.markdown(
        (
            '<div class="project-flow">'
            '<div class="project-flow-item"><div class="project-flow-step">STEP 01</div>'
            '<div class="project-flow-name">取得</div>'
            '<div class="project-flow-note">東京都の公開統計と行政区域GeoJSON</div></div>'
            '<div class="project-flow-item"><div class="project-flow-step">STEP 02</div>'
            '<div class="project-flow-name">整形</div>'
            '<div class="project-flow-note">自治体コードをキーにCSVを統合</div></div>'
            '<div class="project-flow-item"><div class="project-flow-step">STEP 03</div>'
            '<div class="project-flow-name">検証</div>'
            '<div class="project-flow-note">23区数、重複、欠損、増減式を確認</div></div>'
            '<div class="project-flow-item"><div class="project-flow-step">STEP 04</div>'
            '<div class="project-flow-name">可視化</div>'
            '<div class="project-flow-note">Streamlit、Altair、PyDeckで実装</div></div>'
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    summary_columns = st.columns(4)
    summary_columns[0].metric("自治体", f"{current_data['自治体'].nunique()}区")
    summary_columns[1].metric("収録期間", f"{start_year}–{end_year}")
    summary_columns[2].metric("経年レコード", f"{len(history):,}件")
    summary_columns[3].metric("分析画面", "7タブ")

    _section("03 / DECISIONS", "設計上の判断")
    decisions = [
        (
            "絶対値と指数を使い分ける",
            "人口・高齢化率・人口密度は単位が異なるため、実数に加えて23区中央値を100とする指数でも比較します。",
        ),
        (
            "分類や相関の限界を画面内に書く",
            "中央値による都市タイプや相関係数は探索の手掛かりであり、政策評価や因果関係を直接示さないことを明記しています。",
        ),
        (
            "元データの整合性を自動で確認する",
            "自治体数、重複、欠損、値の範囲に加え、自然増減＝出生数－死亡数などの関係を検証します。",
        ),
        (
            "重い処理を必要な画面だけで実行する",
            "タブの遅延読み込みとキャッシュを使い、地図や経年計算を毎回すべて再実行しない構成にしました。",
        ),
    ]
    st.markdown(
        "".join(
            (
                '<div class="project-decision">'
                f"<strong>{escape(title)}</strong>"
                f"<span>{escape(note)}</span></div>"
            )
            for title, note in decisions
        ),
        unsafe_allow_html=True,
    )

    _section("04 / ITERATION", "実装中に直したこと")
    iteration_left, iteration_right = st.columns(2, gap="large")
    with iteration_left:
        st.markdown(
            """
**表示と操作**
- 地図だけの構成から、比較・構造・経年・要因分析へ拡張
- 経年地図の描画崩れを、軽量なGeoJSON地図へ置換
- 説明文と配色を見直し、機能が先に伝わる画面へ修正
"""
        )
    with iteration_right:
        st.markdown(
            """
**データと処理**
- 類似区計算の型エラーを数値変換で修正
- 公式CSVの取得・整形処理をスクリプト化
- バリデーションとGitHub Actionsで再現性を確認
"""
        )

    st.divider()
    _section("05 / WARD REPORT", "区別レポートを作る")
    st.caption(
        "現在値、長期変化、2025年の人口増減要因を一枚にまとめます。"
        "HTMLはブラウザで開き、印刷からPDFとして保存できます。"
    )
    ward_names = current_data["自治体"].tolist()
    ward = st.selectbox(
        "対象区",
        ward_names,
        index=ward_names.index("杉並区") if "杉並区" in ward_names else 0,
        key="project_report_ward",
    )
    values = _report_values(current_data, history, factors, ward)
    st.markdown(_preview(values), unsafe_allow_html=True)

    report_html = _report_html(values)
    st.download_button(
        "区別レポートをダウンロード",
        data=report_html.encode("utf-8"),
        file_name=f"{ward}_urban_data_report.html",
        mime="text/html",
        key="download_ward_report",
    )

    st.markdown(
        (
            '<div class="project-source">'
            f"収録範囲：東京23区、{start_year}〜{end_year}年。"
            "データ取得・加工手順と技術的な判断は、GitHubのPROJECT_STORY.mdに記載しています。"
            + (
                f' 公開版：<a href="{escape(live_app_url)}" target="_blank">{escape(live_app_url)}</a>'
                if live_app_url
                else ""
            )
            + "</div>"
        ),
        unsafe_allow_html=True,
    )
