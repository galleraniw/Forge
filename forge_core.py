from __future__ import annotations

import re
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
PLAN_PATH = ROOT / "data" / "workout_plan.csv"
DB_PATH = ROOT / "database" / "workout_logs.db"


def apply_page_config(title: str, icon: str = "🔥") -> None:
    st.set_page_config(
        page_title=f"{title} | Forge",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.25rem;
            padding-bottom: 3rem;
            max-width: 1150px;
        }
        .forge-card {
            border: 1px solid rgba(128,128,128,.28);
            border-radius: 16px;
            padding: 15px;
            margin: 10px 0;
            background: rgba(255,255,255,.025);
        }
        .forge-muted {
            opacity: .72;
            font-size: .92rem;
        }
        .stButton > button {
            width: 100%;
            min-height: 2.8rem;
            border-radius: 12px;
            font-weight: 650;
        }
        div[data-testid="stMetric"] {
            border: 1px solid rgba(128,128,128,.25);
            border-radius: 14px;
            padding: .75rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def forge_header(subtitle: str) -> None:
    st.title("🔥 Forge")
    st.caption(subtitle)


@st.cache_data
def load_plan() -> pd.DataFrame:
    df = pd.read_csv(PLAN_PATH)
    required = {
        "program", "week", "week_focus", "progression", "day", "day_title",
        "optional_day", "time_cap_min", "exercise_order", "exercise", "block",
        "sets", "reps_time", "rest_seconds", "notes", "safety_substitution",
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Workout plan is missing columns: {sorted(missing)}")

    numeric_cols = ["week", "day", "time_cap_min", "exercise_order", "rest_seconds"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    return df.sort_values(["program", "week", "day", "exercise_order"])


def clean_text(value) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none", "null"} else text


def parse_target_sets(value) -> int:
    match = re.search(r"\d+", clean_text(value))
    return int(match.group()) if match else 1


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS workout_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            program TEXT NOT NULL,
            week INTEGER NOT NULL,
            day INTEGER NOT NULL,
            day_title TEXT NOT NULL,
            exercise TEXT NOT NULL,
            set_num INTEGER NOT NULL,
            reps_time TEXT,
            weight REAL DEFAULT 0,
            rpe REAL DEFAULT 0,
            pain INTEGER DEFAULT 0,
            notes TEXT DEFAULT ''
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_logs_lookup
        ON workout_logs(log_date, program, week, day, exercise)
        """
    )
    conn.commit()
    return conn


def query_df(query: str, params=()) -> pd.DataFrame:
    conn = get_conn()
    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


def execute(query: str, params=()) -> int:
    conn = get_conn()
    try:
        with conn:
            cur = conn.execute(query, params)
        return cur.rowcount
    finally:
        conn.close()


def next_set_number(log_date: str, program: str, week: int, day: int, exercise: str) -> int:
    df = query_df(
        """
        SELECT COALESCE(MAX(set_num), 0) AS max_set
        FROM workout_logs
        WHERE log_date = ? AND program = ? AND week = ? AND day = ? AND exercise = ?
        """,
        (log_date, program, week, day, exercise),
    )
    return int(df.iloc[0]["max_set"]) + 1


def last_exercise_entry(exercise: str):
    df = query_df(
        """
        SELECT reps_time, weight, rpe, pain
        FROM workout_logs
        WHERE exercise = ?
        ORDER BY timestamp DESC, id DESC
        LIMIT 1
        """,
        (exercise,),
    )
    if df.empty:
        return None
    return df.iloc[0].to_dict()


def suggested_weight(last_entry: dict | None) -> float:
    if not last_entry:
        return 0.0
    weight = float(last_entry.get("weight", 0) or 0)
    rpe = float(last_entry.get("rpe", 0) or 0)
    pain = int(last_entry.get("pain", 0) or 0)
    if weight <= 0:
        return 0.0
    if pain >= 3 or rpe >= 9:
        return weight
    return weight + 5.0


def save_set(
    *,
    log_date: str,
    program: str,
    week: int,
    day: int,
    day_title: str,
    exercise: str,
    set_num: int,
    reps_time: str,
    weight: float,
    rpe: float,
    pain: int,
    notes: str,
) -> int:
    conn = get_conn()
    try:
        with conn:
            cur = conn.execute(
                """
                INSERT INTO workout_logs
                (log_date, timestamp, program, week, day, day_title, exercise,
                 set_num, reps_time, weight, rpe, pain, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log_date,
                    datetime.now().isoformat(timespec="seconds"),
                    program,
                    int(week),
                    int(day),
                    day_title,
                    exercise,
                    int(set_num),
                    reps_time.strip(),
                    float(weight),
                    float(rpe),
                    int(pain),
                    notes.strip(),
                ),
            )
            record_id = int(cur.lastrowid)
        return record_id
    finally:
        conn.close()
