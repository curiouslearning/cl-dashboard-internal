import streamlit as st
import pandas as pd
import plotly.express as px

import ui_widgets as ui
from users import ensure_user_data_initialized
from settings import initialize

# Wherever your tile function actually lives
from ui_components import show_dual_metric_tiles

initialize()
ensure_user_data_initialized()

df_cr_book_user_cohorts = st.session_state["df_cr_book_user_cohorts"]
df_cr_users = st.session_state["df_cr_users"]

# ----------------------------
# Helpers
# ----------------------------
def _clean_str_aligned(s: pd.Series) -> pd.Series:
    """Return a cleaned string series WITHOUT changing index alignment."""
    return s.fillna("").astype(str).str.strip()

def _truncate_csv(text: str, max_chars: int = 120) -> str:
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    if "," in cut:
        cut = cut.rsplit(",", 1)[0]
    return cut + "…"

# ----------------------------
# Book languages for selector (safe: we can drop empties AFTER cleaning)
# ----------------------------
book_languages = (
    _clean_str_aligned(df_cr_book_user_cohorts["app_language_book"])
    .loc[lambda s: s.ne("")]
    .unique()
)
book_languages = sorted(book_languages)

selected_languages = ui.multi_select_all(book_languages, "Select Book Languages", key="book-1")
effective_book_languages = book_languages if (not selected_languages or "All" in selected_languages) else selected_languages

# Clean language display (caption + hover)
if "All" in (selected_languages or []):
    lang_help = ", ".join(book_languages)
    lang_caption = "All book languages"
else:
    lang_help = ", ".join(effective_book_languages)
    lang_caption = _truncate_csv(lang_help, max_chars=120)

st.caption(f"Showing engagement for: {lang_caption}", help=lang_help)

# -----------------------------------------
# Mapping: book language -> FTM app_language
# -----------------------------------------
lang_map = df_cr_book_user_cohorts[["app_language_book", "app_language"]].copy()
lang_map["app_language_book"] = _clean_str_aligned(lang_map["app_language_book"])
lang_map["app_language"] = _clean_str_aligned(lang_map["app_language"])

lang_map = lang_map.loc[(lang_map["app_language_book"] != "") & (lang_map["app_language"] != "")]
lang_map = lang_map.drop_duplicates()

mapped_ftm_languages = (
    lang_map.loc[lang_map["app_language_book"].isin(effective_book_languages), "app_language"]
    .unique()
    .tolist()
)

# -------------------------------------------------------
# Denominator: eligible FTM users (in mapped FTM languages)
# -------------------------------------------------------
df_cr_users_tmp = df_cr_users.copy()
df_cr_users_tmp["app_language_clean"] = _clean_str_aligned(df_cr_users_tmp["app_language"])

cr_users_book_universe = (
    df_cr_users_tmp.loc[
        df_cr_users_tmp["app_language_clean"].isin(mapped_ftm_languages),
        ["cr_user_id", "app_language"],
    ]
    .drop_duplicates(subset=["cr_user_id"])
)

denominator_users = int(cr_users_book_universe["cr_user_id"].nunique())

# -------------------------------------------------------
# Tier attribution for the pie (language-mapped tiers only)
# -------------------------------------------------------
df_cohorts_tmp = df_cr_book_user_cohorts.copy()
df_cohorts_tmp["app_language_book_clean"] = _clean_str_aligned(df_cohorts_tmp["app_language_book"])

tier_df_mapped = (
    df_cohorts_tmp.loc[
        df_cohorts_tmp["app_language_book_clean"].isin(effective_book_languages),
        ["cr_user_id", "book_engagement_tier"],
    ]
    .drop_duplicates(subset=["cr_user_id"])
)

tier_df_mapped["book_engagement_tier"] = (
    pd.to_numeric(tier_df_mapped["book_engagement_tier"], errors="coerce")
    .fillna(0)
    .astype(int)
)

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
cohort_flags["app_language_book_clean"] = _clean_str_aligned(cohort_flags["app_language_book"])

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

df_pie_book_tiers = (
    pie_base.groupby("book_engagement_tier", as_index=False)["cr_user_id"]
    .nunique()
    .rename(columns={"cr_user_id": "users"})
)

df_pie_book_tiers["tier_label"] = df_pie_book_tiers["book_engagement_tier"].map(TIER_LABELS).fillna("Unknown")
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
)

fig_book_tier_pie.update_traces(
    textinfo="percent+label",
    textposition="inside",
    sort=False,
    hovertemplate=(
        "<b>%{label}</b><br>"
        "Users: %{value:,}<br>"
        "Share: %{percent}<extra></extra>"
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


