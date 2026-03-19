import streamlit as st
import pandas as pd

import ui_widgets as ui
from users import ensure_user_data_initialized
from settings import initialize
from ui_components import show_dual_metric_tiles
import book_details_helpers as bdh
from books_helpers import truncate_csv

initialize()
ensure_user_data_initialized()

df_book_summary    = st.session_state["df_cr_book_user_book_summary"]
df_cr_book_cohorts = st.session_state["df_cr_book_user_cohorts"]
df_cr_users        = st.session_state["df_cr_users"]

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
         "All users who have opened at least one book in the selected language(s), "
         "sourced from cr_book_user_book_summary (one row per user × book)."],
        ["Online sessions only",
         "All book metrics are based on GA4/Firebase events. Offline reading is not "
         "captured — users who read entirely offline will appear as Bounced even if "
         "they engaged deeply with the content."],
        ["Stickiness",
         "Per-book engagement level based on how many distinct days a user opened "
         "that specific book online: Bounced = 1 day, Returned = 2 days, Hooked = 3+ days."],
        ["Reader Tier vs Stickiness",
         "Reader Tier (0–3) measures overall book engagement across ALL books. "
         "Stickiness measures engagement with ONE specific book. A Tier 3 user can "
         "Bounce on a specific book if they simply preferred other titles."],
        ["FTM Outcomes",
         "FTM progression metrics (avg level, % RA) are restricted to LA users "
         "(learners who completed Level 1) in the mapped language universe. "
         "The relationship between book engagement and FTM outcomes is associative — "
         "causality has not been established."],
        ["500 reader minimum",
         "The stickiness chart excludes books with fewer than 500 readers to avoid "
         "misleading percentages from small samples."],
    ],
    columns=["Note", "Description"],
)
display_definitions_table("ℹ️ About this page", page_notes)

# -------------------------------------------------------
# Language selector
# -------------------------------------------------------
book_languages = bdh.get_book_languages_from_summary(df_book_summary)

c1, c2 = st.columns(2)
with c1:
    selected_languages = ui.multi_select_all(
        book_languages, "Select Book Languages", key="book-details-lang"
    )

effective_languages = (
    book_languages
    if (not selected_languages or "All" in selected_languages)
    else selected_languages
)

if "All" in (selected_languages or []):
    lang_caption = "All book languages"
    lang_help    = ", ".join(book_languages)
else:
    lang_help    = ", ".join(effective_languages)
    lang_caption = truncate_csv(lang_help, max_chars=120)

st.caption(f"Showing books for: {lang_caption}", help=lang_help)

# -------------------------------------------------------
# Filter summary table to selected languages
# -------------------------------------------------------
df_filtered = bdh.get_book_summary_for_language(df_book_summary, effective_languages)

if df_filtered.empty:
    st.warning("No book data found for the selected languages.")
    st.stop()

# -------------------------------------------------------
# Top-level metrics
# -------------------------------------------------------
total_books   = int(df_filtered["base_book_id"].fillna(df_filtered["book_id"]).nunique())
total_readers = int(df_filtered["cr_user_id"].nunique())
pct_hooked    = float((df_filtered["stickiness"] == "Hooked").sum()) / len(df_filtered)
pct_bounced   = float((df_filtered["stickiness"] == "Bounced").sum()) / len(df_filtered)

show_dual_metric_tiles(
    "Overview",
    {
        "Distinct books":   total_books,
        "Unique readers":   total_readers,
        "Hooked rate":      pct_hooked,
        "Bounce rate":      pct_bounced,
    },
    formats={
        "Distinct books":   "{:,.0f}",
        "Unique readers":   "{:,.0f}",
        "Hooked rate":      lambda v: f"{v:.1%}",
        "Bounce rate":      lambda v: f"{v:.1%}",
    },
)

st.caption(
    "Bounced = opened 1 day only · Returned = 2 days · Hooked = 3+ days. "
    "Online sessions only — offline reading is not captured."
)

# -------------------------------------------------------
# Section 1: Stickiness distribution per book
# -------------------------------------------------------
st.divider()
st.header("Book stickiness")

stickiness_notes = pd.DataFrame(
    [
        ["Bounced",  "User opened this book on only 1 distinct day online."],
        ["Returned", "User opened this book on exactly 2 distinct days online."],
        ["Hooked",   "User opened this book on 3 or more distinct days online."],
        ["Sort order", "Books are sorted by Hooked % descending — "
                       "highest repeat engagement at the top."],
        ["500 reader minimum", "Books with fewer than 100 readers are excluded from "
                               "this chart to avoid misleading percentages."],
    ],
    columns=["Term", "Definition"],
)
display_definitions_table("ℹ️ Stickiness definitions", stickiness_notes)

df_popularity = bdh.build_book_popularity(df_filtered)

fig_stickiness = bdh.build_stickiness_chart(
    df_popularity, min_readers=100, sort_by="Hooked"
)
st.plotly_chart(fig_stickiness, use_container_width=True)

st.caption(
    "Books at the top have the highest share of Hooked readers. "
    "High Bounced % may reflect content issues or simply that most reading happens offline."
)

# -------------------------------------------------------
# Section 2: Per-book FTM outcomes
# -------------------------------------------------------
st.divider()
st.header("FTM outcomes by book (LA users)")

ftm_notes = pd.DataFrame(
    [
        ["Book",          "Book title (language suffix removed)."],
        ["Readers",       "Number of users at the selected stickiness level who read this book."],
        ["Avg Level",     "Average FTM level reached by readers of this book (LA users only)."],
        ["Avg Level (others)", "Average FTM level reached by all other users at the same "
                               "stickiness level who did NOT read this book."],
        ["Level Lift",    "Difference in avg level: readers minus others. "
                          "Positive = readers progressed further in FTM."],
        ["% RA",          "Percentage of readers who reached Reader Acquired (FTM level 25+)."],
        ["% RA (others)", "Percentage of non-readers who reached RA."],
        ["RA Lift",       "Difference in RA rate: readers minus others."],
        ["Caution",       "Books with small reader counts (e.g. <200) show high lift but "
                          "are less statistically reliable than books with thousands of readers."],
    ],
    columns=["Column", "Description"],
)
display_definitions_table("ℹ️ Column definitions", ftm_notes)

c1, c2 = st.columns(2)
with c1:
    stickiness_filter = st.selectbox(
        "Compare readers at stickiness level",
        ["Hooked", "Returned", "Bounced"],
        key="book-details-ftm-stickiness",
        help=(
            "Compares FTM outcomes for readers at this stickiness level "
            "vs all other readers at the same level who didn't read this book."
        ),
    )

df_outcomes = bdh.build_book_ftm_outcomes(
    df_filtered=df_filtered,
    df_cr_users=df_cr_users,
    ra_level_threshold=25,
    stickiness_filter=stickiness_filter,
)

if df_outcomes.empty:
    st.info(f"No books have readers at stickiness level: {stickiness_filter}")
else:
    # Rename columns to short display names and drop index
    df_display = df_outcomes.rename(columns={
        "base_book_id":         "Book",
        "readers":              "Readers",
        "avg_level_readers":    "Avg Level",
        "avg_level_others":     "Avg Level (others)",
        "lift_avg_level":       "Level Lift",
        "pct_ra_readers":       "% RA",
        "pct_ra_others":        "% RA (others)",
        "lift_pct_ra":          "RA Lift",
    })

    st.dataframe(
        df_display.style
            .format({
                "Readers":            "{:,.0f}",
                "Avg Level":          "{:.2f}",
                "Avg Level (others)": "{:.2f}",
                "Level Lift":         "{:+.2f}",
                "% RA":               "{:.1%}",
                "% RA (others)":      "{:.1%}",
                "RA Lift":            "{:+.1%}",
            })
            .hide(axis="index"),
        use_container_width=True,
    )
    st.caption(
        f"Comparing {stickiness_filter} readers of each book vs other {stickiness_filter} "
        "readers who did not read that book. Positive lift = stronger FTM progression."
    )

# -------------------------------------------------------
# Section 3: Book drill-down
# -------------------------------------------------------
st.divider()
st.header("Book drill-down")

drilldown_notes = pd.DataFrame(
    [
        ["Reader tier × stickiness",
         "Cross-tab of overall reader tier (rows) vs stickiness for this specific book (columns). "
         "A Tier 3 user who Bounced chose not to return to this book despite being broadly engaged."],
        ["Readers by book level",
         "Some books have multiple difficulty levels (Lv1, Lv2, ...). "
         "This table shows reader counts and stickiness per level. "
         "A sharp drop between levels may indicate difficulty or disinterest at that level."],
    ],
    columns=["Section", "Description"],
)
display_definitions_table("ℹ️ Drill-down guide", drilldown_notes)

# Build popularity once (already computed above) and filter to min 100 readers
_book_reader_counts = (
    df_filtered.copy()
    .assign(base_book_id=lambda d: d["base_book_id"].fillna(d["book_id"]))
    .groupby("base_book_id")["cr_user_id"]
    .nunique()
)
available_books = sorted(
    _book_reader_counts[_book_reader_counts >= 100].index.tolist()
)

selected_book = st.selectbox(
    "Select a book", available_books, key="book-details-drilldown"
)

if selected_book:
    # --- Cross-tab: user tier × stickiness ---
    st.subheader("Reader tier × stickiness")
    df_crosstab = bdh.build_book_tier_crosstab(
        df_filtered=df_filtered,
        df_cr_book_user_cohorts=df_cr_book_cohorts,
        base_book_id=selected_book,
    )
    if df_crosstab.empty:
        st.info("No data for this book.")
    else:
        st.dataframe(df_crosstab, use_container_width=True)

    # --- Level breakdown ---
    st.subheader("Readers by book level")
    df_levels = bdh.build_book_level_breakdown(
        df_filtered=df_filtered,
        base_book_id=selected_book,
    )
    if df_levels.empty:
        st.info(
            "This book has no level variants — it exists as a single version "
            "with no Lv1/Lv2/... suffix in the book ID."
        )
    else:
        df_levels["book_level"] = df_levels["book_level"].astype(int)
        df_levels_display = df_levels.rename(columns={
            "book_level":      "Level",
            "unique_readers":  "Readers",
            "total_events":    "Events",
            "avg_active_days": "Avg Days",
            "n_bounced":       "Bounced",
            "n_returned":      "Returned",
            "n_hooked":        "Hooked",
        })
        st.dataframe(
            df_levels_display.style
                .format({
                    "Readers":  "{:,.0f}",
                    "Events":   "{:,.0f}",
                    "Avg Days": "{:.2f}",
                    "Bounced":  "{:,.0f}",
                    "Returned": "{:,.0f}",
                    "Hooked":   "{:,.0f}",
                })
                .hide(axis="index"),
            use_container_width=True,
        )