import streamlit as st
import sqlite3
import pandas as pd
from chatbot import query_bot  # Import the chatbot query function

import os
os.environ["TORCH_USE_RTLD_GLOBAL"] = "YES"


import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Summarized Financial News", layout="wide")
st.title("📈 AI-Powered Financial News Summarizer")

# Load data from database
@st.cache_data
def load_data():
    conn = sqlite3.connect("financial_news.db")
    news_df = pd.read_sql_query(
        "SELECT id, title, publishedAt, source, summary FROM news ORDER BY publishedAt DESC", conn
    )
    kpi_df = pd.read_sql_query(
        "SELECT news_id, summary_length, response_time, model FROM summary_metrics", conn
    )
    conn.close()
    return news_df, kpi_df

news_df, kpi_df = load_data()

# Tabs
tab1, tab2 = st.tabs(["📰 Summarized News", "📊 Summary KPI Dashboard"])

# --- 📰 Tab 1: News Summaries ---
with tab1:
    sources = news_df['source'].dropna().unique()
    selected_sources = st.multiselect("Filter by Source", options=sources, default=list(sources))
    filtered_df = news_df[news_df['source'].isin(selected_sources)]

    for _, row in filtered_df.iterrows():
        with st.expander(f"📰 {row['title']}"):
            st.markdown(f"**Published:** {row['publishedAt']}  \n**Source:** {row['source']}")
            st.write(row['summary'] if pd.notna(row['summary']) else "_No summary available_")

    with st.expander("🔍 View All Summaries as Table"):
        st.dataframe(filtered_df[['publishedAt', 'source', 'title', 'summary']])

# --- 📊 Tab 2: KPI Dashboard ---
with tab2:
    st.subheader("📊 Summary Generation Metrics")
    kpi_df = kpi_df.merge(news_df[['id', 'title']], left_on='news_id', right_on='id', how='left')

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Average Summary Length (words)", round(kpi_df['summary_length'].mean(), 2))

    with col2:
        st.metric("Avg. Response Time (sec)", round(kpi_df['response_time'].mean(), 2))

    # Load emissions if available
    try:
        emissions_df = pd.read_csv("emissions.csv")
        latest_emission = emissions_df['emissions'].iloc[-1]  # Most recent
        st.metric("Estimated CO₂ Emissions", f"{latest_emission:.6f} kg")
    except Exception as e:
        st.warning("⚠️ CO₂ emissions data not found. Run summarization to generate it.")


    st.markdown("### KPI Table")
    st.dataframe(kpi_df[['title', 'summary_length', 'response_time', 'model']])

    st.markdown("### 📈 Distribution Plots")
    st.bar_chart(kpi_df['summary_length'], use_container_width=True)
    st.bar_chart(kpi_df['response_time'], use_container_width=True)

# Tab 3: chatbot
st.markdown("## 🤖 Ask the Financial News Chatbot")

user_question = st.text_input("Ask a question like 'Which stock is good to invest in today?'")

if st.button("Get Answer") and user_question:
    with st.spinner("Thinking..."):
        answer = query_bot(user_question)
        st.success(answer)