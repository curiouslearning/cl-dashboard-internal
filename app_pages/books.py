import streamlit as st
import pandas as pd
import plotly.express as px

import ui_widgets as ui
from users import ensure_user_data_initialized
from settings import initialize

from ui_components import plot_days_to_ra_by_tier, show_dual_metric_tiles, build_survival_curve_by_tier
import books_helpers as bh

initialize()
ensure_user_data_initialized()

df_cr_book_user_cohorts = st.session_state["df_cr_book_user_cohorts"]
df_cr_users = st.session_state["df_cr_users"]

# -------------------------------------------------------
# Helper: definition expander
# -------------------------------------------------------
HIDE_INDEX_CSS = """
    <style>
    thead tr th:first-child {display:none}
    tbody th {display:none}
    </style>
"""

def display_definitions_table(title, def_df):
    expander = st.expander(title)
    st.markdown(HIDE_INDEX_CSS, unsafe_allow_html=True)
    expander.table(def_df)


# -------------------------------------------------------
# Page-level notes expander
# -------------------------------------------------------
page_notes = pd.DataFrame(
    [
        ["Universe",
         "Eligible users are CR users whose FTM app_language maps to an available book language. "
         "Non-book users (Tier 0) are included so the full population is visible."],
        ["Language mapping",
         "Book languages are mapped to FTM app_language via a canonical lookup. "
         "Some users read books in a language different from their primary FTM language — "
         "these appear as 'unmapped' readers."],
        ["Online sessions only",
         "All book engagement data is based on GA4/Firebase events. "
         "Offline reading is not captured and will cause engagement to be understated."],
        ["FTM outcomes",
         "FTM progression metrics are restricted to LA users (learners who completed Level 1) "
         "in the mapped language universe. The relationship between book engagement and FTM "
         "outcomes is associative — causality has not been established."],
        ["Days to RA",
         "Average days from first app open to reaching Reader Acquired (FTM level 25+). "
         "Only includes users who actually reached RA."],
    ],
    columns=["Note", "Description"],
)
display_definitions_table("ℹ️ About this page", page_notes)

# -------------------------------------------------------
# Language selector
# -------------------------------------------------------
book_languages = bh.get_book_languages(df_cr_book_user_cohorts)

c1, c2 = st.columns(2)
with c1:
    selected_languages = ui.multi_select_all(book_languages, "Select Book Languages", key="book-1")

effective_book_languages = book_languages if (not selected_languages or "All" in selected_languages) else selected_languages

if "All" in (selected_languages or []):
    lang_help = ", ".join(book_languages)
    lang_caption = "All book languages"
else:
    lang_help = ", ".join(effective_book_languages)
    lang_caption = bh.truncate_csv(lang_help, max_chars=120)

st.caption(f"Showing engagement for: {lang_caption}", help=lang_help)

# -------------------------------------------------------
# Language mapping
# -------------------------------------------------------
lang_map = bh.compute_lang_map(df_cr_book_user_cohorts)
mapped_ftm_languages = bh.mapped_ftm_languages_for_books(lang_map, effective_book_languages)

# -------------------------------------------------------
# Denominator: eligible FTM users
# -------------------------------------------------------
cr_users_book_universe = bh.eligible_ftm_users(df_cr_users, mapped_ftm_languages)
denominator_users = int(cr_users_book_universe["cr_user_id"].nunique())

# -------------------------------------------------------
# Tier attribution
# -------------------------------------------------------
tier_df_mapped = bh.tier_df_language_mapped(df_cr_book_user_cohorts, effective_book_languages)

pie_base = cr_users_book_universe.merge(tier_df_mapped, on="cr_user_id", how="left")
pie_base["book_engagement_tier"] = (
    pd.to_numeric(pie_base["book_engagement_tier"], errors="coerce")
    .fillna(0)
    .astype(int)
)

mapped_readers = int((pie_base["book_engagement_tier"] > 0).sum())
uptake = (mapped_readers / denominator_users) if denominator_users else 0.0

# -------------------------------------------------------
# Unmapped readers
# -------------------------------------------------------
cohort_flags = df_cr_book_user_cohorts[["cr_user_id", "is_book_user", "app_language_book"]].drop_duplicates(subset=["cr_user_id"]).copy()
cohort_flags["app_language_book_clean"] = bh.clean_str_aligned(cohort_flags["app_language_book"])
cohort_flags["is_book_user"] = cohort_flags["is_book_user"].astype(bool)

unmapped_in_eligible = cr_users_book_universe[["cr_user_id"]].merge(cohort_flags, on="cr_user_id", how="left")
unmapped_readers = int(
    unmapped_in_eligible.loc[
        (unmapped_in_eligible["is_book_user"] == True) &
        (unmapped_in_eligible["app_language_book_clean"] == ""),
        "cr_user_id",
    ].nunique()
)

# -------------------------------------------------------
# Metric tiles
# -------------------------------------------------------
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

show_dual_metric_tiles("Metrics", book_kpis, formats=book_formats)
st.caption("Some users read books in a language different from their primary FTM language.")

# -------------------------------------------------------
# Tier pie chart
# -------------------------------------------------------
tier_notes = pd.DataFrame(
    [
        ["Tier 0 — No book use",    "User is in an eligible language but has no recorded book activity online."],
        ["Tier 1 — Tried once",     "total_active_book_days = 1 across all books."],
        ["Tier 2 — Returning reader", "total_active_book_days ≥ 2, OR distinct books ≥ 2, OR any book with ≥ 2 active days."],
        ["Tier 3 — Highly engaged", "total_active_book_days ≥ 3 AND (distinct books ≥ 3, OR ≥ 2 books with ≥ 2 days, OR book span ≥ 3 days)."],
        ["Offline caveat",          "Users who read exclusively offline will appear as Tier 0 even if they engaged deeply."],
    ],
    columns=["Tier", "Definition"],
)
display_definitions_table("ℹ️ Tier definitions", tier_notes)

TIER_LABELS = {
    0: "No book use",
    1: "Tried once",
    2: "Returning reader",
    3: "Highly engaged",
}

TIER_HOVER_DEFS = {
    "No book use":      "Tier 0: not a book user (no recorded book activity)",
    "Tried once":       "Tier 1: total_active_book_days = 1",
    "Returning reader": "Tier 2: active days ≥ 2 OR distinct books ≥ 2 OR any book with ≥2 active days",
    "Highly engaged":   "Tier 3: active days ≥ 3 AND (distinct books ≥ 3 OR ≥2 books with ≥2 days OR span ≥ 3 days)",
    "Unknown":          "Tier ?: definition unavailable",
}

df_pie_book_tiers = (
    pie_base.groupby("book_engagement_tier", as_index=False)["cr_user_id"]
    .nunique()
    .rename(columns={"cr_user_id": "users"})
)
df_pie_book_tiers["tier_label"] = df_pie_book_tiers["book_engagement_tier"].map(TIER_LABELS).fillna("Unknown")
df_pie_book_tiers["tier_def"]   = df_pie_book_tiers["tier_label"].map(TIER_HOVER_DEFS).fillna(TIER_HOVER_DEFS["Unknown"])
df_pie_book_tiers["tier_order"] = df_pie_book_tiers["book_engagement_tier"]
df_pie_book_tiers = df_pie_book_tiers.sort_values("tier_order")

from colors import PALETTE

PIE_COLOR_MAP = {
    "No book use":      PALETTE["pink"],
    "Tried once":       PALETTE["peach"],
    "Returning reader": PALETTE["green"],
    "Highly engaged":   PALETTE["blue"],
    "Unknown":          PALETTE["purple"],
}

fig_book_tier_pie = px.pie(
    df_pie_book_tiers,
    names="tier_label",
    values="users",
    color="tier_label",
    color_discrete_map=PIE_COLOR_MAP,
    hole=0,
    custom_data=["tier_def"],
)
fig_book_tier_pie.update_traces(
    textinfo="percent+label",
    textposition="inside",
    sort=False,
    hovertemplate="<b>%{label}</b><br>%{customdata[0]}<br><br>",
)
fig_book_tier_pie.update_layout(
    title_text="Book engagement tiers",
    legend_title_text="Tier",
    margin=dict(l=20, r=20, t=55, b=20),
)
st.plotly_chart(fig_book_tier_pie, use_container_width=True)
st.caption(
    "Engagement tiers are based on active reading days and breadth/depth of book usage. "
    "'No book use' means the user is in an eligible language but has no recorded book activity."
)

# -------------------------------------------------------
# FTM outcomes
# -------------------------------------------------------
st.divider()
st.header("FTM outcomes (LA users only)")

ftm_notes = pd.DataFrame(
    [
        ["Users",            "Number of LA users (completed Level 1) in the mapped universe for this tier."],
        ["Avg Furthest Level", "Average maximum FTM level reached across all users in this tier."],
        ["Avg Time (min)",   "Average total time played in FTM (minutes)."],
        ["% RA",             "Percentage who reached Reader Acquired (FTM level 25+)."],
        ["% Reach L2",       "Percentage who reached Level 2 — early friction test."],
        ["% Reach L4",       "Percentage who reached Level 4 — early block completion."],
        ["% Reach L10",      "Percentage who reached Level 10 — sustained engagement entry."],
        ["% Reach L25",      "Percentage who reached Level 25 — RA threshold."],
        ["Milestone levels", "L2, L4, L10, L25 are chosen based on observed behavioral "
                             "breakpoints in the FTM survival curve."],
    ],
    columns=["Column", "Description"],
)
display_definitions_table("ℹ️ Column definitions", ftm_notes)

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

df_ftm_display = df_ftm_compare[["book_engagement_tier"] + milestone_cols].rename(columns={
    "book_engagement_tier":   "Tier",
    "users":                  "Users",
    "avg_furthest_level":     "Avg Furthest Level",
    "avg_total_time_minutes": "Avg Time (min)",
    "pct_ra":                 "% RA",
    "pct_reach_2":            "% Reach L2",
    "pct_reach_4":            "% Reach L4",
    "pct_reach_10":           "% Reach L10",
    "pct_reach_25":           "% Reach L25",
})

st.dataframe(
    df_ftm_display.style
        .format({
            "Users":              "{:,.0f}",
            "Avg Furthest Level": "{:.2f}",
            "Avg Time (min)":     "{:.1f}",
            "% RA":               "{:.1%}",
            "% Reach L2":         "{:.1%}",
            "% Reach L4":         "{:.1%}",
            "% Reach L10":        "{:.1%}",
            "% Reach L25":        "{:.1%}",
        })
        .hide(axis="index"),
    use_container_width=True,
)

# -------------------------------------------------------
# Survival curve — all tiers, no selector
# -------------------------------------------------------
st.subheader("Survival curve by book engagement tier")

max_level = st.slider("Max level shown", 10, 60, 35, key="books-survival-maxlvl")

df_survival, fig_survival = build_survival_curve_by_tier(
    df_ftm_base=df_ftm_base,
    max_level=max_level,
    tiers_to_plot=[0, 1, 2, 3],
    include_overall_baseline=True,
)

st.plotly_chart(fig_survival, use_container_width=True)
st.caption(
    "Each line shows the % of LA users in the mapped universe reaching each level. "
    "Early separation suggests reduced friction; tail separation suggests long-term persistence."
)

# -------------------------------------------------------
# Days to RA
# -------------------------------------------------------
st.divider()
st.subheader("Average days to RA by book engagement tier")

agg_df = bh.build_days_to_ra_by_tier(df_cr_users, df_cr_book_user_cohorts)
fig = plot_days_to_ra_by_tier(agg_df)
st.plotly_chart(fig, use_container_width=True)