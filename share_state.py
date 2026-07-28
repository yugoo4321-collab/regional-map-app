from __future__ import annotations

from urllib.parse import urlencode

import streamlit as st


TAB_TO_SLUG = {
    "地図とプロフィール": "map",
    "3分デモ": "demo",
    "2区比較": "compare",
    "構造分析": "structure",
    "特徴分析": "features",
    "要因分析": "factors",
    "経年変化": "history",
    "プロジェクト": "project",
    "データ": "data",
}

SLUG_TO_TAB = {slug: tab for tab, slug in TAB_TO_SLUG.items()}


def normalize_tab(value: str | None) -> str | None:
    if not value:
        return None

    cleaned = str(value).strip()
    if cleaned in TAB_TO_SLUG:
        return cleaned
    return SLUG_TO_TAB.get(cleaned.lower())


def tab_slug(tab: str | None) -> str | None:
    if not tab:
        return None
    return TAB_TO_SLUG.get(tab, tab)


def build_share_url(
    base_url: str,
    *,
    tab: str | None = None,
    ward: str | None = None,
) -> str:
    params: dict[str, str] = {}

    normalized_tab = normalize_tab(tab)
    if normalized_tab:
        params["tab"] = TAB_TO_SLUG[normalized_tab]

    if ward and ward != "23区全体":
        params["ward"] = ward

    root = base_url.rstrip("/")
    if not params:
        return root

    return f"{root}/?{urlencode(params)}"


def initialize_share_state(
    valid_wards: list[str],
    *,
    tab_key: str,
    ward_key: str,
) -> None:
    raw_tab = st.query_params.get("tab")
    raw_ward = st.query_params.get("ward")
    signature = f"{raw_tab or ''}|{raw_ward or ''}"

    if st.session_state.get("_share_url_signature") == signature:
        return

    requested_tab = normalize_tab(raw_tab)
    if requested_tab:
        st.session_state[tab_key] = requested_tab

    valid_ward_values = {"23区全体", *valid_wards}
    if raw_ward in valid_ward_values:
        st.session_state[ward_key] = raw_ward

    st.session_state["_share_url_signature"] = signature


def sync_share_state_to_url(
    *,
    tab_key: str,
    ward_key: str,
) -> None:
    current_tab = st.session_state.get(tab_key)
    current_ward = st.session_state.get(ward_key)

    expected_tab = tab_slug(current_tab)
    expected_ward = (
        current_ward
        if current_ward and current_ward != "23区全体"
        else None
    )

    current_tab_param = st.query_params.get("tab")
    current_ward_param = st.query_params.get("ward")

    changed = False

    if expected_tab:
        if current_tab_param != expected_tab:
            st.query_params["tab"] = expected_tab
            changed = True
    elif current_tab_param is not None:
        del st.query_params["tab"]
        changed = True

    if expected_ward:
        if current_ward_param != expected_ward:
            st.query_params["ward"] = expected_ward
            changed = True
    elif current_ward_param is not None:
        del st.query_params["ward"]
        changed = True

    if changed:
        st.session_state["_share_url_signature"] = (
            f"{expected_tab or ''}|{expected_ward or ''}"
        )
