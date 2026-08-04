import pandas as pd
import streamlit as st

from forge_core import apply_page_config, apply_theme, execute, forge_header, query_df

apply_page_config("History", "📚")
apply_theme()
forge_header("Review, filter, export, and correct saved training records.")

history = query_df(
    """
    SELECT id, log_date, program, week, day, day_title, exercise,
           set_num, reps_time, weight, rpe, pain, notes, timestamp
    FROM workout_logs
    ORDER BY timestamp DESC, id DESC
    """
)

if history.empty:
    st.info("No workout history yet.")
    st.stop()

history["log_date"] = pd.to_datetime(history["log_date"])

c1, c2 = st.columns(2)
start = c1.date_input("From", history["log_date"].min().date())
end = c2.date_input("Through", history["log_date"].max().date())

filtered = history[
    (history["log_date"].dt.date >= start)
    & (history["log_date"].dt.date <= end)
].copy()

st.dataframe(filtered, use_container_width=True, hide_index=True)

csv_bytes = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download filtered history",
    data=csv_bytes,
    file_name="forge_workout_history.csv",
    mime="text/csv",
)

st.divider()
delete_id = st.number_input("Delete record ID", min_value=0, value=0, step=1)
if st.button("Delete record"):
    if delete_id <= 0:
        st.warning("Enter a valid record ID.")
    else:
        deleted = execute("DELETE FROM workout_logs WHERE id = ?", (int(delete_id),))
        if deleted:
            st.success(f"Deleted record #{int(delete_id)}.")
            st.rerun()
        else:
            st.warning("Record ID not found.")
