from datetime import date, datetime, timedelta

import streamlit as st

from forge_core import (
    apply_page_config,
    apply_theme,
    clean_text,
    forge_header,
    last_exercise_entry,
    load_plan,
    next_set_number,
    parse_target_sets,
    query_df,
    save_set,
    suggested_weight,
)

apply_page_config("Workout", "🏋️")
apply_theme()
forge_header("Workout execution and reliable set logging.")

plan = load_plan()

program = st.selectbox("Program", plan["program"].drop_duplicates().tolist())
program_df = plan[plan["program"] == program]

c1, c2 = st.columns(2)
with c1:
    week = st.selectbox("Week", sorted(program_df["week"].unique()))
week_df = program_df[program_df["week"] == week]

day_options = (
    week_df[["day", "day_title"]]
    .drop_duplicates()
    .sort_values("day")
)
day_map = {
    int(row.day): f"Day {int(row.day)} — {row.day_title.split('–', 1)[-1].strip()}"
    for row in day_options.itertuples()
}
with c2:
    day = st.selectbox(
        "Training day",
        list(day_map.keys()),
        format_func=lambda x: day_map[x],
    )

workout = week_df[week_df["day"] == day].copy()
first = workout.iloc[0]

m1, m2, m3 = st.columns(3)
m1.metric("Focus", first["week_focus"])
m2.metric("Work cap", f"{int(first['time_cap_min'])} min")
m3.metric("Optional", first["optional_day"])
st.info(first["progression"])

log_date = st.date_input("Workout date", value=date.today())
session_note = st.text_input("Session note", placeholder="Energy, sleep, equipment changes, etc.")

completed = query_df(
    """
    SELECT exercise, COUNT(*) AS sets_logged
    FROM workout_logs
    WHERE log_date = ? AND program = ? AND week = ? AND day = ?
    GROUP BY exercise
    """,
    (str(log_date), program, int(week), int(day)),
)
completed_map = (
    dict(zip(completed["exercise"], completed["sets_logged"]))
    if not completed.empty
    else {}
)

target_sets = sum(parse_target_sets(v) for v in workout["sets"])
logged_sets = int(completed["sets_logged"].sum()) if not completed.empty else 0
pct = min(100, round(logged_sets / max(1, target_sets) * 100))
st.progress(pct / 100)
st.caption(f"Completion: {logged_sets} of {target_sets} target sets ({pct}%)")

st.subheader(first["day_title"])

for row in workout.itertuples():
    logged = int(completed_map.get(row.exercise, 0))
    st.markdown(
        f"""
        <div class="forge-card">
            <b>{row.exercise_order}. {row.exercise}</b><br>
            <span class="forge-muted">
                {row.block} • {row.sets} sets × {row.reps_time}
                • Rest {row.rest_seconds} sec • Logged today: {logged}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    setup = clean_text(row.notes)
    safety = clean_text(row.safety_substitution)
    if setup:
        st.caption(f"Setup: {setup}")
    if safety:
        st.caption(f"Safety/substitution: {safety}")

    last = last_exercise_entry(row.exercise)
    next_weight = suggested_weight(last)

    if last:
        p1, p2 = st.columns(2)
        p1.caption(
            f"Previous: {last['reps_time'] or '—'} @ {float(last['weight']):g} lb "
            f"• RPE {float(last['rpe']):g}"
        )
        p2.caption(f"Suggested start: {next_weight:g} lb")
    else:
        st.caption("No prior entry yet — establish a clean baseline.")

    next_set = next_set_number(str(log_date), program, int(week), int(day), row.exercise)

    with st.expander(f"Log set {next_set}", expanded=(row.exercise_order == 1)):
        x1, x2 = st.columns(2)
        reps = x1.text_input(
            "Reps or time",
            value=str(last["reps_time"]) if last else "",
            key=f"reps_{week}_{day}_{row.exercise_order}",
        )
        weight = x2.number_input(
            "Weight",
            min_value=0.0,
            value=float(next_weight),
            step=5.0,
            key=f"weight_{week}_{day}_{row.exercise_order}",
        )

        x3, x4 = st.columns(2)
        rpe = x3.number_input(
            "RPE",
            min_value=0.0,
            max_value=10.0,
            value=float(last["rpe"]) if last else 7.0,
            step=0.5,
            key=f"rpe_{week}_{day}_{row.exercise_order}",
        )
        pain = x4.number_input(
            "Pain 0–10",
            min_value=0,
            max_value=10,
            value=int(last["pain"]) if last else 0,
            step=1,
            key=f"pain_{week}_{day}_{row.exercise_order}",
        )
        note = st.text_input(
            "Set note",
            key=f"note_{week}_{day}_{row.exercise_order}",
        )

        if st.button(
            f"✅ Save {row.exercise} — Set {next_set}",
            key=f"save_{week}_{day}_{row.exercise_order}",
        ):
            if not reps.strip() and weight == 0 and not note.strip():
                st.warning("Enter reps/time, weight, or a note before saving.")
            else:
                record_id = save_set(
                    log_date=str(log_date),
                    program=program,
                    week=int(week),
                    day=int(day),
                    day_title=row.day_title,
                    exercise=row.exercise,
                    set_num=next_set,
                    reps_time=reps,
                    weight=weight,
                    rpe=rpe,
                    pain=pain,
                    notes=" | ".join(
                        part for part in [session_note.strip(), note.strip()] if part
                    ),
                )
                st.success(f"Saved successfully — record #{record_id}.")
                st.rerun()

st.divider()
st.subheader("⏱️ Rest Timer")

if "forge_timer_end" not in st.session_state:
    st.session_state.forge_timer_end = None
if "forge_timer_duration" not in st.session_state:
    st.session_state.forge_timer_duration = 120

buttons = st.columns(4)
for column, seconds in zip(buttons, [45, 60, 75, 120]):
    if column.button(f"{seconds}s", key=f"timer_{seconds}"):
        st.session_state.forge_timer_duration = seconds
        st.session_state.forge_timer_end = datetime.now() + timedelta(seconds=seconds)

if st.session_state.forge_timer_end:
    remaining = max(
        0,
        int((st.session_state.forge_timer_end - datetime.now()).total_seconds())
    )
    mins, secs = divmod(remaining, 60)
    st.metric("Time remaining", f"{mins:02d}:{secs:02d}")
    st.progress(remaining / max(1, st.session_state.forge_timer_duration))
    if remaining == 0:
        st.success("Rest complete.")
        st.session_state.forge_timer_end = None
    else:
        st.caption("Tap Refresh Timer to update the countdown.")
        if st.button("Refresh Timer"):
            st.rerun()
        if st.button("Stop Timer"):
            st.session_state.forge_timer_end = None
            st.rerun()

saved_today = query_df(
    """
    SELECT id, exercise, set_num, reps_time, weight, rpe, pain, notes
    FROM workout_logs
    WHERE log_date = ? AND program = ? AND week = ? AND day = ?
    ORDER BY id DESC
    """,
    (str(log_date), program, int(week), int(day)),
)
if not saved_today.empty:
    st.subheader("Saved today")
    st.dataframe(saved_today, use_container_width=True, hide_index=True)
