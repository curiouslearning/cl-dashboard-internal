import streamlit as st
from rich import print as rprint
import ui_widgets as ui
from users import ensure_user_data_initialized
from settings import initialize
import plotly.express as px
import pandas as pd

initialize()
ensure_user_data_initialized()

df_cr_book_user_cohorts = st.session_state["df_cr_book_user_cohorts"]
missing_map_readers = df_cr_book_user_cohorts.loc[
    (df_cr_book_user_cohorts["is_book_user"] == True) &
    (df_cr_book_user_cohorts["app_language_book"].isna() | (df_cr_book_user_cohorts["app_language_book"].astype(str).str.strip() == "")),
    "cr_user_id"
].nunique()

st.write(missing_map_readers, "book readers with missing app_language_book mapping")



df_cr_users = st.session_state["df_cr_users"]

# ----------------------------
# Page debug: total users
# ----------------------------
st.write(len(df_cr_users), "total FTM users")

# ----------------------------
# Book languages for selector
# ----------------------------
book_languages = (
    df_cr_book_user_cohorts["app_language_book"]
    .dropna()
    .astype(str)
    .str.strip()
    .loc[lambda s: s.ne("")]
    .unique()
)
book_languages = sorted(book_languages)

selected_languages = ui.multi_select_all(book_languages, "Select Book Languages", key="book-1")
effective_book_languages = book_languages if (not selected_languages or "All" in selected_languages) else selected_languages

# -----------------------------------------
# Mapping: book language -> FTM app_language
# -----------------------------------------
lang_map = (
    df_cr_book_user_cohorts[["app_language_book", "app_language"]]
    .dropna()
    .astype(str)
    .apply(lambda s: s.str.strip())
    .loc[lambda d: (d["app_language_book"] != "") & (d["app_language"] != "")]
    .drop_duplicates()
)

mapped_ftm_languages = (
    lang_map.loc[lang_map["app_language_book"].isin(effective_book_languages), "app_language"]
    .unique()
    .tolist()
)

# -------------------------------------------------------
# Denominator: all FTM users in mapped FTM languages
# -------------------------------------------------------
cr_users_book_universe = (
    df_cr_users.loc[
        df_cr_users["app_language"].astype(str).str.strip().isin(mapped_ftm_languages),
        ["cr_user_id", "app_language"],
    ]
    .drop_duplicates(subset=["cr_user_id"])
)

denominator_users = cr_users_book_universe["cr_user_id"].nunique()

# -------------------------------------------------------
# Tier attribution from cohorts (already includes tier 0)
# -------------------------------------------------------
tier_df = (
    df_cr_book_user_cohorts.loc[
        df_cr_book_user_cohorts["app_language_book"].astype(str).str.strip().isin(effective_book_languages),
        ["cr_user_id", "book_engagement_tier"],
    ]
    .drop_duplicates(subset=["cr_user_id"])
)

# Ensure tier is numeric
tier_df["book_engagement_tier"] = pd.to_numeric(tier_df["book_engagement_tier"], errors="coerce").fillna(0).astype(int)

# Join tiers onto denominator (left join keeps denominator authoritative)
pie_base = cr_users_book_universe.merge(tier_df, on="cr_user_id", how="left")

# Any missing tier for a denominator user should be treated as 0 (non-reader)
pie_base["book_engagement_tier"] = pd.to_numeric(pie_base["book_engagement_tier"], errors="coerce").fillna(0).astype(int)

df_pie_book_tiers = (
    pie_base.groupby("book_engagement_tier", as_index=False)["cr_user_id"]
    .nunique()
    .rename(columns={"cr_user_id": "users"})
)

# Readers = tier 1-3
readers = df_pie_book_tiers.loc[df_pie_book_tiers["book_engagement_tier"] > 0, "users"].sum()
share = readers / denominator_users if denominator_users else 0

# ----------------------------
# Labels + ordering polish
# ----------------------------
TIER_LABELS = {
    0: "No book use",
    1: "Tried once",
    2: "Returning reader",
    3: "Highly engaged",
}

df_pie_book_tiers["tier_label"] = (
    df_pie_book_tiers["book_engagement_tier"]
    .map(TIER_LABELS)
    .fillna("Unknown")
)

# Order slices in a meaningful progression
df_pie_book_tiers["tier_order"] = df_pie_book_tiers["book_engagement_tier"]
df_pie_book_tiers = df_pie_book_tiers.sort_values("tier_order")

# ----------------------------
# Header metrics (nice UX)
# ----------------------------
col1, col2, col3 = st.columns(3)
col1.metric("Eligible users", f"{denominator_users:,}")
col2.metric("Book readers", f"{readers:,}")
col3.metric("Uptake", f"{share:.1%}")

st.caption(
    "Engagement tiers are based on active reading days and breadth/depth of book usage. "
    "‘No book use’ means the user is in an eligible language but has no recorded book activity."
)

# ----------------------------
# Plotly pie
# ----------------------------
fig_book_tier_pie = px.pie(
    df_pie_book_tiers,
    names="tier_label",
    values="users",
    hole=0,
)

fig_book_tier_pie.update_traces(
    textinfo="percent+label",
    textposition="inside",
    sort=False,  # keep our tier_order instead of Plotly resorting
    hovertemplate=(
        "<b>%{label}</b><br>"
        "Users: %{value:,}<br>"
        "Share: %{percent}<extra></extra>"
    ),
)

lang_title = "All book languages" if ("All" in (selected_languages or [])) else ", ".join(effective_book_languages)

fig_book_tier_pie.update_layout(
    title_text=f"Book engagement tiers — {lang_title}",
    legend_title_text="Tier",
    margin=dict(l=20, r=20, t=60, b=20),
)

st.plotly_chart(fig_book_tier_pie, use_container_width=True)

# ----------------------------
# Optional: keep your debug info but hidden
# ----------------------------
with st.expander("Debug", expanded=False):
    st.write(len(lang_map), "rows in language map (distinct pairs)")
    st.write(len(mapped_ftm_languages), "mapped FTM languages for selection")
    st.write(len(cr_users_book_universe), "eligible FTM users (raw rows after dedupe)")
    st.write(len(tier_df), "users with a tier row")
    st.dataframe(df_pie_book_tiers)
