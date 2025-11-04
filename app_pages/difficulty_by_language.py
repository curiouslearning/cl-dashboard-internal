import streamlit as st
import pandas as pd
import plotly.express as px
import itertools
from settings import get_gcp_credentials
from ui_widgets import display_definitions_table

# --------------------------------------
# 🎨 Global Style Tweaks (center + tighten captions)
# --------------------------------------
st.markdown("""
    <style>
    div[data-testid="stCaptionContainer"] {
        margin-top: -0.8rem;
        margin-bottom: 0.2rem;
        text-align: center;
        color: #555;
        font-style: italic;
    }
    </style>
""", unsafe_allow_html=True)

autumn_palette = [
    "#B35C1E",  # copper rust
    "#C1440E",  # deep orange-red
    "#E17E26",  # warm pumpkin
    "#EBA937",  # golden amber
    "#F3D250",  # sunflower
    "#8CB369",  # muted olive green
    "#3B7A57",  # deep forest teal
    "#9C3F0E",  # rustic brown
    "#8E6C88",  # mauve plum (neutral anchor)
    "#5B2333",  # dark burgundy
]
color_cycle = itertools.cycle(autumn_palette)

# --------------------------------------
# 1️⃣ Data Definitions
# --------------------------------------
data_metrics = pd.DataFrame(
    [
        [
            "Adjusted Relative Difficulty Score",
            (
                "Measures how challenging each level is, combining level completion difficulty "
                "and puzzle-level struggle. It multiplies the level failure rate by the log of total attempts "
                "and boosts the result based on the proportion of puzzle failures. "
                "Formula: (1 − success_rate) × log(1 + total_attempts) × (1 + puzzle_failure_rate). "
                "Higher scores indicate levels where learners fail more often or struggle with puzzles."
            ),
        ],
        [
            "Success Rate",
            (
                "The share of level_completed events that were successful. "
                "A high success rate indicates learners complete the level easily."
            ),
        ],
        [
            "Puzzle Failure Rate",
            (
                "The percentage of all puzzle attempts within this level that ended in failure. "
                "High puzzle failure rates indicate internal level difficulty even if the level is eventually completed."
            ),
        ],
        [
            "Total Puzzle Failures",
            (
                "The total number of failed puzzles attempted within this level across all users. "
                "Helps identify specific levels where learners consistently struggle."
            ),
        ],
        [
            "Average Puzzles Solved",
            (
                "Average number of puzzles successfully completed within a level attempt. "
                "Provides insight into within-level progression and learner persistence."
            ),
        ],
    ],
    columns=["Metric", "Definition"],
)

st.markdown("## 📊 Level Difficulty Analysis")
display_definitions_table("Data & Metric Notes", data_metrics)

# --------------------------------------
# 2️⃣ Load Data from BigQuery
# --------------------------------------
_, bq_client = get_gcp_credentials()

query = """
SELECT
  language,
  level_number,
  total_attempts,
  total_success,
  total_failure,
  success_rate,
  avg_success_puzzles,
  total_puzzle_failures,
  total_puzzle_attempts,
  puzzle_failure_rate,
  relative_difficulty_score,
  unique_users
FROM `dataexploration-193817.user_data.ftm_level_difficulty_by_language`
WHERE total_attempts >= 10
ORDER BY language, level_number
"""
df_difficulty = bq_client.query(query).to_dataframe()

if df_difficulty.empty:
    st.warning("No data found. Try lowering the attempt threshold.")
    st.stop()

# --------------------------------------
# 3️⃣ Controls
# --------------------------------------
st.markdown("### 📈 Adjusted Relative Difficulty Curve by Language")

lang_summary = (
    df_difficulty.groupby("language")["total_attempts"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)

c1, c2 = st.columns([2, 4])
top_n = c1.slider("Top N languages by total gameplay volume", 1, 60, 5)
st.caption("Ranked by total level attempts (successful or failed) across all learners.")

top_langs = lang_summary.head(top_n)["language"].tolist()

selected_langs = c2.multiselect(
    "Select languages to display",
    sorted(df_difficulty["language"].unique()),
    default=top_langs,
)

filtered_df = df_difficulty[df_difficulty["language"].isin(selected_langs)].copy()
if filtered_df.empty:
    st.info("No data available for selected languages.")
    st.stop()

# --------------------------------------
# 4️⃣ Shared Color Map (unified across both charts)
# --------------------------------------
# palette that matches your bottom chart look
preferred_palette = px.colors.qualitative.Bold + px.colors.qualitative.Set2

# preserve the multiselect order for legend & colors
selected_langs_ordered = list(selected_langs)  # keep order as shown in UI
color_cycle = itertools.cycle(preferred_palette)


# --------------------------------------
# 5️⃣ Difficulty Curve Chart
# --------------------------------------
custom_columns = [
    "language", "success_rate", "puzzle_failure_rate", "avg_success_puzzles",
    "total_puzzle_failures", "unique_users", "total_attempts"
]
filtered_df["customdata"] = filtered_df[custom_columns].to_numpy().tolist()

color_cycle = itertools.cycle(autumn_palette)
selected_color_map = {lang: next(color_cycle) for lang in selected_langs}

fig = px.line(
    filtered_df,
    x="level_number",
    y="relative_difficulty_score",
    color="language",
    color_discrete_map=selected_color_map,                    # <—
    category_orders={"language": selected_langs_ordered},     # <—
    title="Adjusted Relative Difficulty Curve by Language",
    labels={"level_number": "Level", "relative_difficulty_score": "Adjusted Relative Difficulty Score"},
)

fig.update_traces(
    mode="lines+markers",
    line=dict(width=2.0),
    marker=dict(size=5, opacity=0.6, symbol="circle", line=dict(width=0)),
    customdata=filtered_df["customdata"],
    hovertemplate=(
        "<b>Language:</b> %{customdata[0]}<br>"
        "<b>Level:</b> %{x}<br>"
        "<b>Difficulty:</b> %{y:.2f}<br>"
        "Success Rate: %{customdata[1]:.2f}<br>"
        "Puzzle Failure Rate: %{customdata[2]:.2f}<br>"
        "Avg Puzzles Solved: %{customdata[3]:.2f}<br>"
        "Puzzle Failures: %{customdata[4]}<br>"
        "Users: %{customdata[5]}<br>"
        "Attempts: %{customdata[6]}<extra></extra>"
    ),
)

for trace in fig.data:
    trace.mode = "lines"

fig.update_layout(
    height=550,
    margin=dict(t=70, l=50, r=30, b=50),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(size=13, color="#222"),
    hovermode="closest",
    legend=dict(
        title="Language",
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=1.02,
        itemsizing="constant",
        traceorder="normal",
        tracegroupgap=4,
    ),
    legend_traceorder="normal"
)
st.plotly_chart(fig, use_container_width=True)
st.caption("Each line represents a language’s difficulty curve based on adjusted level performance.")

# --------------------------------------
# 6️⃣ Top Hardest Levels by Language
# --------------------------------------
st.markdown("### 🥇 Top Hardest Levels by Language")

c1, c2 = st.columns([2, 4])
num_levels = c1.slider("Top N hardest levels per language", 1, 80, 10)

df_top_hardest = (
    filtered_df
    .sort_values(["language", "relative_difficulty_score"], ascending=[True, False])
    .groupby("language", group_keys=False)
    .apply(lambda g: g.head(num_levels))
    .reset_index(drop=True)
)
df_top_hardest = df_top_hardest.drop_duplicates(subset=["language", "level_number"]).dropna()

fig_top = px.bar(
    df_top_hardest,
    x="relative_difficulty_score",
    y="level_number",
    color="language",
    orientation="h",
    color_discrete_map=selected_color_map,                    # <—
    category_orders={"language": selected_langs_ordered},     # <—
    title=f"Top {num_levels} Hardest Levels per Language",
    labels={"relative_difficulty_score": "Adjusted Relative Difficulty Score", "level_number": "Level"},
)

fig_top.update_traces(
    customdata=df_top_hardest[
        [
            "language", "success_rate", "puzzle_failure_rate", "avg_success_puzzles",
            "total_puzzle_failures", "unique_users", "total_attempts",
        ]
    ].to_numpy().tolist(),
    hovertemplate=(
        "<b>Language:</b> %{customdata[0]}<br>"
        "<b>Level:</b> %{y}<br>"
        "<b>Difficulty:</b> %{x:.2f}<br>"
        "Success Rate: %{customdata[1]:.2f}<br>"
        "Puzzle Failure Rate: %{customdata[2]:.2f}<br>"
        "Avg Puzzles Solved: %{customdata[3]:.2f}<br>"
        "Puzzle Failures: %{customdata[4]}<br>"
        "Users: %{customdata[5]}<br>"
        "Attempts: %{customdata[6]}<extra></extra>"
    ),
)

fig_top.update_layout(
    height=700,
    margin=dict(t=80, l=60, r=40, b=60),
    font=dict(size=13, color="#222"),
    yaxis=dict(autorange="reversed"),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    legend=dict(
        title="Language",
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=1.02,
        itemsizing="constant",
        traceorder="normal",
        tracegroupgap=4,
    ),
    legend_traceorder="normal"
)
st.plotly_chart(fig_top, use_container_width=True)
st.caption("Each bar shows the hardest levels (by difficulty score) per selected language.")
