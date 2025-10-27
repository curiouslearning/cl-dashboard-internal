import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from google.cloud import bigquery

st.title("FTM Gameplay Timeline (Success / Failure by Event)")

# ───────────────────────────────────────────────
# Load Data
# ───────────────────────────────────────────────
@st.cache_data(ttl=1800)
def load_data():
    client = bigquery.Client()
    q = """
        SELECT
          cr_user_id, cohort_group, event_ts, event_name,
          level_number, puzzle_number,
          success_or_failure, number_of_successful_puzzles,
          app_language, country
        FROM `dataexploration-193817.user_data.ftm_event_timeline_cohort`
        ORDER BY cr_user_id, event_ts
    """
    return client.query(q).to_dataframe()

df = load_data()

if not pd.api.types.is_datetime64_any_dtype(df["event_ts"]):
    df["event_ts"] = pd.to_datetime(df["event_ts"], errors="coerce")

# ───────────────────────────────────────────────
# Filters
# ───────────────────────────────────────────────
all_users = sorted(df["cr_user_id"].unique())
users = st.multiselect("Users", all_users, default=all_users)

events = st.multiselect(
    "Event types",
    sorted(df["event_name"].dropna().unique().tolist()),
    default=["puzzle_completed", "level_completed"]
)

subset = df[df["cr_user_id"].isin(users) & df["event_name"].isin(events)].copy()
subset = subset.sort_values(["cr_user_id", "event_ts"])
if subset.empty:
    st.error("Subset is empty after filters.")
    st.stop()

# ───────────────────────────────────────────────
# Outcome inference
# ───────────────────────────────────────────────
def derive_outcome(row):
    if row["success_or_failure"] == "success":
        return "success"
    if row["success_or_failure"] == "failure":
        return "failure"
    if row["event_name"] == "puzzle_completed" and pd.isna(row["success_or_failure"]):
        return "success"
    if row["event_name"] == "level_completed" and (
        pd.notna(row["number_of_successful_puzzles"]) and row["number_of_successful_puzzles"] < 3
    ):
        return "failure"
    return "unknown"

subset["outcome"] = subset.apply(derive_outcome, axis=1)
subset["event_type"] = np.where(
    subset["event_name"].str.contains("puzzle"), "Puzzle", "Level"
)
subset["marker_key"] = subset["outcome"].str.capitalize() + " – " + subset["event_type"]

# ───────────────────────────────────────────────
# Numeric y-axis for compact layout
# ───────────────────────────────────────────────
user_order = {uid: i + 1 for i, uid in enumerate(sorted(subset["cr_user_id"].unique()))}
subset["user_number"] = subset["cr_user_id"].map(user_order)

# ───────────────────────────────────────────────
# Jitter for overlapping timestamps
# ───────────────────────────────────────────────
np.random.seed(42)
subset["user_event_count"] = subset.groupby("cr_user_id")["event_ts"].transform("count")
max_jitter, min_jitter = 10, 2
scale_factor = np.clip(min_jitter + (subset["user_event_count"] / 25), min_jitter, max_jitter)
subset["event_ts_plot"] = subset["event_ts"] + pd.to_timedelta(
    np.random.uniform(-1, 1, len(subset)) * scale_factor, unit="s"
)

# ───────────────────────────────────────────────
# Colors and symbols
# ───────────────────────────────────────────────
color_map = {
    "Success – Puzzle": "green",
    "Failure – Puzzle": "red",
    "Success – Level": "limegreen",
    "Failure – Level": "darkred",
    "Unknown – Puzzle": "gray",
    "Unknown – Level": "lightgray",
}
symbol_map = {"Puzzle": "circle", "Level": "diamond"}

# ───────────────────────────────────────────────
# Hover text (includes cr_user_id again)
# ───────────────────────────────────────────────
def make_hover(r):
    parts = [f"<b>{r['outcome'].capitalize()}</b>"]
    parts.append(f"User ID: {r['cr_user_id']}")
    if pd.notna(r.get("level_number")):
        parts.append(f"Level {int(r['level_number'])}")
    if r["event_name"].startswith("puzzle") and pd.notna(r.get("puzzle_number")):
        parts.append(f"Puzzle {int(r['puzzle_number'])}")
    if r["event_name"].startswith("level") and pd.notna(r.get("number_of_successful_puzzles")):
        parts.append(f"Puzzles succeeded: {int(r['number_of_successful_puzzles'])}")
    if pd.notna(r.get("app_language")):
        parts.append(f"Lang: {r['app_language']}")
    return "<br>".join(parts)

subset["hover_text"] = subset.apply(make_hover, axis=1).fillna("")

# ───────────────────────────────────────────────
# Plot
# ───────────────────────────────────────────────
fig = px.scatter(
    subset,
    x="event_ts_plot",
    y="user_number",
    color="marker_key",
    color_discrete_map=color_map,
    symbol="event_type",
    symbol_map=symbol_map,
    hover_data={"hover_text": True},
    title="FTM Gameplay Timeline (Success / Failure by Event)",
    labels={"event_ts_plot": "Timestamp", "user_number": "User #"},
)

fig.update_traces(
    hovertemplate="%{customdata[0]}<extra></extra>",
    marker=dict(size=10, line=dict(width=0.5, color="black")),
)

# Clean up legend
fig.for_each_trace(lambda t: t.update(name=t.name.split(",")[0]))

# Axis and layout
tickvals = list(user_order.values())
ticktext = [str(i) for i in tickvals]
chart_height = max(400, 40 * len(user_order))

fig.update_layout(
    height=chart_height,
    yaxis=dict(tickmode="array", tickvals=tickvals, ticktext=ticktext, title="User #"),
    legend_title_text="Outcome / Event Type",
    margin=dict(l=60, r=20, t=60, b=60),
    plot_bgcolor="rgba(240,255,240,0.3)",
)

st.plotly_chart(fig, use_container_width=True)
