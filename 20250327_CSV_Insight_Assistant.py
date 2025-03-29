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

class CSVInsightAssistant:
    def __init__(self):
        st.set_page_config(page_title="CSV Data Insight", page_icon="📊")
        st.title("📊 CSV Insight Generator + AI Summary")
        st.markdown("Upload a `.csv` file to view descriptive stats, visualizations, and AI-generated insights.")
        self.uploaded_file = st.file_uploader("📎 Upload CSV File", type=["csv"])

    def call_deepseek(self, prompt):
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "deepseek-coder:6.7b", "prompt": prompt, "stream": False}
            )
            return response.json().get("response", "(No response from model)")
        except Exception as e:
            return f"❌ LLM call failed: {e}"

    def generate_insights(self):
        if self.uploaded_file:
            try:
                content = self.uploaded_file.read().decode("utf-8")
            except UnicodeDecodeError:
                content = self.uploaded_file.read().decode("utf-8-sig")

            df = pd.read_csv(StringIO(content))

            st.subheader("📑 Basic Info")
            buffer = StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())

            st.subheader("📈 Summary Statistics")
            describe_df = df.describe(include="all")
            st.dataframe(describe_df)

            st.subheader("🧼 Missing Values Table")
            missing = df.isnull().sum()
            st.dataframe(missing[missing > 0])

            st.subheader("🌌 Missing Values Heatmap")
            fig, ax = plt.subplots(figsize=(10, 4))
            sns.heatmap(df.isnull(), cmap="viridis", cbar=False, ax=ax)
            st.pyplot(fig)
            plt.close(fig)

            numeric_cols = df.select_dtypes(include=["int", "float"]).columns.tolist()
            target_col = df.columns[-1] if pd.api.types.is_numeric_dtype(df[df.columns[-1]]) else None

            st.subheader("📦 Boxplots")
            cols_per_row = 2
            total_plots = len(numeric_cols)
            rows = total_plots // cols_per_row + (total_plots % cols_per_row > 0)
            fig, axes = plt.subplots(rows, cols_per_row, figsize=(12, 5 * rows))
            axes = axes.flatten()

            for idx, col in enumerate(numeric_cols):
                if target_col and col != target_col:
                    sns.boxplot(x=df[target_col], y=df[col], ax=axes[idx])
                    axes[idx].set_title(f"{col} by {target_col}")
                else:
                    sns.boxplot(y=df[col], ax=axes[idx])
                    axes[idx].set_title(f"{col} Distribution")

            for j in range(len(numeric_cols), len(axes)):
                fig.delaxes(axes[j])

            plt.tight_layout()
            st.pyplot(fig)

            st.subheader("🔗 Feature Correlation Heatmap")
            numeric_df = df.select_dtypes(include=["int", "float"])
            corr = numeric_df.corr()
            fig, ax = plt.subplots(figsize=(12, 8))
            sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
            st.pyplot(fig)

            st.success("✅ Analysis complete.")

            st.subheader("🤖 AI Insight by DeepSeek")
            sample_csv = df.head(10).to_csv(index=False)
            ai_prompt = f"""
Analyze the provided CSV sample. Suggest 3 meaningful analyses or questions for further exploration:

--- Sample Data ---
{sample_csv}
"""
            ai_summary = self.call_deepseek(ai_prompt)
            st.markdown(ai_summary)

            st.subheader("💬 Chat with DeepSeek AI")
            user_query = st.text_area("Ask AI further questions about this dataset:")
            if st.button("Submit") and user_query:
                response = self.call_deepseek(user_query)
                st.markdown(f"### Your Question:\n{user_query}")
                st.markdown(f"### AI Response:\n{response}")

if __name__ == "__main__":
    app = CSVInsightAssistant()
    app.generate_insights()
