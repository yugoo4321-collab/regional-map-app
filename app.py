import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="地域課題可視化ダッシュボード",
    page_icon=None,
    layout="wide",
)

st.title("地域課題可視化ダッシュボード")
st.write(
    "自治体ごとの人口、高齢化率、空き家率をまとめ、"
    "地域が抱える課題を比較するための試作版です。"
)

st.info(
    "現在の数値は画面と計算処理を確認するための仮データです。"
    "最終版では政府統計などの公開データに差し替えます。"
)

data = pd.read_csv("data/regions.csv")

aging_min = data["高齢化率"].min()
aging_max = data["高齢化率"].max()
vacant_min = data["空き家率"].min()
vacant_max = data["空き家率"].max()

data["高齢化スコア"] = (
    (data["高齢化率"] - aging_min) / (aging_max - aging_min) * 100
)

data["空き家スコア"] = (
    (data["空き家率"] - vacant_min) / (vacant_max - vacant_min) * 100
)

data["地域課題スコア"] = (
    data["高齢化スコア"] * 0.6
    + data["空き家スコア"] * 0.4
).round(1)

prefectures = ["すべて"] + sorted(data["都道府県"].unique().tolist())

selected_prefecture = st.sidebar.selectbox(
    "都道府県",
    prefectures,
)

if selected_prefecture == "すべて":
    filtered_data = data.copy()
else:
    filtered_data = data[data["都道府県"] == selected_prefecture].copy()

st.sidebar.caption(
    "表示する都道府県を選択すると、地図と一覧が切り替わります。"
)

col1, col2, col3 = st.columns(3)

col1.metric(
    "表示自治体数",
    f"{len(filtered_data)}自治体",
)

col2.metric(
    "平均高齢化率",
    f"{filtered_data['高齢化率'].mean():.1f}%",
)

col3.metric(
    "平均空き家率",
    f"{filtered_data['空き家率'].mean():.1f}%",
)

st.subheader("自治体の位置")

map_data = filtered_data.rename(
    columns={
        "緯度": "lat",
        "経度": "lon",
    }
)

st.map(map_data[["lat", "lon"]])

st.subheader("地域課題の比較")

display_data = filtered_data[
    [
        "都道府県",
        "自治体",
        "人口",
        "高齢化率",
        "空き家率",
        "地域課題スコア",
    ]
].sort_values(
    "地域課題スコア",
    ascending=False,
)

st.dataframe(
    display_data,
    width="stretch",
    hide_index=True,
)

with st.expander("地域課題スコアの計算方法"):
    st.write(
        "各指標を0点から100点にそろえたうえで、"
        "高齢化率を60%、空き家率を40%として合計しています。"
    )
    st.write(
        "この配分は試作段階の設定です。"
        "今後、先行研究や行政資料を確認しながら根拠を整えます。"
    )
