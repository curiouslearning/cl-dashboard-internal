import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import itertools

from settings import get_gcp_credentials
from ui_widgets import display_definitions_table, get_apps

# =========================================================
# 🎨 Page Setup + Global Styles
# =========================================================
st.set_page_config(page_title="Level Difficulty Analysis", layout="wide")

# Center & soften captions
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

# Global color palette (autumn tones)
AUTUMN_PALETTE = [
    "#B35C1E", "#C1440E", "#E17E26", "#EBA937", "#F3D250",
    "#8CB369", "#3B7A57", "#9C3F0E", "#8E6C88", "#5B2333"
]

# =========================================================
# 🛠️ Helper Utilities
# =========================================================

def get_color_map(keys, palette):
    """
    Create a stable color mapping based on given palette and key order.
    """
    cycle = itertools.cycle(palette)
    return {k: next(cycle) for k in keys}


def style_line_chart(fig, legend_title):
    """
    Apply consistent styling to line charts for visual uniformity.
    """
    fig.update_traces(
        mode="lines+markers",
        line=dict(width=2.0),
        marker=dict(size=5, opacity=0.6, symbol="circle", line=dict(width=0)),
    )

    fig.update_layout(
        height=600,
        margin=dict(t=70, l=50, r=30, b=50),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13, color="#222"),
        hovermode="closest",
        legend=dict(
            title=legend_title,
            yanchor="top", y=0.99,
            xanchor="left", x=1.02,
            itemsizing="constant",
            traceorder="normal",
            tracegroupgap=4,
        ),
    )

    return fig


def style_bar_chart(fig, legend_title):
    """
    Apply consistent styling for bar charts.
    """
    fig.update_layout(
        height=700,
        margin=dict(t=80, l=60, r=40, b=60),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13, color="#222"),
        yaxis=dict(autorange="reversed"),
        legend=dict(
            title=legend_title,
            yanchor="top", y=0.99,
            xanchor="left", x=1.02,
            itemsizing="constant",
            traceorder="normal",
            tracegroupgap=4,
        ),
    )
    return fig


def assign_hover(fig, df, group_col, custom_cols, title):
    """
    Assign custom hover data for each trace based on group (language/app).
    """
    for trace in fig.data:
        name = trace.name
        sub = df[df[group_col] == name]
        trace.customdata = sub[custom_cols].to_numpy().tolist()
        trace.hovertemplate = (
            f"<b>{title}:</b> %{{customdata[0]}}<br>"
            "<b>Level:</b> %{x}<br>"
            "<b>Difficulty:</b> %{y:.2f}<br>"
            "Success Rate: %{customdata[1]:.2f}<br>"
            "Puzzle Failure Rate: %{customdata[2]:.2f}<br>"
            "Avg Puzzles Solved: %{customdata[3]:.2f}<br>"
            "Puzzle Failures: %{customdata[4]}<br>"
            "Users: %{customdata[5]}<br>"
            "Attempts: %{customdata[6]}<extra></extra>"
        )


@st.cache_data(show_spinner=False)
def load_data():
    """
    Load difficulty data from BigQuery and cache for performance.
    """
    _, client = get_gcp_credentials()
    query = """
    SELECT
      language, level_number, app,
      total_attempts, total_success, total_failure,
      success_rate, avg_success_puzzles,
      total_puzzle_failures, total_puzzle_attempts,
      puzzle_failure_rate, relative_difficulty_score,
      unique_users
    FROM `dataexploration-193817.user_data.ftm_level_difficulty_by_language`
    WHERE total_attempts >= 10
    ORDER BY language, level_number
    """
    return client.query(query).to_dataframe()


# =========================================================
# 📊 METRIC DEFINITIONS TABLE
# =========================================================
st.markdown("## 📊 Level Difficulty Analysis")

data_metrics = pd.DataFrame([
    ("Adjusted Relative Difficulty Score", "Measures level challenge via completion difficulty + puzzle struggle."),
    ("Success Rate", "Share of successful level attempts."),
    ("Puzzle Failure Rate", "Percent of puzzles failed within the level."),
    ("Total Puzzle Failures", "Total puzzle failures across all plays."),
    ("Average Puzzles Solved", "Avg puzzles solved per attempt.")
], columns=["Metric", "Definition"])

display_definitions_table("Data & Metric Notes", data_metrics)

# =========================================================
# 🧠 LOAD DATA
# =========================================================
df = load_data()
if df.empty:
    st.warning("No data found. Try lowering the attempt threshold.")
    st.stop()

# =========================================================
# 🎛️ LANGUAGE CONTROLS
# =========================================================
st.markdown("### 📈 Difficulty Curve by Language")

lang_totals = df.groupby("language")["total_attempts"].sum().sort_values(ascending=False).reset_index()
c1, c2 = st.columns([2, 4])
top_n = c1.slider("Top N languages by total gameplay volume", 1, 60, 5)
selected_langs = c2.multiselect("Select languages to display", sorted(df["language"].unique()), default=lang_totals.head(top_n)["language"])

df_lang = df[df["language"].isin(selected_langs)]
if df_lang.empty:
    st.info("No data available for selected languages.")
    st.stop()

# color map
lang_color_map = get_color_map(selected_langs, AUTUMN_PALETTE)

# =========================================================
# 📈 Language Difficulty Curve
# =========================================================
language_cols = ["language","success_rate","puzzle_failure_rate","avg_success_puzzles","total_puzzle_failures","unique_users","total_attempts"]

fig_lang = px.line(
    df_lang,
    x="level_number", y="relative_difficulty_score", color="language",
    color_discrete_map=lang_color_map,
    category_orders={"language": selected_langs},
    title="Adjusted Relative Difficulty Curve by Language"
)

assign_hover(fig_lang, df_lang, "language", language_cols, "Language")
fig_lang = style_line_chart(fig_lang, "Language")
st.plotly_chart(fig_lang, use_container_width=True)
st.caption("Each line shows difficulty progression across levels for selected languages.")

# =========================================================
# 🥇 Top Hardest Levels (Language)
# =========================================================
st.markdown("### 🥇 Top Hardest Levels by Language")
num_levels = st.slider("Top N hardest levels per language", 1, 80, 10)

df_hard = (
    df_lang.sort_values(["language","relative_difficulty_score"], ascending=[True,False])
    .groupby("language", group_keys=False).head(num_levels)
    .drop_duplicates(subset=["language","level_number"])
)

fig_hard = px.bar(
    df_hard,
    x="relative_difficulty_score", y="level_number", color="language",
    orientation="h",
    color_discrete_map=lang_color_map,
    category_orders={"language": selected_langs},
    title=f"Top {num_levels} Hardest Levels per Language"
)

assign_hover(fig_hard, df_hard, "language", language_cols, "Language")
fig_hard = style_bar_chart(fig_hard, "Language")
st.plotly_chart(fig_hard, use_container_width=True)
st.caption("Bars highlight toughest levels across selected languages.")

# =========================================================
# 🎮 APP COMPARISON
# =========================================================
st.markdown("### 🎮 Difficulty Curve by App")

apps = [a for a in get_apps() if a not in ["Unity", "CR", "WBS-standalone"]]

selected_apps = st.multiselect("Select apps to compare", apps, default=apps[:4])
df_app = df[df["app"].isin(selected_apps)]

if df_app.empty:
    st.info("No data available for selected apps.")
    st.stop()

app_color_map = get_color_map(selected_apps, AUTUMN_PALETTE)

app_cols = ["app","success_rate","puzzle_failure_rate","avg_success_puzzles","total_puzzle_failures","unique_users","total_attempts"]

fig_app = px.line(
    df_app,
    x="level_number", y="relative_difficulty_score", color="app",
    color_discrete_map=app_color_map,
    category_orders={"app": selected_apps},
    title="Adjusted Relative Difficulty Curve by App"
)

assign_hover(fig_app, df_app, "app", app_cols, "App")
fig_app = style_line_chart(fig_app, "App")
st.plotly_chart(fig_app, use_container_width=True)
st.caption("Each line shows difficulty curve by app version.")

# =========================================================
# 🧮 LOG VISUALIZATION
# =========================================================
st.markdown("### 🧮 Understanding the Log Weight in the Difficulty Formula")

attempts = np.linspace(1, 1000, 200)
log_weight = np.log1p(attempts)

fig_log = go.Figure()
fig_log.add_trace(
    go.Scatter(
        x=attempts, y=log_weight, mode="lines",
        line=dict(width=3),
        hovertemplate="Attempts: %{x:.0f}<br>Weight: %{y:.2f}"
    )
)

fig_log.update_layout(
    title="How the Log Function Stabilizes Difficulty Weighting",
    xaxis_title="Total Attempts", yaxis_title="log(1 + attempts)",
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    height=400, margin=dict(t=60,l=60,r=30,b=60),
)

st.plotly_chart(fig_log, use_container_width=True)
st.caption("Log growth stabilizes difficulty — early plays affect more than late plays.")
