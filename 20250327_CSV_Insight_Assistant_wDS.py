# ======================================================
# 📦 Project: CSV Insight Assistant
# 👤 Author: YILUO
# 📅 Date: 2025-03-27
# 📝 Description: Streamlit app to auto-analyze and visualize any CSV file — including
# basic stats, missing value heatmaps, correlation maps, and boxplots. It also uses a
# local DeepSeek model via Ollama to generate AI summaries and analysis suggestions
# based on the actual file content and insights.
# ======================================================

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import requests
from io import StringIO

# === DeepSeek LLM Call ===
def call_deepseek(prompt):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "deepseek-coder:6.7b", "prompt": prompt, "stream": False}
        )
        return response.json().get("response", "(No response from model)")
    except Exception as e:
        return f"❌ LLM call failed: {e}"

# === Streamlit App ===
st.set_page_config(page_title="CSV Data Insight", page_icon="📊")
st.title("📊 CSV Insight Generator + AI Summary")
st.markdown("Upload a `.csv` file to view descriptive stats, visualizations, and get LLM-generated insights.")

uploaded_file = st.file_uploader("📎 Upload CSV File", type=["csv"])

if uploaded_file:
    try:
        content = uploaded_file.read().decode("utf-8")
    except UnicodeDecodeError:
        content = uploaded_file.read().decode("utf-8-sig")

    if len(content.strip()) == 0:
        st.warning("⚠️ File is empty.")
    else:
        df = pd.read_csv(StringIO(content))

        st.subheader("📑 Basic Info")
        buffer = StringIO()
        df.info(buf=buffer)
        info_summary = buffer.getvalue()
        st.text(info_summary)

        st.subheader("📈 Summary Statistics")
        describe_df = df.describe(include="all")
        describe_summary = describe_df.to_string()
        st.dataframe(describe_df)

        st.subheader("🧼 Missing Values Table")
        missing = df.isnull().sum()
        missing_summary = missing[missing > 0].to_string()
        st.dataframe(missing[missing > 0])

        st.subheader("🌌 Missing Values Heatmap")
        fig, ax = plt.subplots(figsize=(10, 4))
        sns.heatmap(df.isnull(), cmap="viridis", cbar=False, ax=ax)
        st.pyplot(fig)
        plt.close(fig)

        st.subheader("📊 Distribution Plots")
        numeric_cols = df.select_dtypes(include=["int", "float"]).columns.tolist()

        for col in numeric_cols:
            st.markdown(f"#### 🔹 {col} Distribution")
            fig, ax = plt.subplots()
            sns.boxplot(data=df, y=col, ax=ax)
            st.pyplot(fig)
            plt.close(fig)

        st.subheader("🔗 Feature Correlation Heatmap (Including Target)")
        all_corr_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if df.columns[-1] not in all_corr_cols:
            try:
                df[df.columns[-1]] = pd.to_numeric(df[df.columns[-1]], errors='coerce')
                all_corr_cols.append(df.columns[-1])
            except:
                pass

        corr = df[all_corr_cols].corr()
        corr_top = corr.abs().unstack().sort_values(ascending=False)
        corr_summary = corr_top[corr_top < 1.0].drop_duplicates().head(5).to_string()

        fig, ax = plt.subplots(figsize=(12, 8))
        sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
        st.pyplot(fig)
        plt.close(fig)

        for target_col in ['Survived', 'target', 'label', 'outcome', df.columns[-1]]:
            if target_col in df.columns and pd.api.types.is_numeric_dtype(df[target_col]):
                st.subheader(f"📦 Boxplots by '{target_col}'")
                for col in numeric_cols:
                    if col != target_col:
                        st.markdown(f"##### {col} by {target_col}")
                        fig, ax = plt.subplots()
                        sns.boxplot(x=target_col, y=col, data=df, ax=ax)
                        st.pyplot(fig)
                        plt.close(fig)
                break

        st.success("✅ Analysis complete.")

        # === AI Summary with CSV Sample ===
        st.subheader("🤖 AI Insight by DeepSeek")
        sample_csv = df.head(10).to_csv(index=False)
        summary_prompt = f"""
You are a data analyst. The user uploaded the following CSV file. Based on the sample data and initial insights, please:
1. Describe what the dataset might be about.
2. Suggest 3 possible analysis or modeling tasks that could be performed.

--- Sample Data ---
{sample_csv}

--- Summary Statistics ---
{describe_summary}

--- Top Correlations ---
{corr_summary}

--- Missing Value Overview ---
{missing_summary if missing_summary else 'No missing values found'}

Respond in Markdown.
"""
        ai_summary = call_deepseek(summary_prompt)
        st.markdown(ai_summary)
