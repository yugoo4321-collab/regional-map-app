from __future__ import annotations

from datetime import date

import copy
import json
from html import escape
from pathlib import Path

import altair as alt
import pandas as pd
import pydeck as pdk
import streamlit as st

from population_factors_tab import render_population_factors_tab
from project_portfolio_tab import render_project_tab
from guided_demo_tab import render_demo_tab

DATA_PATH = Path("data/tokyo_wards.csv")
GEOJSON_PATH = Path("data/tokyo_wards.geojson")
HISTORY_PATH = Path("data/tokyo_wards_history.csv")
FACTORS_PATH = Path("data/tokyo_population_factors_2025.csv")
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

# PLAIN_HERO_COPY_V1
# ROBUST_PLAIN_HERO_TITLE_V1
st.set_page_config(
    page_title="東京23区データダッシュボード",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """<style>
/* PLAYFUL_HUMAN_TOUCH_V1 */
.hero-eyebrow {
    display: inline-flex !important;
    width: fit-content !important;
    align-items: center !important;
    padding: 0.36rem 0.66rem !important;
    margin: 0 0 0.9rem 0.1rem !important;
    border: 1.5px solid #315f7b !important;
    border-radius: 5px 8px 5px 7px !important;
    background: #fffdf7 !important;
    color: #274b63 !important;
    font-size: 0.76rem !important;
    font-weight: 750 !important;
    letter-spacing: 0.02em !important;
    transform: rotate(-1.15deg) !important;
    box-shadow: 3px 3px 0 rgba(49, 95, 123, 0.10) !important;
}

.hero::after,
.hero-shell::after,
.hero-panel::after {
    content: "" !important;
    position: absolute !important;
    right: 1.7rem !important;
    top: 1.45rem !important;
    width: 74px !important;
    height: 34px !important;
    opacity: 0.7 !important;
    background:
        radial-gradient(circle, #b9663d 0 2px, transparent 2.5px)
        0 0 / 15px 15px !important;
    transform: rotate(5deg) !important;
    pointer-events: none !important;
}

.play-zone {
    margin: 0.85rem 0 1rem;
}

.play-zone-head {
    display: flex;
    justify-content: space-between;
    align-items: end;
    gap: 1rem;
    margin-bottom: 0.55rem;
}

.play-zone-title {
    color: #17263a;
    font-size: 0.94rem;
    font-weight: 760;
}

.play-zone-note {
    color: #6b7687;
    font-size: 0.76rem;
}

.play-rail {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.72rem;
}

.play-card {
    --card-accent: #315f7b;
    position: relative;
    min-height: 148px;
    overflow: hidden;
    padding: 0.9rem 0.95rem 0.85rem;
    border: 1px solid #cfd8e1;
    border-radius: 9px 12px 8px 11px;
    background:
        linear-gradient(145deg, rgba(255,255,255,0.98), rgba(247,249,251,0.96)),
        repeating-linear-gradient(
            -12deg,
            transparent 0 12px,
            rgba(45, 70, 90, 0.018) 12px 13px
        );
    box-shadow: 0 5px 15px rgba(31, 47, 65, 0.045);
    transition:
        transform 180ms cubic-bezier(.2,.8,.2,1),
        box-shadow 180ms ease,
        border-color 180ms ease;
    scroll-snap-align: start;
}

.play-card:nth-child(2) {
    --card-accent: #a55d39;
    transform: rotate(0.2deg);
}

.play-card:nth-child(3) {
    --card-accent: #6c648f;
    transform: rotate(-0.18deg);
}

.play-card::before {
    content: "";
    position: absolute;
    left: 0.85rem;
    top: 0;
    width: 38px;
    height: 4px;
    background: var(--card-accent);
    border-radius: 0 0 4px 4px;
}

.play-card:hover {
    transform: translateY(-3px) rotate(-0.25deg);
    border-color: #b8c6d3;
    box-shadow: 0 10px 22px rgba(31, 47, 65, 0.085);
}

.play-card-label {
    color: var(--card-accent);
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    margin-bottom: 0.38rem;
}

.play-card-title {
    color: #17263a;
    font-size: 1.05rem;
    font-weight: 780;
    line-height: 1.35;
    margin-bottom: 0.42rem;
}

.play-card-copy {
    color: #566477;
    font-size: 0.8rem;
    line-height: 1.62;
}

.play-card-facts {
    display: flex;
    flex-wrap: wrap;
    gap: 0.34rem;
    margin-top: 0.62rem;
}

.play-fact {
    padding: 0.22rem 0.42rem;
    border: 1px solid #d7dfe7;
    border-radius: 4px 6px 4px 5px;
    background: rgba(255,255,255,0.78);
    color: #35465a;
    font-size: 0.7rem;
    font-weight: 650;
}

.play-card details {
    margin-top: 0.56rem;
}

.play-card summary {
    width: fit-content;
    cursor: pointer;
    color: #315f7b;
    font-size: 0.76rem;
    font-weight: 750;
    list-style: none;
    border-bottom: 1px dashed #6f8fa4;
}

.play-card summary::-webkit-details-marker {
    display: none;
}

.play-answer {
    margin-top: 0.45rem;
    padding: 0.48rem 0.55rem;
    background: #fffaf2;
    border-left: 3px solid #a55d39;
    color: #3f4d5e;
    font-size: 0.78rem;
    line-height: 1.55;
}

div[data-testid="stButton"] button[kind="secondary"] {
    border: 1px solid #315f7b !important;
}

div[data-testid="stButton"] button:hover {
    transform: translateY(-1px) rotate(-0.2deg);
}

.gacha-caption {
    color: #667487;
    font-size: 0.76rem;
    line-height: 1.55;
    padding-top: 0.2rem;
}

@keyframes playCardIn {
    from {
        opacity: 0;
        transform: translateY(7px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.play-card {
    animation: playCardIn 360ms ease both;
}

.play-card:nth-child(2) {
    animation-delay: 55ms;
}

.play-card:nth-child(3) {
    animation-delay: 110ms;
}

@media (max-width: 850px) {
    .play-rail {
        display: flex;
        overflow-x: auto;
        scroll-snap-type: x mandatory;
        padding-bottom: 0.35rem;
    }

    .play-card {
        min-width: min(82vw, 330px);
    }

    .hero::after,
    .hero-shell::after,
    .hero-panel::after {
        display: none !important;
    }
}

@media (prefers-reduced-motion: reduce) {
    .play-card {
        animation: none !important;
        transition: none !important;
    }

    .play-card:hover,
    div[data-testid="stButton"] button:hover {
        transform: none !important;
    }
}
</style>""",
    unsafe_allow_html=True,
)

st.markdown(
    """<style>
/* BALANCED_VISUAL_POLISH_V1 */
:root {
    --ui-bg: #eef2f6;
    --ui-paper: #ffffff;
    --ui-paper-soft: #f7f9fb;
    --ui-ink: #152235;
    --ui-body: #3f4d5f;
    --ui-muted: #687487;
    --ui-line: #d4dce5;
    --ui-line-strong: #bdc9d6;
    --ui-accent: #2f5f7d;
    --ui-accent-soft: #e6eef3;
    --ui-warm: #a95f38;
}

.stApp {
    background:
        linear-gradient(180deg, #e9eef3 0, #f3f5f7 260px, #f3f5f7 100%) !important;
}

.block-container {
    max-width: 1320px !important;
    padding-top: 1.25rem !important;
    padding-bottom: 4rem !important;
}

/* トップ：装飾ではなく、情報誌の表紙程度の強弱 */
.hero,
.hero-shell,
.hero-panel {
    position: relative !important;
    overflow: hidden !important;
    background:
        linear-gradient(115deg, #ffffff 0%, #f5f8fa 70%, #edf3f6 100%) !important;
    border: 1px solid var(--ui-line-strong) !important;
    border-radius: 12px !important;
    box-shadow: 0 12px 30px rgba(31, 47, 65, 0.07) !important;
    padding: 1.65rem 1.75rem 1.5rem !important;
}

.hero::before,
.hero-shell::before,
.hero-panel::before {
    content: "" !important;
    position: absolute !important;
    inset: 0 auto 0 0 !important;
    width: 6px !important;
    background: var(--ui-accent) !important;
}

.hero h1,
.hero-title,
.hero-heading {
    color: var(--ui-ink) !important;
    font-size: clamp(2.1rem, 3.5vw, 3.15rem) !important;
    line-height: 1.08 !important;
    letter-spacing: -0.045em !important;
    font-weight: 800 !important;
    margin: 0 0 0.9rem !important;
    text-shadow: none !important;
}

.hero p,
.hero-copy,
.hero-description {
    color: var(--ui-body) !important;
    font-size: 1rem !important;
    line-height: 1.8 !important;
    max-width: 850px !important;
}

.hero a,
.hero button,
.hero-chip,
.hero-tag {
    color: #29465c !important;
    background: #f7f9fb !important;
    border: 1px solid #cbd6df !important;
    border-radius: 5px !important;
    box-shadow: none !important;
}

/* 通常カード：質素すぎず、装飾過多にもならない */
.stat-card,
.panel,
.profile-card,
.highlight-card,
.discovery-card,
.similar-item,
.project-report,
.factor-kpi,
[data-testid="stMetric"] {
    background: var(--ui-paper) !important;
    border: 1px solid var(--ui-line) !important;
    border-radius: 10px !important;
    box-shadow: 0 5px 16px rgba(31, 47, 65, 0.055) !important;
}

.stat-card {
    position: relative !important;
    overflow: hidden !important;
}

.stat-card::after {
    content: "" !important;
    position: absolute !important;
    inset: 0 0 auto 0 !important;
    height: 3px !important;
    background: var(--ui-accent) !important;
    opacity: 0.72 !important;
}

.stat-label,
.stat-meta {
    color: #5d6a7c !important;
}

.stat-value {
    color: var(--ui-ink) !important;
}

/* 白地に白文字になっていたプロフィールを強制的に修正 */
.profile-card,
.profile-card * {
    text-shadow: none !important;
}

.profile-card {
    background:
        linear-gradient(180deg, #ffffff 0%, #f7f9fb 100%) !important;
    color: var(--ui-ink) !important;
    border-color: #cbd6df !important;
}

.profile-card .profile-kicker {
    color: var(--ui-accent) !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.04em !important;
    text-transform: none !important;
}

.profile-card .profile-name {
    color: var(--ui-ink) !important;
    opacity: 1 !important;
}

.profile-card .profile-summary {
    color: #465568 !important;
    opacity: 1 !important;
}

.profile-card .profile-row {
    border-top-color: #dce3ea !important;
}

.profile-card .profile-row span:first-child {
    color: #617084 !important;
    opacity: 1 !important;
}

.profile-card .profile-row span:last-child {
    color: #17263a !important;
    opacity: 1 !important;
}

.profile-card .type-badge {
    background: var(--ui-accent-soft) !important;
    border: 1px solid #c6d6e0 !important;
    color: #274e68 !important;
}

/* 説明・要点 */
.insight-strip,
.comparison-callout,
.factor-brief,
.project-note {
    color: #334357 !important;
    background: #f8fafb !important;
    border: 1px solid #d1dae3 !important;
    border-left: 4px solid var(--ui-accent) !important;
    border-radius: 7px !important;
    box-shadow: 0 3px 10px rgba(31, 47, 65, 0.035) !important;
}

.insight-strip strong {
    color: #214c69 !important;
}

.section-intro,
.source-note,
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p {
    color: #536276 !important;
    opacity: 1 !important;
}

/* 入力欄とタブ */
.control-panel {
    background: rgba(255, 255, 255, 0.82) !important;
    border: 1px solid var(--ui-line) !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 14px rgba(31, 47, 65, 0.04) !important;
}

[data-baseweb="select"] > div,
[data-baseweb="input"] > div {
    background: #ffffff !important;
    border-color: #cdd7e0 !important;
}

[data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #cdd6df !important;
}

[data-baseweb="tab"] {
    color: #566477 !important;
    border-radius: 0 !important;
}

[aria-selected="true"][data-baseweb="tab"] {
    color: #1d3f56 !important;
    background: transparent !important;
}

[aria-selected="true"][data-baseweb="tab"]::after {
    background: var(--ui-accent) !important;
}

/* グラフの周囲 */
[data-testid="stVegaLiteChart"],
[data-testid="stDeckGlJsonChart"],
[data-testid="stDataFrame"] {
    background: #ffffff !important;
    border: 1px solid #d4dce5 !important;
    border-radius: 10px !important;
    box-shadow: 0 5px 16px rgba(31, 47, 65, 0.045) !important;
    overflow: hidden !important;
}

/* 本文と見出しのコントラスト */
h1, h2, h3, h4 {
    color: var(--ui-ink) !important;
}

p, li {
    color: var(--ui-body);
}

hr {
    border-color: #d4dce5 !important;
}

/* 英字装飾は隠し、日本語の機能名を優先 */
.hero-eyebrow,
.factor-kicker,
.factor-section-number,
.project-label,
.project-section-no {
    display: none !important;
}

@media (max-width: 900px) {
    .hero,
    .hero-shell,
    .hero-panel {
        padding: 1.35rem 1.25rem !important;
    }

    .hero h1,
    .hero-title,
    .hero-heading {
        font-size: 2.15rem !important;
        white-space: normal !important;
    }
}
</style>""",
    unsafe_allow_html=True,
)

st.markdown(
    """<style>
/* FINAL_HOMEPAGE_POLISH_V2 */
.hero,
.hero-shell,
.hero-panel {
    padding: 1.35rem 1.5rem 1.2rem !important;
    min-height: 0 !important;
}

.hero h1,
.hero-title,
.hero-heading {
    color: #172033 !important;
    font-size: clamp(1.95rem, 3.15vw, 2.7rem) !important;
    line-height: 1.12 !important;
    letter-spacing: -0.045em !important;
    word-break: keep-all !important;
    overflow-wrap: normal !important;
    max-width: none !important;
    margin-bottom: 0.8rem !important;
}

.hero p,
.hero-copy,
.hero-description {
    color: #5F6876 !important;
    font-size: 0.96rem !important;
    line-height: 1.75 !important;
    max-width: 900px !important;
    margin-bottom: 0.9rem !important;
}

.hero a,
.hero button,
.hero-chip,
.hero-tag {
    font-size: 0.82rem !important;
    font-weight: 650 !important;
    background: #F4F6F8 !important;
    border: 1px solid #D7DDE5 !important;
    color: #2E3A49 !important;
    border-radius: 5px !important;
    box-shadow: none !important;
}

.journey-grid,
.journey-card {
    display: none !important;
}

.stat-card,
.highlight-card,
.discovery-card,
.profile-card {
    border-left: 1px solid #D9DEE5 !important;
    border-top: 1px solid #D9DEE5 !important;
}

.stat-card::before,
.highlight-card::before,
.discovery-card::before,
.profile-card::before {
    display: none !important;
}

.stat-card .value,
.stat-value,
.metric-value {
    color: #172033 !important;
    letter-spacing: -0.04em !important;
}

.block-container > div:first-child {
    padding-top: 0 !important;
}

[data-testid="stRadio"] label,
[data-testid="stSelectbox"] label {
    color: #485363 !important;
}

[data-baseweb="tab"] {
    color: #596474 !important;
}

[aria-selected="true"][data-baseweb="tab"] {
    color: #172033 !important;
}

@media (min-width: 1050px) {
    .hero h1,
    .hero-title,
    .hero-heading {
        white-space: nowrap !important;
    }
}

@media (max-width: 1049px) {
    .hero h1,
    .hero-title,
    .hero-heading {
        white-space: normal !important;
    }
}
</style>""",
    unsafe_allow_html=True,
)

st.markdown(
    '<style>\n/* FINAL_HUMAN_UI_V1 */\n:root {\n    --final-ink: #18202a;\n    --final-muted: #66707d;\n    --final-line: #d9dee5;\n    --final-paper: #ffffff;\n    --final-bg: #f4f6f8;\n    --final-accent: #315b78;\n}\n.stApp { background: var(--final-bg) !important; }\n.block-container {\n    max-width: 1320px !important;\n    padding-top: 1.2rem !important;\n}\nh1, h2, h3 {\n    color: var(--final-ink) !important;\n    letter-spacing: -0.025em !important;\n}\n.hero, .hero-shell, .hero-panel {\n    background: var(--final-paper) !important;\n    background-image: none !important;\n    color: var(--final-ink) !important;\n    border: 1px solid var(--final-line) !important;\n    border-radius: 10px !important;\n    box-shadow: none !important;\n    min-height: auto !important;\n    padding: 1.5rem 1.6rem !important;\n}\n.hero h1, .hero-title, .hero-heading {\n    color: var(--final-ink) !important;\n    font-size: clamp(2rem, 4vw, 3rem) !important;\n    line-height: 1.12 !important;\n    max-width: 1000px !important;\n}\n.hero p, .hero-copy, .hero-description {\n    color: var(--final-muted) !important;\n    max-width: 880px !important;\n    line-height: 1.75 !important;\n}\n.hero-eyebrow, .hero-visual, .hero-network, .hero-graphic,\n.urban-signal, .signal-board, .network-board,\n.factor-kicker, .factor-section-number,\n.project-label, .project-section-no {\n    display: none !important;\n}\n.hero [class*="network"], .hero [class*="signal"] {\n    display: none !important;\n}\n.stat-card, .panel, .profile-card, .journey-card,\n.highlight-card, .discovery-card, .similar-item,\n.factor-kpi, .project-report, [data-testid="stMetric"] {\n    background: var(--final-paper) !important;\n    background-image: none !important;\n    border: 1px solid var(--final-line) !important;\n    border-radius: 8px !important;\n    box-shadow: none !important;\n}\n.journey-card, .highlight-card, .discovery-card {\n    transform: none !important;\n}\n.insight-strip, .comparison-callout, .factor-brief, .project-note {\n    background: #fbfcfd !important;\n    border: 1px solid var(--final-line) !important;\n    border-left: 3px solid var(--final-accent) !important;\n    border-radius: 4px !important;\n    box-shadow: none !important;\n}\n.type-badge, .rank-chip, .hero-chip, .hero-tag, [class*="pill"] {\n    border-radius: 4px !important;\n    background: #f2f4f6 !important;\n    border: 1px solid var(--final-line) !important;\n    color: #334155 !important;\n}\n[data-baseweb="tab-list"] {\n    gap: 0 !important;\n    border-bottom: 1px solid var(--final-line) !important;\n}\n[data-baseweb="tab"] {\n    border-radius: 0 !important;\n    font-weight: 650 !important;\n    padding-left: 0.85rem !important;\n    padding-right: 0.85rem !important;\n}\n[data-testid="stButton"] button,\n[data-testid="stDownloadButton"] button {\n    border-radius: 6px !important;\n    box-shadow: none !important;\n}\n.factor-title, .project-title {\n    font-size: clamp(1.7rem, 3vw, 2.35rem) !important;\n}\n.factor-section-title, .project-section-title {\n    margin-top: 0 !important;\n}\n[data-testid="stDataFrame"] {\n    border-radius: 6px !important;\n    box-shadow: none !important;\n}\n@media (max-width: 900px) {\n    .hero, .hero-shell, .hero-panel {\n        padding: 1.2rem !important;\n        border-radius: 8px !important;\n    }\n}\n</style>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
        /* VISUAL_SYSTEM_V3 */
        :root {
            --ink: #0B1728;
            --muted: #65758A;
            --line: #DCE5EF;
            --navy: #071525;
            --navy-2: #0D2A48;
            --blue: #2563EB;
            --cyan: #55D5FF;
            --shadow-sm: 0 10px 28px rgba(11,23,40,.06);
            --shadow-lg: 0 34px 90px rgba(5,20,38,.22);
        }

        html { scroll-behavior: smooth; }

        .stApp {
            background:
                radial-gradient(circle at 8% 4%, rgba(79,140,255,.075), transparent 27rem),
                radial-gradient(circle at 94% 18%, rgba(56,189,248,.05), transparent 25rem),
                #F5F7FA;
        }

        .block-container {
            max-width: 1420px;
            padding-top: 1rem;
            padding-bottom: 5rem;
        }

        h1, h2, h3 {
            color: var(--ink);
            letter-spacing: -.045em;
        }

        [data-testid="stHeader"] {
            background: rgba(245,247,250,.78);
            backdrop-filter: blur(18px);
            border-bottom: 1px solid rgba(220,229,239,.65);
        }

        .hero {
            position: relative;
            isolation: isolate;
            display: grid;
            grid-template-columns: minmax(0,1.18fr) minmax(360px,.82fr);
            gap: 2.2rem;
            min-height: 430px;
            overflow: hidden;
            border: 1px solid rgba(114,155,200,.2);
            border-radius: 30px;
            padding: 3rem 3.1rem;
            margin: 0 0 1rem;
            background:
                radial-gradient(circle at 82% 12%, rgba(56,189,248,.24), transparent 28%),
                radial-gradient(circle at 10% 115%, rgba(37,99,235,.32), transparent 40%),
                linear-gradient(135deg,#06111E 0%,#0A2038 54%,#0C2C49 100%);
            box-shadow: var(--shadow-lg);
        }

        .hero::before {
            content: "";
            position: absolute;
            inset: 0;
            z-index: -2;
            opacity: .17;
            background-image:
                linear-gradient(rgba(255,255,255,.13) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,.13) 1px, transparent 1px);
            background-size: 42px 42px;
            mask-image: linear-gradient(90deg,#000 0%,rgba(0,0,0,.3) 68%,transparent 100%);
        }

        .hero-copy {
            display: flex;
            min-width: 0;
            flex-direction: column;
            justify-content: center;
        }

        .hero-eyebrow {
            display: inline-flex;
            width: fit-content;
            align-items: center;
            gap: .5rem;
            padding: .4rem .72rem;
            margin-bottom: 1.15rem;
            border: 1px solid rgba(148,197,238,.3);
            border-radius: 999px;
            background: rgba(255,255,255,.07);
            color: #B9D9F4;
            font-size: .73rem;
            font-weight: 760;
            letter-spacing: .11em;
        }

        .hero-eyebrow::before {
            content: "";
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #65D4FF;
            box-shadow: 0 0 0 5px rgba(101,212,255,.12);
        }

        .hero h1 {
            max-width: 820px;
            margin: 0;
            color: #F8FBFF;
            font-size: clamp(2.7rem,5.1vw,4.75rem);
            line-height: 1.02;
            letter-spacing: -.065em;
            font-weight: 820;
        }

        .hero h1 span { color: #83D7FF; }

        .hero p {
            max-width: 780px;
            margin: 1.15rem 0 0;
            color: #B9CADD;
            font-size: 1.01rem;
            line-height: 1.9;
        }

        .hero-tags {
            display: flex;
            flex-wrap: wrap;
            gap: .5rem;
            margin-top: 1.35rem;
        }

        .hero-tag {
            padding: .46rem .72rem;
            border: 1px solid rgba(193,219,242,.18);
            border-radius: 10px;
            background: rgba(255,255,255,.055);
            color: #D9E8F5;
            font-size: .76rem;
            font-weight: 700;
        }

        .hero-visual {
            position: relative;
            min-height: 320px;
            overflow: hidden;
            border: 1px solid rgba(161,203,238,.21);
            border-radius: 24px;
            background:
                radial-gradient(circle at 70% 30%, rgba(56,189,248,.15), transparent 34%),
                linear-gradient(160deg,rgba(255,255,255,.095),rgba(255,255,255,.025));
            box-shadow: inset 0 1px 0 rgba(255,255,255,.08);
        }

        .visual-topline {
            position: absolute;
            top: 1rem;
            left: 1.1rem;
            right: 1.1rem;
            z-index: 2;
            display: flex;
            justify-content: space-between;
            color: #B7CEE2;
            font-size: .68rem;
            font-weight: 760;
            letter-spacing: .12em;
        }

        .visual-topline span:last-child { color: #72D7FF; }

        .city-network {
            position: absolute;
            inset: 2.3rem .8rem 4.8rem;
            width: calc(100% - 1.6rem);
            height: calc(100% - 7.1rem);
            filter: drop-shadow(0 18px 30px rgba(0,0,0,.18));
        }

        .network-line {
            fill: none;
            stroke: rgba(139,211,248,.24);
            stroke-width: 1.4;
        }

        .network-line--strong {
            stroke: rgba(101,212,255,.58);
            stroke-width: 2;
        }

        .network-node {
            fill: #A8E5FF;
            stroke: #0B2842;
            stroke-width: 4;
            animation: nodePulse 3.6s ease-in-out infinite;
        }

        .network-node:nth-of-type(2n) { animation-delay: .7s; }
        .network-node:nth-of-type(3n) { animation-delay: 1.4s; }

        @keyframes nodePulse {
            0%,100% { opacity: .58; }
            50% { opacity: 1; }
        }

        .visual-metrics {
            position: absolute;
            left: 1rem;
            right: 1rem;
            bottom: 1rem;
            display: grid;
            grid-template-columns: repeat(3,1fr);
            gap: .55rem;
        }

        .visual-metric {
            padding: .72rem;
            border: 1px solid rgba(184,215,241,.16);
            border-radius: 13px;
            background: rgba(3,16,30,.42);
            backdrop-filter: blur(8px);
        }

        .visual-metric strong {
            display: block;
            color: #F7FBFF;
            font-size: 1.25rem;
            line-height: 1.1;
            letter-spacing: -.04em;
        }

        .visual-metric span {
            display: block;
            margin-top: .25rem;
            color: #96B2CA;
            font-size: .66rem;
            letter-spacing: .06em;
        }

        .journey-grid {
            display: grid;
            grid-template-columns: repeat(4,minmax(0,1fr));
            gap: .72rem;
            margin: .85rem 0 1.2rem;
        }

        .journey-card {
            display: grid;
            grid-template-columns: auto 1fr;
            gap: .72rem;
            align-items: center;
            padding: .88rem .95rem;
            border: 1px solid var(--line);
            border-radius: 15px;
            background: rgba(255,255,255,.9);
            box-shadow: var(--shadow-sm);
        }

        .journey-index {
            display: grid;
            place-items: center;
            width: 34px;
            height: 34px;
            border-radius: 11px;
            background: #E9F1FF;
            color: #1D4ED8;
            font-size: .74rem;
            font-weight: 820;
        }

        .journey-card strong {
            display: block;
            color: var(--ink);
            font-size: .85rem;
        }

        .journey-card small {
            display: block;
            margin-top: .15rem;
            color: var(--muted);
            font-size: .7rem;
        }

        .control-panel,
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--line) !important;
            border-radius: 18px !important;
            background: rgba(255,255,255,.9);
            box-shadow: var(--shadow-sm);
        }

        .stat-card {
            position: relative;
            height: 100%;
            min-height: 150px;
            overflow: hidden;
            border: 1px solid var(--line);
            border-radius: 20px;
            padding: 1.08rem 1.15rem;
            background: linear-gradient(180deg,#FFFFFF,#F9FBFE);
            box-shadow: var(--shadow-sm);
        }

        .stat-card::before {
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 4px;
            background: linear-gradient(180deg,#2563EB,#55D5FF);
        }

        .stat-label {
            color: var(--muted);
            font-size: .8rem;
            font-weight: 720;
            margin-bottom: .5rem;
        }

        .stat-value {
            color: var(--ink);
            font-size: clamp(1.65rem,2.8vw,2.45rem);
            line-height: 1.08;
            font-weight: 820;
            letter-spacing: -.05em;
            word-break: keep-all;
        }

        .stat-meta {
            color: #637389;
            font-size: .78rem;
            margin-top: .58rem;
            line-height: 1.48;
        }

        .insight-strip {
            border: 1px solid #CADCF0;
            border-radius: 17px;
            padding: 1.03rem 1.15rem;
            margin: 1rem 0 1.2rem;
            background:
                radial-gradient(circle at 94% 15%,rgba(37,99,235,.11),transparent 28%),
                linear-gradient(135deg,#F7FBFF,#EEF5FD);
            color: #334B63;
            line-height: 1.78;
            box-shadow: var(--shadow-sm);
        }

        .insight-strip::before {
            content: "要点";
            display: inline-block;
            margin-right: .6rem;
            color: #2563EB;
            font-size: .65rem;
            font-weight: 880;
            letter-spacing: .12em;
        }

        .panel {
            border: 1px solid var(--line);
            border-radius: 20px;
            padding: 1.12rem 1.18rem;
            background: #FFF;
            box-shadow: var(--shadow-sm);
            margin-bottom: 1rem;
        }

        .profile-card {
            min-height: 450px;
            overflow: hidden;
            border: 1px solid rgba(115,169,211,.24);
            border-radius: 22px;
            padding: 1.3rem 1.32rem;
            background:
                radial-gradient(circle at 92% 8%,rgba(56,189,248,.18),transparent 28%),
                linear-gradient(155deg,#071522 0%,#0A2138 62%,#0F3150 100%);
            box-shadow: 0 24px 58px rgba(7,26,46,.18);
        }

        .profile-kicker {
            color: #7DD3FC;
            font-size: .68rem;
            font-weight: 820;
            letter-spacing: .12em;
            text-transform: uppercase;
        }

        .profile-name {
            color: #F8FBFF;
            font-weight: 830;
            font-size: 2.15rem;
            letter-spacing: -.055em;
            margin: .3rem 0 .82rem;
        }

        .profile-summary {
            color: #B8CADB;
            font-size: .9rem;
            line-height: 1.76;
            margin-bottom: 1rem;
        }

        .profile-row {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            gap: 1rem;
            border-top: 1px solid rgba(207,228,245,.13);
            padding: .68rem 0;
        }

        .profile-row span:first-child {
            color: #8FA9BF;
            font-size: .78rem;
        }

        .profile-row span:last-child {
            color: #EEF7FF;
            font-size: .88rem;
            font-weight: 750;
            text-align: right;
        }

        .type-badge {
            display: inline-flex;
            padding: .38rem .68rem;
            border: 1px solid rgba(155,210,247,.22);
            border-radius: 999px;
            background: rgba(255,255,255,.075);
            color: #D9EFFF;
            font-size: .72rem;
            font-weight: 750;
            margin-bottom: .78rem;
        }

        .map-legend {
            display: grid;
            grid-template-columns: repeat(6,minmax(74px,1fr));
            gap: 6px;
            margin: .3rem 0 .9rem;
        }

        .map-legend-swatch {
            height: 9px;
            border-radius: 999px;
            margin-bottom: 5px;
        }

        [data-baseweb="tab-list"] {
            position: sticky;
            top: 3.35rem;
            z-index: 20;
            gap: .25rem;
            padding: .32rem;
            margin: .2rem 0 1rem;
            border: 1px solid var(--line);
            border-radius: 16px;
            background: rgba(255,255,255,.9);
            backdrop-filter: blur(16px);
            box-shadow: var(--shadow-sm);
        }

        [data-baseweb="tab"] {
            height: 2.85rem;
            padding: 0 1rem;
            border-radius: 11px;
            color: #5B6F84;
            font-size: .83rem;
            font-weight: 740;
        }

        [data-baseweb="tab"][aria-selected="true"] {
            background: var(--navy);
            color: #F4F9FF;
        }

        [data-testid="stDeckGlJsonChart"],
        [data-testid="stVegaLiteChart"],
        [data-testid="stDataFrame"] {
            overflow: hidden;
            border: 1px solid var(--line);
            border-radius: 18px;
            background: #FFF;
            box-shadow: var(--shadow-sm);
        }

        .stDownloadButton button,
        .stButton button {
            border: 0;
            border-radius: 12px;
            background: var(--navy);
            color: #FFF;
            font-weight: 760;
            box-shadow: 0 9px 24px rgba(7,31,54,.16);
        }

        @media (prefers-reduced-motion: reduce) {
            html { scroll-behavior: auto; }
            .network-node { animation: none; }
        }

        @media (max-width: 1040px) {
            .hero {
                grid-template-columns: 1fr;
                padding: 2.4rem 2.2rem;
            }
            .hero-visual { min-height: 300px; }
            .journey-grid { grid-template-columns: repeat(2,minmax(0,1fr)); }
            .map-legend { grid-template-columns: repeat(3,1fr); }
            .profile-card { min-height: auto; }
        }

        @media (max-width: 640px) {
            .block-container { padding: .55rem .65rem 3rem; }
            .hero {
                min-height: auto;
                padding: 1.45rem 1.05rem 1.1rem;
                border-radius: 20px;
                gap: 1.2rem;
            }
            .hero h1 { font-size: 2.35rem; }
            .hero p { font-size: .86rem; line-height: 1.72; }
            .hero-visual { min-height: 250px; border-radius: 17px; }
            .journey-grid { grid-template-columns: 1fr 1fr; gap: .48rem; }
            .journey-card { padding: .7rem; gap: .55rem; }
            .stat-card { min-height: auto; border-radius: 15px; }
            .profile-card { min-height: auto; padding: 1rem; border-radius: 17px; }
            .profile-name { font-size: 1.75rem; }
            .map-legend { grid-template-columns: repeat(2,minmax(0,1fr)); }
            [data-baseweb="tab-list"] {
                top: 3rem;
                overflow-x: auto;
                white-space: nowrap;
                gap: 0;
            }
            [data-baseweb="tab"] {
                flex: 0 0 auto;
                min-width: max-content;
                height: 2.65rem;
                padding: 0 .72rem;
                font-size: .79rem;
            }
        }
    
        /* LIGHT_PANEL_CONTRAST_FIX_V1
           白い.panel内だけ、ダークカード用の明るい文字色を上書きする */
        .panel {
            color: #0B1728 !important;
            background: linear-gradient(180deg, #FFFFFF 0%, #FBFCFE 100%) !important;
        }

        .panel h1,
        .panel h2,
        .panel h3,
        .panel h4,
        .panel p,
        .panel strong {
            color: #0B1728 !important;
        }

        .panel .profile-kicker {
            color: #2563EB !important;
        }

        .panel .profile-name {
            color: #0B1728 !important;
            text-shadow: none !important;
        }

        .panel .profile-summary {
            color: #475569 !important;
        }

        .panel .profile-row {
            border-top-color: #E3EAF2 !important;
        }

        .panel .profile-row span:first-child {
            color: #617287 !important;
        }

        .panel .profile-row span:last-child {
            color: #102033 !important;
        }

        .panel .rank-chip {
            display: inline-block;
            margin: 0 0.3rem 0.38rem 0;
            padding: 0.28rem 0.6rem;
            border: 1px solid #D4E2EF;
            border-radius: 999px;
            background: #F3F7FC;
            color: #31506F !important;
            font-size: 0.74rem;
            font-weight: 720;
        }

        .panel .profile-name[style*="font-size"] {
            color: #0B1728 !important;
            font-weight: 850 !important;
        }

    
        /* DISCOVERY_MODE_V1 */
        .discovery-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.75rem;
            margin: 0.8rem 0 1.15rem;
        }

        .discovery-card {
            position: relative;
            min-height: 150px;
            overflow: hidden;
            padding: 1rem 1.05rem;
            border: 1px solid #D9E5F0;
            border-radius: 18px;
            background:
                radial-gradient(circle at 100% 0%, rgba(37, 99, 235, 0.1), transparent 42%),
                linear-gradient(180deg, #FFFFFF 0%, #F8FAFD 100%);
            box-shadow: 0 10px 28px rgba(11, 23, 40, 0.055);
        }

        .discovery-card::before {
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 4px;
            background: linear-gradient(180deg, #2563EB, #55D5FF);
        }

        .discovery-eyebrow {
            color: #2563EB;
            font-size: 0.64rem;
            font-weight: 850;
            letter-spacing: 0.11em;
            text-transform: uppercase;
        }

        .discovery-value {
            margin-top: 0.52rem;
            color: #0B1728;
            font-size: clamp(1.55rem, 2.6vw, 2.2rem);
            font-weight: 830;
            line-height: 1.08;
            letter-spacing: -0.05em;
        }

        .discovery-label {
            margin-top: 0.42rem;
            color: #64748B;
            font-size: 0.78rem;
            line-height: 1.45;
        }

        .story-panel {
            height: 100%;
            min-height: 380px;
            padding: 1.3rem 1.35rem;
            border: 1px solid rgba(113, 171, 217, 0.22);
            border-radius: 22px;
            background:
                radial-gradient(circle at 92% 8%, rgba(56, 189, 248, 0.17), transparent 30%),
                linear-gradient(150deg, #071522 0%, #0B2239 62%, #103553 100%);
            box-shadow: 0 24px 58px rgba(7, 26, 46, 0.16);
        }

        .story-kicker {
            color: #7DD3FC;
            font-size: 0.67rem;
            font-weight: 850;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }

        .story-title {
            margin: 0.38rem 0 0.8rem;
            color: #F8FBFF;
            font-size: 2.15rem;
            font-weight: 840;
            letter-spacing: -0.055em;
        }

        .story-text {
            color: #BED0E0;
            font-size: 0.91rem;
            line-height: 1.82;
        }

        .signal-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.55rem;
            margin-top: 1rem;
        }

        .signal-item {
            padding: 0.72rem 0.76rem;
            border: 1px solid rgba(190, 221, 244, 0.13);
            border-radius: 13px;
            background: rgba(255, 255, 255, 0.045);
        }

        .signal-item strong {
            display: block;
            color: #F5FAFF;
            font-size: 1rem;
            letter-spacing: -0.02em;
        }

        .signal-item span {
            display: block;
            margin-top: 0.2rem;
            color: #8FA9BF;
            font-size: 0.67rem;
        }

        .discovery-explainer {
            padding: 0.92rem 1rem;
            margin: 0.75rem 0 1rem;
            border: 1px solid #D8E4EF;
            border-radius: 15px;
            background: #F8FBFF;
            color: #42566C;
            font-size: 0.84rem;
            line-height: 1.7;
        }

        .discovery-explainer strong {
            color: #153E75;
        }

        .similar-list {
            display: grid;
            gap: 0.62rem;
            margin-top: 0.65rem;
        }

        .similar-item {
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 0.8rem;
            align-items: center;
            padding: 0.85rem 0.9rem;
            border: 1px solid #DCE5EF;
            border-radius: 14px;
            background: #FFFFFF;
            box-shadow: 0 7px 20px rgba(11, 23, 40, 0.035);
        }

        .similar-item strong {
            display: block;
            color: #0B1728;
            font-size: 0.94rem;
        }

        .similar-item span {
            display: block;
            margin-top: 0.18rem;
            color: #6B7B8E;
            font-size: 0.72rem;
        }

        .similar-score {
            min-width: 68px;
            padding: 0.4rem 0.55rem;
            border-radius: 999px;
            background: #EAF2FF;
            color: #174EA6;
            font-size: 0.75rem;
            font-weight: 800;
            text-align: center;
        }

        @media (max-width: 1040px) {
            .discovery-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }

        @media (max-width: 640px) {
            .discovery-grid {
                grid-template-columns: 1fr 1fr;
                gap: 0.5rem;
            }

            .discovery-card {
                min-height: 132px;
                padding: 0.82rem 0.85rem;
                border-radius: 15px;
            }

            .discovery-value {
                font-size: 1.48rem;
            }

            .story-panel {
                min-height: auto;
                padding: 1rem;
                border-radius: 17px;
            }

            .story-title {
                font-size: 1.75rem;
            }

            .signal-grid {
                grid-template-columns: 1fr 1fr;
            }
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


@st.cache_data
def load_history() -> pd.DataFrame:
    if not HISTORY_PATH.exists():
        raise FileNotFoundError(
            f"{HISTORY_PATH} が見つかりません。prepare_history.pyを実行してください"
        )
    history = pd.read_csv(HISTORY_PATH, dtype={"自治体コード": str})
    required_columns = {"自治体コード", "自治体", "年", "人口", "高齢化率"}
    missing_columns = required_columns - set(history.columns)
    if missing_columns:
        raise ValueError(f"経年CSVに必要な列がありません: {sorted(missing_columns)}")
    history["自治体コード"] = history["自治体コード"].str.zfill(5)
    for column in ["年", "人口", "高齢化率"]:
        history[column] = pd.to_numeric(history[column], errors="raise")
    history["年"] = history["年"].astype(int)
    if history["自治体"].nunique() != 23:
        raise ValueError(
            f"経年データの自治体数が23区ではなく{history['自治体'].nunique()}区です"
        )
    if history.duplicated(["自治体コード", "年"]).any():
        raise ValueError("経年データに自治体・年の重複があります")
    if (history["人口"] <= 0).any():
        raise ValueError("経年データの人口に0以下の値があります")
    if not history["高齢化率"].between(0, 100).all():
        raise ValueError("経年データの高齢化率が0〜100の範囲外です")
    return history.sort_values(["年", "自治体コード"]).reset_index(drop=True)


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
        <div class="profile-kicker">選択区</div>
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



@st.cache_data(show_spinner=False)
def calculate_period_changes(
    history: pd.DataFrame, start_year: int, end_year: int
) -> pd.DataFrame:
    start = history.loc[history["年"] == start_year, [
        "自治体コード", "自治体", "人口", "高齢化率"
    ]].rename(
        columns={
            "人口": "開始人口",
            "高齢化率": "開始高齢化率",
        }
    )
    end = history.loc[history["年"] == end_year, [
        "自治体コード", "自治体", "人口", "高齢化率"
    ]].rename(
        columns={
            "自治体": "終了自治体",
            "人口": "終了人口",
            "高齢化率": "終了高齢化率",
        }
    )
    changes = start.merge(end, on="自治体コード", validate="one_to_one")
    if len(changes) != 23:
        raise ValueError(
            f"{start_year}年と{end_year}年を比較できる自治体が{len(changes)}区です"
        )
    changes["人口増減"] = changes["終了人口"] - changes["開始人口"]
    changes["人口増減率"] = changes["人口増減"] / changes["開始人口"] * 100
    changes["高齢化率変化"] = changes["終了高齢化率"] - changes["開始高齢化率"]
    return changes.drop(columns="終了自治体")


@st.cache_data(show_spinner=False)
def period_summary(
    history: pd.DataFrame, start_year: int, end_year: int
) -> dict[str, float]:
    start = history.loc[history["年"] == start_year]
    end = history.loc[history["年"] == end_year]
    start_population = float(start["人口"].sum())
    end_population = float(end["人口"].sum())
    start_aging = float(
        (start["人口"] * start["高齢化率"]).sum() / start_population
    )
    end_aging = float(
        (end["人口"] * end["高齢化率"]).sum() / end_population
    )
    return {
        "開始人口": start_population,
        "終了人口": end_population,
        "人口増減": end_population - start_population,
        "人口増減率": (end_population - start_population) / start_population * 100,
        "開始高齢化率": start_aging,
        "終了高齢化率": end_aging,
        "高齢化率変化": end_aging - start_aging,
    }


def change_color(value: float, maximum_absolute: float) -> list[int]:
    if maximum_absolute == 0 or abs(value) < 1e-12:
        return [226, 232, 240, 220]
    ratio = min(abs(value) / maximum_absolute, 1.0)
    if value < 0:
        start = (219, 234, 254)
        end = (29, 78, 216)
    else:
        start = (255, 237, 213)
        end = (194, 65, 12)
    return [
        int(start[index] + (end[index] - start[index]) * ratio)
        for index in range(3)
    ] + [230]


@st.cache_data(show_spinner=False)
def prepare_change_geojson(
    source_geojson: dict,
    changes: pd.DataFrame,
    change_metric: str,
    selected_ward: str,
) -> dict:
    values = changes.set_index("自治体コード").to_dict("index")
    maximum_absolute = float(changes[change_metric].abs().max())
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
        value = float(row[change_metric])
        is_selected = selected_ward == row["自治体"]
        if change_metric == "人口増減率":
            display_value = f"{value:+.2f}%"
            metric_label = "人口増減率"
        else:
            display_value = f"{value:+.2f}pt"
            metric_label = "高齢化率変化"
        properties.update(
            {
                "自治体": row["自治体"],
                "変化指標": metric_label,
                "変化表示": display_value,
                "開始人口表示": f"{row['開始人口']:,.0f}人",
                "終了人口表示": f"{row['終了人口']:,.0f}人",
                "開始高齢化率表示": f"{row['開始高齢化率']:.2f}%",
                "終了高齢化率表示": f"{row['終了高齢化率']:.2f}%",
                "fill_color": change_color(value, maximum_absolute),
                "line_color": [15, 23, 42, 255] if is_selected else [255, 255, 255, 220],
                "line_width": 4 if is_selected else 1.2,
            }
        )
    return prepared


# LIGHTWEIGHT_HISTORY_MAP_ROBUST_V1
def make_change_map_chart(
    source_geojson: dict,
    changes: pd.DataFrame,
    change_metric: str,
    selected_ward: str,
) -> alt.Chart:
    """経年変化を軽量なVega-Lite地図として描画する。"""
    prepared = prepare_change_geojson(
        source_geojson,
        changes,
        change_metric,
        selected_ward,
    )

    features: list[dict] = []
    selected_features: list[dict] = []

    for source_feature in prepared["features"]:
        feature = copy.deepcopy(source_feature)
        properties = feature.setdefault("properties", {})
        red, green, blue, _ = properties.get(
            "fill_color",
            [210, 210, 210, 220],
        )
        properties["fill_hex"] = f"#{red:02X}{green:02X}{blue:02X}"
        features.append(feature)

        if properties.get("自治体") == selected_ward:
            selected_features.append(copy.deepcopy(feature))

    base = (
        alt.Chart(alt.Data(values=features))
        .mark_geoshape(
            stroke="#FFFFFF",
            strokeWidth=1.0,
            opacity=0.98,
        )
        .encode(
            color=alt.Color(
                "properties.fill_hex:N",
                scale=None,
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("properties.自治体:N", title="区"),
                alt.Tooltip("properties.変化指標:N", title="指標"),
                alt.Tooltip("properties.変化表示:N", title="変化"),
                alt.Tooltip("properties.開始人口表示:N", title="開始人口"),
                alt.Tooltip("properties.終了人口表示:N", title="終了人口"),
                alt.Tooltip(
                    "properties.開始高齢化率表示:N",
                    title="開始高齢化率",
                ),
                alt.Tooltip(
                    "properties.終了高齢化率表示:N",
                    title="終了高齢化率",
                ),
            ],
        )
    )

    layers: list[alt.Chart] = [base]

    if selected_features:
        selected_outline = (
            alt.Chart(alt.Data(values=selected_features))
            .mark_geoshape(
                fillOpacity=0,
                stroke="#0F172A",
                strokeWidth=3.2,
            )
        )
        layers.append(selected_outline)

    return (
        alt.layer(*layers)
        .project(type="mercator")
        .properties(height=500)
        .configure_view(
            stroke="#DCE5EF",
            strokeWidth=1,
            fill="#F8FAFC",
        )
    )


def change_legend_html(changes: pd.DataFrame, change_metric: str) -> str:
    maximum_absolute = float(changes[change_metric].abs().max())
    if change_metric == "人口増減率":
        formatter = lambda value: f"{value:+.1f}%"
    else:
        formatter = lambda value: f"{value:+.1f}pt"
    values = [
        -maximum_absolute,
        -maximum_absolute / 2,
        0.0,
        maximum_absolute / 2,
        maximum_absolute,
    ]
    blocks = []
    for value in values:
        color = change_color(value, maximum_absolute)
        blocks.append(
            '<div class="map-legend-item">'
            f'<div class="map-legend-swatch" style="background:rgba({color[0]},{color[1]},{color[2]},{color[3] / 255:.2f})"></div>'
            f'{escape(formatter(value))}</div>'
        )
    return '<div class="map-legend" style="grid-template-columns:repeat(5,minmax(74px,1fr))">' + "".join(blocks) + "</div>"


def make_history_line_chart(
    history: pd.DataFrame,
    wards: list[str],
    value_column: str,
    title: str,
    axis_title: str,
) -> alt.Chart:
    selected = history.loc[history["自治体"].isin(wards)].copy()
    base = alt.Chart(selected).encode(
        x=alt.X("年:O", title="年", axis=alt.Axis(labelAngle=0)),
        color=alt.Color("自治体:N", title=None),
        tooltip=[
            alt.Tooltip("自治体:N"),
            alt.Tooltip("年:O"),
            alt.Tooltip(f"{value_column}:Q", format=",.2f" if value_column == "高齢化率" else ",.0f"),
        ],
    )
    line = base.mark_line(point=True, strokeWidth=2.5).encode(
        y=alt.Y(f"{value_column}:Q", title=axis_title, scale=alt.Scale(zero=False))
    )
    return line.properties(title=title, height=340)


def make_change_ranking_chart(
    changes: pd.DataFrame, change_metric: str, selected_ward: str
) -> alt.Chart:
    chart_data = changes.copy()
    chart_data["選択"] = chart_data["自治体"].eq(selected_ward)
    chart_data["表示色"] = chart_data[change_metric].map(
        lambda value: "#C2410C" if value >= 0 else "#1D4ED8"
    )
    chart_data.loc[chart_data["選択"], "表示色"] = "#D97706"
    chart_data = chart_data.sort_values(change_metric)
    return (
        alt.Chart(chart_data)
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            x=alt.X(f"{change_metric}:Q", title=change_metric),
            y=alt.Y("自治体:N", title=None, sort=chart_data["自治体"].tolist()),
            color=alt.Color(
                "表示色:N",
                scale=None,
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("自治体:N"),
                alt.Tooltip(f"{change_metric}:Q", format="+.2f"),
            ],
        )
        .properties(height=560)
    )


def history_insight(
    changes: pd.DataFrame, summary: dict[str, float], start_year: int, end_year: int
) -> str:
    population_up = changes.loc[changes["人口増減率"].idxmax()]
    population_down = changes.loc[changes["人口増減率"].idxmin()]
    aging_up = changes.loc[changes["高齢化率変化"].idxmax()]
    return (
        f"<strong>{start_year}→{end_year}年：</strong>"
        f"23区人口は{summary['人口増減率']:+.2f}%、人口加重の高齢化率は"
        f"{summary['高齢化率変化']:+.2f}pt変化しました。"
        f"人口増加率が最大なのは{escape(str(population_up['自治体']))}（{population_up['人口増減率']:+.2f}%）、"
        f"人口増加率が最小なのは{escape(str(population_down['自治体']))}（{population_down['人口増減率']:+.2f}%）、"
        f"高齢化率の上昇幅が最大なのは{escape(str(aging_up['自治体']))}（{aging_up['高齢化率変化']:+.2f}pt）です。"
    )


# DISCOVERY_MODE_V1
@st.cache_data(show_spinner=False)
def build_discovery_dataset(
    data: pd.DataFrame,
    history: pd.DataFrame,
) -> pd.DataFrame:
    start_year = int(history["年"].min())
    end_year = int(history["年"].max())
    changes = calculate_period_changes(history, start_year, end_year)[
        ["自治体コード", "人口増減率", "高齢化率変化"]
    ]
    discovery = data.merge(
        changes,
        on="自治体コード",
        how="left",
        validate="one_to_one",
    )

    analysis_columns = [
        "人口",
        "高齢化率",
        "人口密度",
        "人口増減率",
        "高齢化率変化",
    ]
    scaled_columns: list[str] = []
    for column in analysis_columns:
        median = float(discovery[column].median())
        first_quartile = float(discovery[column].quantile(0.25))
        third_quartile = float(discovery[column].quantile(0.75))
        spread = third_quartile - first_quartile
        if abs(spread) < 1e-12:
            spread = float(discovery[column].std(ddof=0))
        if abs(spread) < 1e-12:
            spread = 1.0
        scaled_name = f"{column}_ロバスト距離"
        discovery[scaled_name] = (discovery[column] - median) / spread
        scaled_columns.append(scaled_name)

    discovery["23区平均との差"] = (
        discovery[scaled_columns].pow(2).mean(axis=1).pow(0.5)
    )
    discovery["総合距離順位"] = discovery["23区平均との差"].rank(
        method="min",
        ascending=False,
    ).astype(int)
    discovery["高密度若年コントラスト"] = (
        discovery["人口密度_ロバスト距離"]
        - discovery["高齢化率_ロバスト距離"]
    )
    return discovery


def discovery_story(
    row: pd.Series,
    discovery: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> str:
    population_growth_median = float(discovery["人口増減率"].median())
    aging_change_median = float(discovery["高齢化率変化"].median())

    growth_relation = (
        "23区中央値を上回る"
        if float(row["人口増減率"]) >= population_growth_median
        else "23区中央値を下回る"
    )
    aging_relation = (
        "23区中央値より上昇幅が大きい"
        if float(row["高齢化率変化"]) >= aging_change_median
        else "23区中央値より上昇幅が小さい"
    )

    notable_parts: list[str] = []
    for metric in ["人口", "高齢化率", "人口密度"]:
        rank = int(row[f"{metric}順位"])
        if rank <= 3:
            notable_parts.append(f"{metric}は23区中{rank}位")
        elif rank >= 21:
            notable_parts.append(f"{metric}は23区中{rank}位")

    if int(row["総合距離順位"]) <= 5:
        notable_parts.append(
            f"5指標を合わせた中央値からの距離は23区中{int(row['総合距離順位'])}位"
        )

    notable_text = (
        "、".join(notable_parts) + "です。"
        if notable_parts
        else "現在値は複数指標で23区の中間層に位置します。"
    )

    return (
        f"{row['自治体']}は「{row['都市タイプ']}型」に分類されます。"
        f"{start_year}年から{end_year}年の人口増減率は"
        f"{float(row['人口増減率']):+.2f}%で、{growth_relation}動きです。"
        f"同期間の高齢化率は{float(row['高齢化率変化']):+.2f}pt変化し、"
        f"{aging_relation}傾向です。{notable_text}"
    )


# DISCOVERY_SIMILARITY_NUMERIC_FIX_V1
def find_similar_wards(
    discovery: pd.DataFrame,
    ward: str,
    limit: int = 3,
) -> pd.DataFrame:
    distance_columns = [
        "人口_ロバスト距離",
        "高齢化率_ロバスト距離",
        "人口密度_ロバスト距離",
        "人口増減率_ロバスト距離",
        "高齢化率変化_ロバスト距離",
    ]

    target_rows = discovery.loc[discovery["自治体"] == ward]
    if target_rows.empty:
        raise ValueError(f"選択した区が見つかりません: {ward}")

    target = target_rows.iloc[0]
    candidates = discovery.loc[discovery["自治体"] != ward].copy()

    # CSV結合後にobject型へ変わった場合でも、距離計算前に数値へ統一する。
    candidate_values = candidates[distance_columns].apply(
        pd.to_numeric,
        errors="coerce",
    )
    target_values = pd.to_numeric(
        target[distance_columns],
        errors="coerce",
    ).astype(float)

    if candidate_values.isna().any().any() or target_values.isna().any():
        raise ValueError("類似度計算に使用する指標に数値化できない値があります")

    distance = (
        candidate_values.astype(float)
        .sub(target_values, axis="columns")
        .pow(2)
        .mean(axis=1)
        .pow(0.5)
    )

    candidates["距離"] = pd.to_numeric(
        distance,
        errors="raise",
    ).astype(float)
    candidates["類似度"] = (
        100.0 / (1.0 + candidates["距離"])
    ).astype(float)

    return (
        candidates
        .sort_values("距離", ascending=True, kind="stable")
        .head(limit)
        .copy()
    )


def discovery_profile_chart(row: pd.Series) -> alt.Chart:
    chart_data = pd.DataFrame(
        {
            "指標": [
                "人口",
                "高齢化率",
                "人口密度",
                "人口増減率",
                "高齢化率変化",
            ],
            "中央値からの距離": [
                float(row["人口_ロバスト距離"]),
                float(row["高齢化率_ロバスト距離"]),
                float(row["人口密度_ロバスト距離"]),
                float(row["人口増減率_ロバスト距離"]),
                float(row["高齢化率変化_ロバスト距離"]),
            ],
        }
    )
    chart_data["方向"] = chart_data["中央値からの距離"].map(
        lambda value: "中央値より高い" if value >= 0 else "中央値より低い"
    )
    bars = (
        alt.Chart(chart_data)
        .mark_bar(cornerRadiusEnd=5, height=26)
        .encode(
            x=alt.X(
                "中央値からの距離:Q",
                title="23区中央値からの距離（四分位範囲で標準化）",
                scale=alt.Scale(domain=[-3.2, 3.2]),
            ),
            y=alt.Y("指標:N", title=None, sort=None),
            color=alt.Color(
                "方向:N",
                scale=alt.Scale(
                    domain=["中央値より低い", "中央値より高い"],
                    range=["#D97706", "#2563EB"],
                ),
                legend=alt.Legend(title=None, orient="bottom"),
            ),
            tooltip=[
                alt.Tooltip("指標:N"),
                alt.Tooltip("中央値からの距離:Q", format="+.2f"),
            ],
        )
        .properties(height=310)
    )
    zero_rule = (
        alt.Chart(pd.DataFrame({"基準": [0.0]}))
        .mark_rule(color="#64748B", strokeDash=[5, 4], strokeWidth=2)
        .encode(x="基準:Q")
    )
    return bars + zero_rule


def discovery_distance_chart(
    discovery: pd.DataFrame,
    selected_ward: str,
) -> alt.Chart:
    chart_data = discovery.nlargest(10, "23区平均との差").copy()
    if selected_ward not in chart_data["自治体"].tolist():
        selected_row = discovery.loc[discovery["自治体"] == selected_ward]
        chart_data = pd.concat([chart_data, selected_row], ignore_index=True)
    chart_data = chart_data.sort_values("23区平均との差")
    chart_data["選択"] = chart_data["自治体"].eq(selected_ward)

    return (
        alt.Chart(chart_data)
        .mark_bar(cornerRadiusEnd=5, height=20)
        .encode(
            x=alt.X(
                "23区平均との差:Q",
                title="23区平均との差",
            ),
            y=alt.Y(
                "自治体:N",
                title=None,
                sort=chart_data["自治体"].tolist(),
            ),
            color=alt.condition(
                alt.datum.選択,
                alt.value("#D97706"),
                alt.value("#2F6FA8"),
            ),
            tooltip=[
                alt.Tooltip("自治体:N"),
                alt.Tooltip("23区平均との差:Q", format=".2f"),
                alt.Tooltip("総合距離順位:Q", title="23区順位"),
            ],
        )
        .properties(height=390)
    )

PLAYFUL_WARD_KEY = "selected_ward_main"


def playful_discovery_html(
    data: pd.DataFrame,
    history: pd.DataFrame,
) -> str:
    """短時間でデータへ入れる、日替わりの探索カードを作る。"""
    ward_names = data["自治体"].tolist()
    day_number = date.today().toordinal()
    daily_ward = ward_names[day_number % len(ward_names)]
    daily_row = data.loc[data["自治体"].eq(daily_ward)].iloc[0]

    daily_history = (
        history.loc[history["自治体"].eq(daily_ward)]
        .sort_values("年")
    )
    first = daily_history.iloc[0]
    last = daily_history.iloc[-1]
    population_change_rate = (
        (float(last["人口"]) - float(first["人口"]))
        / float(first["人口"])
        * 100
    )

    metric_cycle = ["人口", "高齢化率", "人口密度"]
    quiz_metric = metric_cycle[day_number % len(metric_cycle)]
    quiz_row = data.nlargest(1, quiz_metric).iloc[0]

    largest = data.nlargest(1, "人口").iloc[0]
    densest = data.nlargest(1, "人口密度").iloc[0]
    contrast_text = (
        f"人口が最大なのは{largest['自治体']}、"
        f"人口密度が最大なのは{densest['自治体']}。"
        "同じ「大きい」でも、都市の姿は違う。"
    )

    if quiz_metric == "高齢化率":
        quiz_value = f"{float(quiz_row[quiz_metric]):.2f}%"
    elif quiz_metric == "人口":
        quiz_value = f"{float(quiz_row[quiz_metric]):,.0f}人"
    else:
        quiz_value = f"{float(quiz_row[quiz_metric]):,.0f}人/km²"

    return f"""
    <section class="play-zone">
        <div class="play-zone-head">
            <div class="play-zone-title">気になる数字から見る</div>
            <div class="play-zone-note">日替わり / 本編と同じデータ</div>
        </div>
        <div class="play-rail">
            <article class="play-card">
                <div class="play-card-label">今日の1区</div>
                <div class="play-card-title">{escape(str(daily_ward))}</div>
                <div class="play-card-copy">
                    毎日1区。現在値と長期変化を短く。
                </div>
                <div class="play-card-facts">
                    <span class="play-fact">人口 {float(daily_row['人口']):,.0f}人</span>
                    <span class="play-fact">高齢化率 {float(daily_row['高齢化率']):.2f}%</span>
                    <span class="play-fact">{int(first['年'])}→{int(last['年'])} {population_change_rate:+.1f}%</span>
                </div>
            </article>
            <article class="play-card">
                <div class="play-card-label">数字のひっかかり</div>
                <div class="play-card-title">「最大」はひとつではない</div>
                <div class="play-card-copy">{escape(contrast_text)}</div>
            </article>
            <article class="play-card">
                <div class="play-card-label">3秒クイズ</div>
                <div class="play-card-title">{escape(quiz_metric)}が23区で最も高い区は？</div>
                <div class="play-card-copy">答えのあと、地図で周辺との差を見る。</div>
                <details>
                    <summary>答えを見る</summary>
                    <div class="play-answer">
                        {escape(str(quiz_row['自治体']))}（{escape(quiz_value)}）
                    </div>
                </details>
            </article>
        </div>
    </section>
    """


def next_gacha_ward(data: pd.DataFrame) -> str:
    """連打しても同じ区に偏りにくい順番で、次の区を返す。"""
    ward_names = data["自治体"].tolist()
    step = int(st.session_state.get("ward_gacha_step", 0))
    current = st.session_state.get(PLAYFUL_WARD_KEY, "23区全体")

    if current in ward_names:
        current_index = ward_names.index(current)
    else:
        current_index = date.today().toordinal() % len(ward_names)

    next_index = (current_index + 7 + step * 5) % len(ward_names)
    st.session_state["ward_gacha_step"] = step + 1
    return ward_names[next_index]


st.markdown(
    """<style>
/* BUTTON_CONTRAST_FIX_V1 */
.stButton > button,
[data-testid="stButton"] button,
.stDownloadButton > button,
[data-testid="stDownloadButton"] button {
    color-scheme: light !important;
    background: #FFFFFF !important;
    color: #17263A !important;
    -webkit-text-fill-color: #17263A !important;
    border: 1px solid #315F7B !important;
    border-radius: 7px !important;
    box-shadow: 0 3px 10px rgba(31, 47, 65, 0.08) !important;
    font-weight: 750 !important;
}

.stButton > button *,
[data-testid="stButton"] button *,
.stDownloadButton > button *,
[data-testid="stDownloadButton"] button * {
    color: inherit !important;
    -webkit-text-fill-color: inherit !important;
    opacity: 1 !important;
}

.stButton > button:hover,
[data-testid="stButton"] button:hover,
.stDownloadButton > button:hover,
[data-testid="stDownloadButton"] button:hover {
    background: #EAF1F5 !important;
    color: #183E57 !important;
    -webkit-text-fill-color: #183E57 !important;
    border-color: #244E69 !important;
    box-shadow: 0 6px 14px rgba(31, 47, 65, 0.12) !important;
}

.stButton > button[kind="primary"],
[data-testid="stButton"] button[kind="primary"],
.stDownloadButton > button[kind="primary"],
[data-testid="stDownloadButton"] button[kind="primary"] {
    background: #315F7B !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    border-color: #315F7B !important;
}

.stButton > button[kind="primary"]:hover,
[data-testid="stButton"] button[kind="primary"]:hover,
.stDownloadButton > button[kind="primary"]:hover,
[data-testid="stDownloadButton"] button[kind="primary"]:hover {
    background: #244A62 !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    border-color: #244A62 !important;
}

.stButton > button:focus-visible,
[data-testid="stButton"] button:focus-visible,
.stDownloadButton > button:focus-visible,
[data-testid="stDownloadButton"] button:focus-visible {
    outline: 3px solid rgba(49, 95, 123, 0.32) !important;
    outline-offset: 2px !important;
}

.stButton > button:disabled,
[data-testid="stButton"] button:disabled,
.stDownloadButton > button:disabled,
[data-testid="stDownloadButton"] button:disabled {
    background: #E8EDF2 !important;
    color: #6B7687 !important;
    -webkit-text-fill-color: #6B7687 !important;
    border-color: #CBD4DD !important;
    opacity: 1 !important;
    box-shadow: none !important;
}
</style>""",
    unsafe_allow_html=True,
)

try:
    data = add_derived_columns(load_data())
    raw_geojson = load_geojson()
    history = load_history()
except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
    st.error(f"データを読み込めませんでした: {error}")
    st.stop()

hero_start_year = int(history["年"].min())
hero_end_year = int(history["年"].max())
hero_year_count = hero_end_year - hero_start_year + 1

st.markdown(
    f"""
    <section class="hero">
        <div class="hero-copy">
            <div class="hero-eyebrow">公開統計で見る23区</div>
            <h1>東京23区データダッシュボード</h1>
            <p>
                人口・高齢化率・人口密度を、地図と比較で確認できる。
                2015〜2026年の推移と、2025年の人口増減要因を収録。
            </p>
            <div class="hero-tags">
                <div class="hero-tag">地図</div>
                <div class="hero-tag">2区を比較</div>
                <div class="hero-tag">構造分析</div>
                <div class="hero-tag">{hero_start_year}–{hero_end_year}年の推移</div>
            </div>
        </div>
        <div class="hero-visual">
            <div class="visual-topline"><span>概要</span><span>東京都公開統計</span></div>
            <svg class="city-network" viewBox="0 0 520 280" role="img" aria-label="都市ネットワークの抽象図">
                <path class="network-line" d="M26 201 C98 146,145 228,212 163 S345 79,491 113"/>
                <path class="network-line" d="M47 82 C121 117,170 66,232 106 S349 215,477 180"/>
                <path class="network-line network-line--strong" d="M65 240 C146 196,177 130,266 142 S392 84,459 42"/>
                <path class="network-line" d="M98 36 L145 91 L209 61 L266 142 L326 111 L382 158 L459 42"/>
                <circle class="network-node" cx="47" cy="82" r="6"/>
                <circle class="network-node" cx="98" cy="36" r="5"/>
                <circle class="network-node" cx="101" cy="150" r="7"/>
                <circle class="network-node" cx="65" cy="240" r="5"/>
                <circle class="network-node" cx="145" cy="91" r="7"/>
                <circle class="network-node" cx="177" cy="226" r="5"/>
                <circle class="network-node" cx="209" cy="61" r="6"/>
                <circle class="network-node" cx="212" cy="163" r="8"/>
                <circle class="network-node" cx="232" cy="106" r="5"/>
                <circle class="network-node" cx="266" cy="142" r="9"/>
                <circle class="network-node" cx="326" cy="111" r="7"/>
                <circle class="network-node" cx="345" cy="196" r="6"/>
                <circle class="network-node" cx="382" cy="158" r="8"/>
                <circle class="network-node" cx="459" cy="42" r="6"/>
                <circle class="network-node" cx="477" cy="180" r="5"/>
            </svg>
            <div class="visual-metrics">
                <div class="visual-metric"><strong>23</strong><span>区</span></div>
                <div class="visual-metric"><strong>3</strong><span>指標</span></div>
                <div class="visual-metric"><strong>{hero_year_count}</strong><span>収録年数</span></div>
            </div>
        </div>
    </section>
    <div class="journey-grid">
        <div class="journey-card"><span class="journey-index">01</span><div><strong>地図</strong><small>23区の分布を見る</small></div></div>
        <div class="journey-card"><span class="journey-index">02</span><div><strong>2区を比較</strong><small>差と順位を捉える</small></div></div>
        <div class="journey-card"><span class="journey-index">03</span><div><strong>構造を分析</strong><small>関係とタイプを読む</small></div></div>
        <div class="journey-card"><span class="journey-index">04</span><div><strong>経年変化</strong><small>{hero_start_year}–{hero_end_year}年</small></div></div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    playful_discovery_html(data, history),
    unsafe_allow_html=True,
)

if PLAYFUL_WARD_KEY not in st.session_state:
    st.session_state[PLAYFUL_WARD_KEY] = "23区全体"

gacha_button, gacha_note = st.columns([0.18, 0.82], vertical_alignment="center")
with gacha_button:
    if st.button(
        "区ガチャ",
        key="ward_gacha_button",
        use_container_width=True,
        help="ランダムに近い順番で、次に見る区を選びます",
    ):
        st.session_state[PLAYFUL_WARD_KEY] = next_gacha_ward(data)

with gacha_note:
    st.markdown(
        '<div class="gacha-caption">'
        "迷ったときの入口。選んだ区を地図と各分析に反映。"
        "</div>",
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
            key="selected_ward_main",
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

# LAZY_TABS_PERFORMANCE_FIX_V1
map_tab, demo_tab, compare_tab, analysis_tab, discovery_tab, factors_tab, history_tab, project_tab, data_tab = st.tabs(
    ["地図とプロフィール", "3分デモ", "2区比較", "構造分析", "特徴分析", "要因分析", "経年変化", "プロジェクト", "データ"],
    key="main_navigation",
    on_change="rerun",
)

if map_tab.open:
    with map_tab:
        left, right = st.columns([1.65, 0.75], gap="large")
        with left:
            st.subheader(f"{METRICS[selected_metric]['label']}の分布")
            st.markdown(
                '<div class="section-intro">色が濃いほど値が高くなります。区にカーソルを合わせると、複数指標を同時に確認できる。</div>',
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
                        <div class="profile-kicker">23区概要</div>
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

# GUIDED_DEMO_TAB_V1
if demo_tab.open:
    with demo_tab:
        render_demo_tab(
            current_data=data,
            history=history,
            factor_path=str(FACTORS_PATH),
        )

if compare_tab.open:
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

if analysis_tab.open:
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


if discovery_tab.open:
    with discovery_tab:
        discovery = build_discovery_dataset(data, history)
        discovery_start_year = int(history["年"].min())
        discovery_end_year = int(history["年"].max())

        st.subheader("データから、注目すべき区を発見する")
        st.markdown(
            '<div class="section-intro">'
            '現在値と経年変化を組み合わせ、人口増加、高齢化の変化、都市密度、'
            '23区中央値からの離れ方を自動で抽出します。ここでの距離や類似度は'
            '優劣ではなく、特徴を見つけるための探索指標です。'
            '</div>',
            unsafe_allow_html=True,
        )

        fastest_growth = discovery.loc[discovery["人口増減率"].idxmax()]
        largest_aging_shift = discovery.loc[discovery["高齢化率変化"].idxmax()]
        highest_density_discovery = discovery.loc[discovery["人口密度"].idxmax()]
        most_distinctive = discovery.loc[
            discovery["23区平均との差"].idxmax()
        ]

        st.markdown(
            f"""
            <div class="discovery-grid">
                <div class="discovery-card">
                    <div class="discovery-eyebrow">Population mover</div>
                    <div class="discovery-value">{escape(str(fastest_growth['自治体']))}</div>
                    <div class="discovery-label">
                        {discovery_start_year}→{discovery_end_year}年の人口増加率
                        {float(fastest_growth['人口増減率']):+.2f}%
                    </div>
                </div>
                <div class="discovery-card">
                    <div class="discovery-eyebrow">Aging shift</div>
                    <div class="discovery-value">{escape(str(largest_aging_shift['自治体']))}</div>
                    <div class="discovery-label">
                        高齢化率の変化
                        {float(largest_aging_shift['高齢化率変化']):+.2f}pt
                    </div>
                </div>
                <div class="discovery-card">
                    <div class="discovery-eyebrow">Urban density</div>
                    <div class="discovery-value">{escape(str(highest_density_discovery['自治体']))}</div>
                    <div class="discovery-label">
                        人口密度 {float(highest_density_discovery['人口密度']):,.0f}人/km²
                    </div>
                </div>
                <div class="discovery-card">
                    <div class="discovery-eyebrow">Most distinctive</div>
                    <div class="discovery-value">{escape(str(most_distinctive['自治体']))}</div>
                    <div class="discovery-label">
                        5指標を合わせた中央値からの距離が最大
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        discovery_wards = discovery["自治体"].tolist()
        discovery_default = (
            selected_ward
            if selected_ward in discovery_wards
            else str(most_distinctive["自治体"])
        )
        discovery_ward = st.selectbox(
            "深掘りする区",
            discovery_wards,
            index=discovery_wards.index(discovery_default),
            key="discovery_ward",
        )
        selected_discovery = discovery.loc[
            discovery["自治体"] == discovery_ward
        ].iloc[0]

        story_column, profile_column = st.columns(
            [0.92, 1.08],
            gap="large",
        )
        with story_column:
            story = discovery_story(
                selected_discovery,
                discovery,
                discovery_start_year,
                discovery_end_year,
            )
            st.markdown(
                f"""
                <div class="story-panel">
                    <div class="story-kicker">Auto-generated urban brief</div>
                    <div class="story-title">{escape(discovery_ward)}</div>
                    <div class="type-badge">{escape(str(selected_discovery['都市タイプ']))}型</div>
                    <div class="story-text">{escape(story)}</div>
                    <div class="signal-grid">
                        <div class="signal-item">
                            <strong>{int(selected_discovery['人口順位'])}位</strong>
                            <span>人口順位</span>
                        </div>
                        <div class="signal-item">
                            <strong>{int(selected_discovery['高齢化率順位'])}位</strong>
                            <span>高齢化率順位</span>
                        </div>
                        <div class="signal-item">
                            <strong>{float(selected_discovery['人口増減率']):+.2f}%</strong>
                            <span>人口増減率</span>
                        </div>
                        <div class="signal-item">
                            <strong>{int(selected_discovery['総合距離順位'])}位</strong>
                            <span>中央値からの距離</span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with profile_column:
            st.markdown("#### 23区中央値との違い")
            st.markdown(
                '<div class="discovery-explainer">'
                '<strong>0が23区中央値</strong>です。プラスは中央値より高く、'
                'マイナスは低いことを示します。単位差をなくすため、'
                '四分位範囲で標準化しています。'
                '</div>',
                unsafe_allow_html=True,
            )
            st.altair_chart(
                discovery_profile_chart(selected_discovery),
                width="stretch",
            )

        st.divider()
        similar_column, distance_column = st.columns(
            [0.72, 1.28],
            gap="large",
        )
        with similar_column:
            st.subheader("特徴が近い区")
            st.caption(
                "現在値と経年変化の5指標を標準化し、距離が近い3区を表示します。"
            )
            similar = find_similar_wards(
                discovery,
                discovery_ward,
                limit=3,
            )
            # DISCOVERY_NATIVE_CARD_FIX_V1
            for _, similar_row in similar.iterrows():
                with st.container(border=True):
                    similar_name, similar_score = st.columns([1.0, 0.32])
                    with similar_name:
                        st.markdown(f"**{escape(str(similar_row['自治体']))}**")
                        st.caption(
                            f"{escape(str(similar_row['都市タイプ']))}型・"
                            f"人口増減率 {float(similar_row['人口増減率']):+.2f}%"
                        )
                    with similar_score:
                        st.metric(
                            "類似度",
                            f"{float(similar_row['類似度']):.0f}",
                        )
            st.caption(
                "類似度は確率ではなく、距離を0〜100に変換した探索用の目安です。"
            )

        with distance_column:
            st.subheader("中央値から離れた特徴を持つ区")
            st.markdown(
                '<div class="section-intro">'
                '人口・高齢化率・人口密度・人口増減率・高齢化率変化の5指標を'
                '同じ基準にそろえ、23区平均との差を表示します。'
                '</div>',
                unsafe_allow_html=True,
            )
            st.altair_chart(
                discovery_distance_chart(discovery, discovery_ward),
                width="stretch",
            )
            st.caption(
                "値が大きいほど複数指標の組み合わせが23区の中央値から離れています。"
                "良し悪しや政策評価を表すものではありません。"
            )

# POPULATION_FACTORS_TAB_V1
if factors_tab.open:
    with factors_tab:
        render_population_factors_tab(
            current_data=data,
            geojson=raw_geojson,
            factor_path=str(FACTORS_PATH),
        )

if history_tab.open:
    with history_tab:
        st.subheader("2015年以降の経年変化")
        st.markdown(
            '<div class="section-intro">毎年1月1日現在の住民基本台帳データを使い、人口と高齢化率の変化を区別に確認します。現況タブとは統計体系が異なるため、絶対値が一致しない場合があります。</div>',
            unsafe_allow_html=True,
        )
        available_years = sorted(history["年"].unique().tolist())
        start_default = available_years.index(2015) if 2015 in available_years else 0
        end_default = len(available_years) - 1
        control_a, control_b, control_c, control_d = st.columns([0.8, 0.8, 1.1, 1.3])
        with control_a:
            start_year = st.selectbox(
                "開始年", available_years[:-1], index=min(start_default, len(available_years) - 2), key="history_start"
            )
        end_options = [year for year in available_years if year > start_year]
        with control_b:
            end_year = st.selectbox(
                "終了年", end_options, index=len(end_options) - 1, key="history_end"
            )
        with control_c:
            change_metric = st.radio(
                "変化地図の指標", ["人口増減率", "高齢化率変化"], horizontal=True
            )
        trend_default = selected_ward if selected_ward != "23区全体" else "足立区"
        with control_d:
            trend_ward = st.selectbox(
                "変化を詳しく見る区", data["自治体"].tolist(),
                index=data["自治体"].tolist().index(trend_default) if trend_default in data["自治体"].tolist() else 0,
                key="history_ward",
            )

        changes = calculate_period_changes(history, start_year, end_year)
        summary = period_summary(history, start_year, end_year)
        population_growth = changes.loc[changes["人口増減率"].idxmax()]
        aging_growth = changes.loc[changes["高齢化率変化"].idxmax()]

        history_cards = st.columns(4)
        with history_cards[0]:
            stat_card(
                f"23区人口 {start_year}→{end_year}",
                f"{summary['人口増減率']:+.2f}%",
                f"{summary['人口増減']:+,.0f}人",
            )
        with history_cards[1]:
            stat_card(
                "人口加重の高齢化率",
                f"{summary['終了高齢化率']:.2f}%",
                f"{summary['高齢化率変化']:+.2f}pt",
            )
        with history_cards[2]:
            stat_card(
                "人口増加率が最大",
                str(population_growth["自治体"]),
                f"{population_growth['人口増減率']:+.2f}%",
            )
        with history_cards[3]:
            stat_card(
                "高齢化率の上昇幅が最大",
                str(aging_growth["自治体"]),
                f"{aging_growth['高齢化率変化']:+.2f}pt",
            )

        st.markdown(
            f'<div class="insight-strip">{history_insight(changes, summary, start_year, end_year)}</div>',
            unsafe_allow_html=True,
        )

        change_left, change_right = st.columns([1.45, 0.75], gap="large")
        with change_left:
            st.subheader(f"{change_metric}の分布")
            st.markdown(
                '<div class="section-intro">青は減少、オレンジは増加を示します。色は良し悪しではなく、変化の方向と大きさだけを表します。</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                change_legend_html(changes, change_metric), unsafe_allow_html=True
            )
            st.altair_chart(
                make_change_map_chart(
                    raw_geojson,
                    changes,
                    change_metric,
                    trend_ward,
                ),
                width="stretch",
            )
        with change_right:
            selected_change = changes.loc[changes["自治体"] == trend_ward].iloc[0]
            st.markdown(
                f"""
                <div class="profile-card" style="min-height:420px">
                    <div class="profile-kicker">期間サマリー</div>
                    <div class="profile-name">{escape(trend_ward)}</div>
                    <div class="type-badge">{start_year} → {end_year}</div>
                    <div class="profile-summary">人口と高齢化率の変化を同じ期間で確認します。変化の原因は、このデータだけでは特定できません。</div>
                    <div class="profile-row"><span>人口</span><span>{selected_change['開始人口']:,.0f} → {selected_change['終了人口']:,.0f}人</span></div>
                    <div class="profile-row"><span>人口増減</span><span>{selected_change['人口増減']:+,.0f}人</span></div>
                    <div class="profile-row"><span>人口増減率</span><span>{selected_change['人口増減率']:+.2f}%</span></div>
                    <div class="profile-row"><span>高齢化率</span><span>{selected_change['開始高齢化率']:.2f} → {selected_change['終了高齢化率']:.2f}%</span></div>
                    <div class="profile-row"><span>高齢化率変化</span><span>{selected_change['高齢化率変化']:+.2f}pt</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.divider()
        trend_wards = st.multiselect(
            "推移を重ねて見る区（最大4区）",
            data["自治体"].tolist(),
            default=list(dict.fromkeys(
                ward for ward in [trend_ward, "豊島区", "世田谷区"]
                if ward in data["自治体"].tolist()
            ))[:3],
            max_selections=4,
        )
        if not trend_wards:
            trend_wards = [trend_ward]
        population_chart, aging_chart = st.columns(2, gap="large")
        with population_chart:
            st.altair_chart(
                make_history_line_chart(
                    history, trend_wards, "人口", "人口の推移", "人口（人）"
                ),
                width="stretch",
            )
        with aging_chart:
            st.altair_chart(
                make_history_line_chart(
                    history, trend_wards, "高齢化率", "高齢化率の推移", "高齢化率（%）"
                ),
                width="stretch",
            )

        st.divider()
        ranking_left, ranking_right = st.columns([1.35, 0.65], gap="large")
        with ranking_left:
            st.subheader(f"{change_metric}ランキング")
            st.altair_chart(
                make_change_ranking_chart(changes, change_metric, trend_ward),
                width="stretch",
            )
        with ranking_right:
            st.subheader("変化が大きい区")
            top_changes = changes.nlargest(5, change_metric)
            bottom_changes = changes.nsmallest(5, change_metric)
            st.markdown("**増加側 上位5区**")
            for _, row in top_changes.iterrows():
                suffix = "%" if change_metric == "人口増減率" else "pt"
                st.markdown(f"- **{row['自治体']}**　{row[change_metric]:+.2f}{suffix}")
            st.markdown("**減少側 上位5区**")
            for _, row in bottom_changes.iterrows():
                suffix = "%" if change_metric == "人口増減率" else "pt"
                st.markdown(f"- **{row['自治体']}**　{row[change_metric]:+.2f}{suffix}")

        st.markdown(
            '<p class="source-note">経年データ：東京都「住民基本台帳による東京都の世帯と人口」の時系列表。各年1月1日現在。人口移動・住宅供給・出生死亡などの要因分析には追加データが必要です。</p>',
            unsafe_allow_html=True,
        )

# PROJECT_PORTFOLIO_TAB_V1
if project_tab.open:
    with project_tab:
        render_project_tab(
            current_data=data,
            history=history,
            geojson=raw_geojson,
            factor_path=str(FACTORS_PATH),
            live_app_url=LIVE_APP_URL,
        )

if data_tab.open:
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
        current_missing = int(data.isna().sum().sum())
        history_missing = int(history.isna().sum().sum())
        current_duplicates = int(data.duplicated(["自治体コード"]).sum())
        history_duplicates = int(history.duplicated(["自治体コード", "年"]).sum())
        covered_years = sorted(history["年"].unique().tolist())

        st.subheader("データ品質")
        quality_columns = st.columns(4)
        quality_columns[0].metric("現況データ", f"{data['自治体'].nunique()}区", border=True)
        quality_columns[1].metric(
            "経年データ",
            f"{covered_years[0]}〜{covered_years[-1]}年",
            border=True,
        )
        quality_columns[2].metric(
            "欠損値",
            f"{current_missing + history_missing}件",
            border=True,
        )
        quality_columns[3].metric(
            "重複行",
            f"{current_duplicates + history_duplicates}件",
            border=True,
        )

        with st.expander("データ品質チェックの詳細"):
            checks_ok = (
                data["自治体"].nunique() == 23
                and history["自治体"].nunique() == 23
                and current_missing == 0
                and history_missing == 0
                and current_duplicates == 0
                and history_duplicates == 0
            )
            if checks_ok:
                st.success(
                    "23区の件数、欠損、重複、値域を確認済みです。"
                    "GitHub Actionsでも同じ検証を自動実行します。"
                )
            else:
                st.warning("品質チェックに未解決の項目があります。")
            st.markdown(
                f"- 現況データ：{len(data):,}行、{data['自治体'].nunique()}区\n"
                f"- 経年データ：{len(history):,}行、{history['自治体'].nunique()}区、"
                f"{covered_years[0]}〜{covered_years[-1]}年\n"
                f"- 現況の欠損：{current_missing}件、経年の欠損：{history_missing}件\n"
                f"- 現況の重複：{current_duplicates}件、経年の重複：{history_duplicates}件"
            )

        with st.expander("データの出典・設計方針・注意点"):
            st.markdown(
                "- 現況統計：東京都『区市町村統計表（2026年）』\n"
                "- 経年統計：東京都『住民基本台帳による東京都の世帯と人口』時系列表（各年1月1日現在）\n"
                "- 行政境界：国土交通省『国土数値情報（行政区域データ）』をもとにNIIが加工した2023年1月1日時点のGeoJSON\n"
                "- 人口密度：人口 ÷ 面積（km²）で算出\n"
                "- 指数：各指標の23区中央値を100として算出。異なる単位の比較補助にのみ使用\n"
                "- 都市タイプ：高齢化率と人口密度の各中央値で4分類した便宜的ラベル\n"
                "- 独自の総合スコアは作らず、公表値と透明な派生指標だけを表示"
            )
            st.markdown(
                "[東京都 区市町村統計表](https://www.toukei.metro.tokyo.lg.jp/kurasi/2026/ku26-23.htm)  "
                "／ [住民基本台帳 時系列データ](https://www.toukei.metro.tokyo.lg.jp/juukiy/jy-index.htm)  "
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
