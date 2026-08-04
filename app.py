import pandas as pd
import streamlit as st

from forge_core import apply_page_config, apply_theme, forge_header, load_plan, query_df

apply_page_config("Dashboard")
apply_theme()
forge_header("Strength forged. Progress measured.")

plan = load_plan()
history = query_df("SELECT * FROM workout_logs ORDER BY timestamp DESC")

st.subheader("Command Center")

if history.empty:
    st.info("No completed sets yet. Open the Workout page and log your first set.")
    sessions = 0
    sets_logged = 0
    avg_rpe = 0.0
    max_pain = 0
else:
    sessions = len(
        history[["log_date", "program", "week", "day"]].drop_duplicates()
    )
    sets_logged = len(history)
    avg_rpe = history.loc[history["rpe"] > 0, "rpe"].mean()
    avg_rpe = 0.0 if pd.isna(avg_rpe) else float(avg_rpe)
    max_pain = int(history["pain"].max())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Sessions", sessions)
c2.metric("Sets logged", sets_logged)
c3.metric("Average RPE", f"{avg_rpe:.1f}")
c4.metric("Highest pain", max_pain)

st.divider()

programs = plan["program"].drop_duplicates().tolist()
selected_program = st.selectbox("Active program", programs)
program_df = plan[plan["program"] == selected_program]

week = st.selectbox("Current week", sorted(program_df["week"].unique()))
week_df = program_df[program_df["week"] == week]

st.info(week_df["progression"].iloc[0])

days = (
    week_df[["day", "day_title", "optional_day", "time_cap_min"]]
    .drop_duplicates()
    .sort_values("day")
)

st.subheader("Week at a glance")
for row in days.itertuples():
    st.markdown(
        f"""
        <div class="forge-card">
            <b>Day {row.day}: {row.day_title}</b><br>
            <span class="forge-muted">
                {row.time_cap_min} minutes • Optional: {row.optional_day}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.caption("Use the sidebar to open Workout, History, Analytics, or Settings.")
