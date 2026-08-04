import pandas as pd
import streamlit as st

from forge_core import apply_page_config, apply_theme, forge_header, query_df

apply_page_config("Analytics", "📈")
apply_theme()
forge_header("Training trends, workload, effort, and pain signals.")

history = query_df("SELECT * FROM workout_logs ORDER BY timestamp")
if history.empty:
    st.info("Analytics will appear after workout sets are logged.")
    st.stop()

history["log_date"] = pd.to_datetime(history["log_date"])
history["reps_num"] = pd.to_numeric(
    history["reps_time"].astype(str).str.extract(r"(\d+\.?\d*)")[0],
    errors="coerce",
)
history["volume"] = history["reps_num"].fillna(0) * history["weight"].fillna(0)

sessions = history[["log_date", "program", "week", "day"]].drop_duplicates()
weighted = history[history["weight"] > 0]
avg_rpe = history.loc[history["rpe"] > 0, "rpe"].mean()
avg_pain = history["pain"].mean()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Sessions", len(sessions))
c2.metric("Total volume", f"{history['volume'].sum():,.0f}")
c3.metric("Average RPE", f"{0 if pd.isna(avg_rpe) else avg_rpe:.1f}")
c4.metric("Average pain", f"{avg_pain:.1f}")

st.subheader("Exercise trend")
exercise = st.selectbox("Exercise", sorted(history["exercise"].dropna().unique()))
trend = history[history["exercise"] == exercise].sort_values("timestamp")
if not trend.empty:
    st.line_chart(trend.set_index("log_date")[["weight"]])

st.subheader("Daily volume")
daily_volume = history.groupby("log_date")["volume"].sum().sort_index()
st.bar_chart(daily_volume)

st.subheader("Pain trend")
daily_pain = history.groupby("log_date")["pain"].mean().sort_index()
st.line_chart(daily_pain)
