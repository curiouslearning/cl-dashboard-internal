import streamlit as st
import pandas as pd
import plotly.express as px

import ui_widgets as ui
from users import ensure_user_data_initialized
from settings import initialize

from ui_components import show_dual_metric_tiles,build_survival_curve_by_tier
import books_helpers as bh


initialize()
ensure_user_data_initialized()

df_cr_book_user_cohorts = st.session_state["df_cr_book_user_cohorts"]
df_cr_users = st.session_state["df_cr_users"]

book_languages = bh.get_book_languages(df_cr_book_user_cohorts)

c1, c2 = st.columns(2)
with c1:
    selected_languages = ui.multi_select_all(book_languages, "Select Book Languages", key="book-1")
    
effective_book_languages = book_languages if (not selected_languages or "All" in selected_languages) else selected_languages

# Clean language display (caption + hover)
if "All" in (selected_languages or []):
    lang_help = ", ".join(book_languages)
    lang_caption = "All book languages"
else:
    lang_help = ", ".join(effective_book_languages)
    lang_caption = bh.truncate_csv(lang_help, max_chars=120)

st.caption(f"Showing engagement for: {lang_caption}", help=lang_help)

# -----------------------------------------
# Mapping: book language -> FTM app_language
# -----------------------------------------
lang_map = bh.compute_lang_map(df_cr_book_user_cohorts)
mapped_ftm_languages = bh.mapped_ftm_languages_for_books(lang_map, effective_book_languages)

# -------------------------------------------------------
# Denominator: eligible FTM users (in mapped FTM languages)
# -------------------------------------------------------
cr_users_book_universe = bh.eligible_ftm_users(df_cr_users, mapped_ftm_languages)
denominator_users = int(cr_users_book_universe["cr_user_id"].nunique())

# -------------------------------------------------------
# Tier attribution for the pie (language-mapped tiers only)
# -------------------------------------------------------
tier_df_mapped = bh.tier_df_language_mapped(df_cr_book_user_cohorts, effective_book_languages)

pie_base = cr_users_book_universe.merge(tier_df_mapped, on="cr_user_id", how="left")
pie_base["book_engagement_tier"] = (
    pd.to_numeric(pie_base["book_engagement_tier"], errors="coerce")
    .fillna(0)
    .astype(int)
)

# Language-mapped readers
mapped_readers = int((pie_base["book_engagement_tier"] > 0).sum())
uptake = (mapped_readers / denominator_users) if denominator_users else 0.0

# -------------------------------------------------------
# Unmapped readers metric (within eligible universe)
# -------------------------------------------------------
cohort_flags = df_cr_book_user_cohorts[["cr_user_id", "is_book_user", "app_language_book"]].drop_duplicates(subset=["cr_user_id"]).copy()
cohort_flags["app_language_book_clean"] = bh.clean_str_aligned(cohort_flags["app_language_book"])

# robust boolean conversion (handles True/False, 0/1, "true"/"false")
cohort_flags["is_book_user"] = cohort_flags["is_book_user"].astype(bool)

unmapped_in_eligible = cr_users_book_universe[["cr_user_id"]].merge(cohort_flags, on="cr_user_id", how="left")

unmapped_readers = int(
    unmapped_in_eligible.loc[
        (unmapped_in_eligible["is_book_user"] == True) &
        (unmapped_in_eligible["app_language_book_clean"] == ""),
        "cr_user_id",
    ].nunique()
)

# ----------------------------
# Metric tiles (YOUR function)
# ----------------------------
book_kpis = {
    "Eligible users": denominator_users,
    "Book readers (language-mapped)": mapped_readers,
    "Uptake": uptake,
    "Book readers (unmapped)": unmapped_readers,
}

book_formats = {
    "Eligible users": "{:,.0f}",
    "Book readers (language-mapped)": "{:,.0f}",
    "Book readers (unmapped)": "{:,.0f}",
    "Uptake": lambda v: f"{v:.1%}",
}

show_dual_metric_tiles(
    "Metrics",
    book_kpis,
    formats=book_formats
)

st.caption("Some users read books in a language different from their primary FTM language.")

# ----------------------------
# Pie data + labels
# ----------------------------
TIER_LABELS = {
    0: "No book use",
    1: "Tried once",
    2: "Returning reader",
    3: "Highly engaged",
}

TIER_HOVER_DEFS = {
    "No book use": "Tier 0: not a book user (no recorded book activity)",
    "Tried once": "Tier 1: total_active_book_days = 1",
    "Returning reader": "Tier 2: active days ≥ 2 OR distinct books ≥ 2 OR any book with ≥2 active days",
    "Highly engaged": "Tier 3: active days ≥ 3 AND (distinct books ≥ 3 OR ≥2 books with ≥2 days OR span ≥ 3 days)",
    "Unknown": "Tier ?: definition unavailable",
}

df_pie_book_tiers = (
    pie_base.groupby("book_engagement_tier", as_index=False)["cr_user_id"]
    .nunique()
    .rename(columns={"cr_user_id": "users"})
)
df_pie_book_tiers["tier_label"] = (
    df_pie_book_tiers["book_engagement_tier"]
    .map(TIER_LABELS)
    .fillna("Unknown")
)

df_pie_book_tiers["tier_def"] = (
    df_pie_book_tiers["tier_label"]
    .map(TIER_HOVER_DEFS)
    .fillna(TIER_HOVER_DEFS["Unknown"])
)

df_pie_book_tiers["tier_order"] = df_pie_book_tiers["book_engagement_tier"]
df_pie_book_tiers = df_pie_book_tiers.sort_values("tier_order")

# ----------------------------
# Pie colors (tile-like pastel vibe)
from colors import PALETTE

PIE_COLOR_MAP = {
    "No book use": PALETTE["pink"],
    "Tried once": PALETTE["peach"],
    "Returning reader": PALETTE["green"],
    "Highly engaged": PALETTE["blue"],
    "Unknown": PALETTE["purple"],
}

fig_book_tier_pie = px.pie(
    df_pie_book_tiers,
    names="tier_label",
    values="users",
    color="tier_label",
    color_discrete_map=PIE_COLOR_MAP,
    hole=0,
    custom_data=["tier_def"],   # <- add this
)


fig_book_tier_pie.update_traces(
    textinfo="percent+label",
    textposition="inside",
    sort=False,
    hovertemplate=(
        "<b>%{label}</b><br>"
        "%{customdata[0]}<br><br>"
    ),
)

fig_book_tier_pie.update_layout(
    title_text="Book engagement tiers",
    legend_title_text="Tier",
    margin=dict(l=20, r=20, t=55, b=20),
)

st.plotly_chart(fig_book_tier_pie, use_container_width=True)

st.caption(
    "Engagement tiers are based on active reading days and breadth/depth of book usage. "
    "‘No book use’ means the user is in an eligible language but has no recorded book activity."
)


st.divider()
st.header("FTM outcomes (LA users only)")

df_ftm_base, df_ftm_compare = bh.build_ftm_compare_la_only(
    df_cr_users=df_cr_users,
    eligible_users_df=cr_users_book_universe,
    tier_df_mapped=tier_df_mapped,
    ra_level_threshold=25,
)

milestone_cols = [
    "users",
    "avg_furthest_level",
    "avg_total_time_minutes",
    "pct_ra",
    "pct_reach_2",
    "pct_reach_4",
    "pct_reach_10",
    "pct_reach_25",
]

st.subheader("Milestone reach rates by tier (LA users, mapped universe)")

st.dataframe(
    df_ftm_compare[["book_engagement_tier"] + milestone_cols].style.format({
        "users": "{:,.0f}",
        "avg_furthest_level": "{:.2f}",
        "avg_total_time_minutes": "{:.1f}",
        "pct_ra": "{:.1%}",
        "pct_reach_2": "{:.1%}",
        "pct_reach_4": "{:.1%}",
        "pct_reach_10": "{:.1%}",
        "pct_reach_25": "{:.1%}",
    }),
    use_container_width=True,
)

st.subheader("Survival curve by book engagement tier")
c1, c2 = st.columns([1,2])
with c1:
    tiers_to_plot = st.multiselect(
        "Show tiers",
        [0, 1, 2, 3],
        default=[0, 1, 2, 3],
        key="books-survival-tiers",
    )

max_level = st.slider("Max level shown", 10, 60, 35, key="books-survival-maxlvl")

df_survival, fig_survival = build_survival_curve_by_tier(
    df_ftm_base=df_ftm_base,
    max_level=max_level,
    tiers_to_plot=tiers_to_plot,
    include_overall_baseline=True,  # baseline is within mapped LA universe
)

st.plotly_chart(fig_survival, use_container_width=True)

st.caption(
    "Each line shows the % of LA users in the mapped universe reaching each level. "
    "Early separation suggests reduced friction; tail separation suggests long-term persistence."
)
