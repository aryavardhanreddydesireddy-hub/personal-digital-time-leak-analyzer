import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st
from sklearn.ensemble import IsolationForest

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "data" / "time_leak.db"

st.set_page_config(page_title="Digital Time Leak Analyzer", page_icon="⏱️", layout="wide")


def connect_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def initialize_db():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS activity_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_date TEXT NOT NULL,
                activity_name TEXT NOT NULL,
                category TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                productive INTEGER NOT NULL,
                notes TEXT
            )
        """)
        conn.commit()


def load_data():
    with connect_db() as conn:
        return pd.read_sql_query(
            "SELECT id, session_date, activity_name, category, duration_minutes, productive, notes "
            "FROM activity_sessions ORDER BY session_date DESC, id DESC",
            conn,
        )


def add_session(session_date, activity_name, category, duration, productive, notes):
    with connect_db() as conn:
        conn.execute(
            """INSERT INTO activity_sessions
            (session_date, activity_name, category, duration_minutes, productive, notes)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (str(session_date), activity_name.strip(), category, int(duration), int(productive), notes.strip()),
        )
        conn.commit()


def seed_demo_data():
    demo_rows = [
        ("2026-10-01", "Python practice", "Study", 60, 1, "Solved beginner problems"),
        ("2026-10-01", "Short-video apps", "Social media", 45, 0, "Unplanned scrolling"),
        ("2026-10-02", "SQL revision", "Study", 50, 1, "Practised SELECT queries"),
        ("2026-10-02", "Gaming", "Entertainment", 70, 0, "Evening break"),
        ("2026-10-03", "Project work", "Project", 90, 1, "Worked on a Python project"),
        ("2026-10-03", "Social media", "Social media", 80, 0, "Longer than planned"),
        ("2026-10-04", "Interview preparation", "Study", 75, 1, "Reviewed Python and SQL"),
        ("2026-10-04", "Video streaming", "Entertainment", 55, 0, "Watched videos"),
        ("2026-10-05", "Machine learning notes", "Study", 65, 1, "Reviewed model evaluation"),
        ("2026-10-05", "Short-video apps", "Social media", 110, 0, "Possible time leak"),
        ("2026-10-06", "College assignment", "Study", 45, 1, "Completed assignment"),
        ("2026-10-06", "Browsing", "Other", 25, 0, "Unplanned browsing"),
    ]
    with connect_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM activity_sessions").fetchone()[0]
        if count == 0:
            conn.executemany(
                """INSERT INTO activity_sessions
                (session_date, activity_name, category, duration_minutes, productive, notes)
                VALUES (?, ?, ?, ?, ?, ?)""",
                demo_rows,
            )
            conn.commit()


def make_insights(df):
    if df.empty:
        return "Add a few sessions to receive insights."
    total = int(df["duration_minutes"].sum())
    productive = int(df.loc[df["productive"] == 1, "duration_minutes"].sum())
    nonproductive = total - productive
    social = int(df.loc[df["category"] == "Social media", "duration_minutes"].sum())
    top_category = df.groupby("category")["duration_minutes"].sum().sort_values(ascending=False)
    top_name = str(top_category.index[0]) if not top_category.empty else "None"

    lines = [
        f"You logged {total} minutes ({total / 60:.1f} hours) across {len(df)} sessions.",
        f"Productive sessions account for {productive} minutes; sessions marked non-productive account for {nonproductive} minutes.",
        f"Social media accounts for {social} minutes.",
        f"Your largest time category is {top_name}.",
    ]
    if total and nonproductive / total >= 0.4:
        lines.append("Suggestion: choose one non-productive activity and set a small time limit for the next day.")
    else:
        lines.append("Suggestion: keep recording sessions for several days so you can compare patterns.")
    return "\n\n".join(lines)


initialize_db()

st.title("⏱️ Personal Digital Time Leak Analyzer")
st.caption("A privacy-friendly prototype: log sessions manually, store them in SQLite, and explore your time patterns.")

with st.sidebar:
    st.header("Demo data")
    if st.button("Load sample data"):
        seed_demo_data()
        st.success("Sample data loaded if the database was empty.")
    st.caption("Sample entries are fictional. Use your own entries for a meaningful analysis.")

st.subheader("1. Record an activity")
with st.form("activity_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        session_date = st.date_input("Date", value=date.today())
        activity_name = st.text_input("Activity name", placeholder="e.g., Python practice")
        category = st.selectbox("Category", ["Study", "Project", "Work", "Social media", "Entertainment", "Exercise", "Other"])
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=1440, value=30, step=5)
        productive = st.selectbox("How would you classify this session?", ["Productive", "Non-productive"])
        notes = st.text_input("Notes (optional)", placeholder="What did you do?")
    submitted = st.form_submit_button("Save session")
    if submitted:
        if not activity_name.strip():
            st.error("Please enter an activity name.")
        else:
            add_session(session_date, activity_name, category, duration, productive == "Productive", notes)
            st.success("Session saved to the local SQLite database.")
            st.rerun()

df = load_data()
st.subheader("2. Your activity overview")
if df.empty:
    st.info("No sessions yet. Add a session or select 'Load sample data' in the sidebar.")
else:
    total_minutes = int(df["duration_minutes"].sum())
    productive_minutes = int(df.loc[df["productive"] == 1, "duration_minutes"].sum())
    c1, c2, c3 = st.columns(3)
    c1.metric("Logged time", f"{total_minutes // 60}h {total_minutes % 60}m")
    c2.metric("Productive time", f"{productive_minutes} min")
    c3.metric("Sessions", len(df))

    chart_df = df.groupby("category", as_index=False)["duration_minutes"].sum()
    st.bar_chart(chart_df.set_index("category"))

    st.subheader("3. Pattern detection (machine learning)")
    if len(df) >= 8 and df["duration_minutes"].nunique() >= 2:
        model_data = df[["duration_minutes"]].copy()
        model = IsolationForest(contamination=0.15, random_state=42)
        df["pattern_result"] = model.fit_predict(model_data)
        unusual = df[df["pattern_result"] == -1]
        st.write("Isolation Forest flags unusually long or short sessions compared with the sessions you logged. A flag is not proof that an activity is bad.")
        if unusual.empty:
            st.success("No unusual-duration sessions were flagged in this run.")
        else:
            st.dataframe(unusual[["session_date", "activity_name", "category", "duration_minutes"]], use_container_width=True)
    else:
        st.info("Log at least 8 sessions with different durations to try the anomaly-detection model.")

    st.subheader("4. Automatically generated summary")
    st.write(make_insights(df))
    st.subheader("5. Session history")
    display_df = df.drop(columns=["pattern_result"], errors="ignore").copy()
    display_df["productive"] = display_df["productive"].map({1: "Yes", 0: "No"})
    st.dataframe(display_df, use_container_width=True)

    csv = df.drop(columns=["pattern_result"], errors="ignore").to_csv(index=False).encode("utf-8")
    st.download_button("Download session history as CSV", csv, "activity_sessions.csv", "text/csv")

st.divider()
st.caption("Next improvement: connect a local LLM for natural-language recommendations. This starter version uses rule-based summaries, not an LLM.")
