from __future__ import annotations

from pathlib import Path

import streamlit as st


STYLE_PATH = Path(__file__).resolve().parent / "assets" / "app.css"


@st.cache_data(show_spinner=False)
def read_app_styles(path: str) -> str:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"スタイルファイルが見つかりません: {source}")
    return source.read_text(encoding="utf-8")


def load_app_styles() -> None:
    """アプリ共通のCSSを1回だけ読み込む。"""
    css = read_app_styles(str(STYLE_PATH))
    st.markdown(
        f"<style>{css}</style>",
        unsafe_allow_html=True,
    )
