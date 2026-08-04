import pandas as pd
import streamlit as st

from forge_core import (
    PLAN_PATH,
    apply_page_config,
    apply_theme,
    forge_header,
    get_conn,
    query_df,
)

apply_page_config("Settings", "⚙️")
apply_theme()
forge_header("Backups, restore tools, and system information.")

st.warning(
    "Local SQLite storage is dependable on your computer. Streamlit Community Cloud "
    "can reset locally written files during restarts or redeployments. Export backups "
    "until permanent cloud storage is connected."
)

history = query_df(
    """
    SELECT id, log_date, timestamp, program, week, day, day_title, exercise,
           set_num, reps_time, weight, rpe, pain, notes
    FROM workout_logs
    ORDER BY timestamp DESC
    """
)

st.download_button(
    "⬇️ Download all workout history",
    data=history.to_csv(index=False).encode("utf-8"),
    file_name="forge_full_history.csv",
    mime="text/csv",
)

st.download_button(
    "⬇️ Download workout plan",
    data=PLAN_PATH.read_bytes(),
    file_name="workout_plan.csv",
    mime="text/csv",
)

st.divider()
st.subheader("Restore V1.0 history backup")
uploaded = st.file_uploader("Upload Forge history CSV", type=["csv"])

if uploaded is not None:
    restore = pd.read_csv(uploaded)
    expected = [
        "log_date", "timestamp", "program", "week", "day", "day_title",
        "exercise", "set_num", "reps_time", "weight", "rpe", "pain", "notes",
    ]
    missing = [col for col in expected if col not in restore.columns]
    if missing:
        st.error(f"Missing columns: {missing}")
    elif st.button("Restore uploaded records"):
        records = (
            restore[expected]
            .where(pd.notna(restore[expected]), None)
            .values
            .tolist()
        )
        conn = get_conn()
        try:
            with conn:
                conn.executemany(
                    """
                    INSERT INTO workout_logs
                    (log_date, timestamp, program, week, day, day_title, exercise,
                     set_num, reps_time, weight, rpe, pain, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    records,
                )
        finally:
            conn.close()
        st.success(f"Restored {len(records)} records.")

st.divider()
st.caption("Forge v1.0 • Modular Streamlit architecture • SQLite logging")
