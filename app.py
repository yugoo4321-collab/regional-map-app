import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="東京23区 人口・高齢化率",
    layout="wide",
)


@st.cache_data
def load_data():
    return pd.read_csv("data/tokyo_wards.csv")


data = load_data()

total_population = data["人口"].sum()

weighted_aging_rate = (
    (data["人口"] * data["高齢化率"]).sum()
    / total_population
)

highest_aging = data.loc[data["高齢化率"].idxmax()]
largest_population = data.loc[data["人口"].idxmax()]


st.title("東京23区 人口・高齢化率ダッシュボード")

st.write(
    "東京都の公開統計をもとに、"
    "23区の人口と65歳以上人口割合を比較します。"
)

st.caption(
    "使用データ：東京都「区市町村統計表（2026年）」"
)


col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "対象自治体",
    "23区",
)

col2.metric(
    "人口合計",
    f"{total_population:,}人",
)

col3.metric(
    "高齢化率",
    f"{weighted_aging_rate:.1f}%",
)

col4.metric(
    "高齢化率が最も高い区",
    highest_aging["自治体"],
    f"{highest_aging['高齢化率']:.2f}%",
)


st.divider()

tab1, tab2 = st.tabs(
    ["高齢化率", "人口"]
)


with tab1:
    st.subheader("区別の高齢化率")

    aging_chart = (
        data[["自治体", "高齢化率"]]
        .sort_values("高齢化率", ascending=False)
        .set_index("自治体")
    )

    st.bar_chart(
        aging_chart,
        height=500,
    )


with tab2:
    st.subheader("区別の人口")

    population_chart = (
        data[["自治体", "人口"]]
        .sort_values("人口", ascending=False)
        .set_index("自治体")
    )

    st.bar_chart(
        population_chart,
        height=500,
    )


st.subheader("23区の一覧")

sort_column = st.selectbox(
    "並び替え",
    ["高齢化率", "人口", "自治体"],
)

ascending = sort_column == "自治体"

display_data = data.sort_values(
    sort_column,
    ascending=ascending,
).copy()

display_data["人口"] = display_data["人口"].map(
    lambda value: f"{value:,}"
)

display_data["高齢化率"] = display_data["高齢化率"].map(
    lambda value: f"{value:.2f}%"
)

st.dataframe(
    display_data,
    hide_index=True,
    width="stretch",
)


with st.expander("データについて"):
    st.write(
        "人口と65歳以上人口割合は、東京都が公開している"
        "区市町村別統計から取得しています。"
    )
    st.write(
        "現段階では、根拠のない独自スコアは使用せず、"
        "公表値をそのまま比較しています。"
    )
