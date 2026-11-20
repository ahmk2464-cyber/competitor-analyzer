import io
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Competitor Analyzer", page_icon="📊")
st.title("📊 Competitor Analyzer")
st.caption("ارفع ملف CSV أو Excel بالأعمدة: Product, Competitor, Your_Value, Competitor_Value")

uploaded = st.file_uploader("Upload file", type=["csv", "xlsx", "xls"])

if uploaded is not None:
    try:
        if uploaded.name.lower().endswith(".csv"):
            df = pd.read_csv(uploaded)
        else:
            df = pd.read_excel(uploaded)

        required = {"Product", "Competitor", "Your_Value", "Competitor_Value"}
        if not required.issubset(df.columns):
            st.error(f"الأعمدة المطلوبة ناقصة: {sorted(required - set(df.columns))}")
        else:
            work = df.copy()
            work["Your_Value"] = pd.to_numeric(work["Your_Value"], errors="coerce")
            work["Competitor_Value"] = pd.to_numeric(work["Competitor_Value"], errors="coerce")
            work = work.dropna(subset=["Your_Value", "Competitor_Value"])

            if work.empty:
                st.warning("لا توجد بيانات رقمية صالحة بعد التنظيف.")
            else:
                work["Diff"] = work["Your_Value"] - work["Competitor_Value"]
                safe_comp = work["Competitor_Value"].replace(0, np.nan)
                work["Pct_Diff"] = ((work["Diff"] / safe_comp) * 100).round(2)
                work["Position"] = np.select(
                    [np.isclose(work["Diff"], 0, atol=1e-6), work["Diff"] < 0, work["Diff"] > 0],
                    ["Equal", "Lower", "Higher"],
                    default="N/A",
                )

                summary = (
                    work.groupby("Competitor", dropna=False)
                    .agg(
                        Products_Count=("Product", "count"),
                        Avg_Mine=("Your_Value", "mean"),
                        Avg_Competitor=("Competitor_Value", "mean"),
                        Avg_Diff=("Diff", "mean"),
                        Avg_Pct_Diff=("Pct_Diff", "mean"),
                        Lower_Count=("Position", lambda s: (s == "Lower").sum()),
                        Equal_Count=("Position", lambda s: (s == "Equal").sum()),
                        Higher_Count=("Position", lambda s: (s == "Higher").sum()),
                    )
                    .round(2)
                    .reset_index()
                )

                st.subheader("Competitor Summary")
                st.dataframe(summary, use_container_width=True)

                st.subheader("Detailed Results")
                st.dataframe(work, use_container_width=True)

                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                    work.to_excel(writer, sheet_name="Detailed_Results", index=False)
                    summary.to_excel(writer, sheet_name="Summary", index=False)
                buf.seek(0)

                st.download_button(
                    "📥 تحميل التقرير (Excel)",
                    data=buf,
                    file_name="competitor_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
    except Exception as e:
        st.error(f"حدث خطأ أثناء معالجة الملف: {e}")
