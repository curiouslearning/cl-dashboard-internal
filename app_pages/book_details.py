import streamlit as st

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
    "Stickiness is based on online sessions only. Offline reading is not captured. "
    "Bounced = opened 1 day only · Returned = 2 days · Hooked = 3+ days."
)

# -------------------------------------------------------
# Section 1: Stickiness distribution per book
# -------------------------------------------------------
st.divider()
st.header("Book stickiness")

df_popularity = bdh.build_book_popularity(df_filtered)

c1, c2 = st.columns(2)
with c1:
    min_readers = st.slider(
        "Minimum readers to show", 1, 100, 10, key="book-details-min-readers"
    )
with c2:
    sort_by = st.selectbox(
        "Sort by", ["Hooked", "Returned", "Bounced"], key="book-details-sort"
    )

fig_stickiness = bdh.build_stickiness_chart(
    df_popularity, min_readers=min_readers, sort_by=sort_by
)
st.plotly_chart(fig_stickiness, use_container_width=True)

st.caption(
    "Books with a high Hooked % are pulling readers back repeatedly. "
    "Books with a high Bounced % may have content or accessibility issues — "
    "though offline reading means some 'Bounced' users may have continued reading offline."
)

# -------------------------------------------------------
# Section 2: Per-book FTM outcomes
# -------------------------------------------------------
st.divider()
st.header("FTM outcomes by book (LA users)")

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
    st.dataframe(
        df_outcomes.style.format({
            "readers":           "{:,.0f}",
            "avg_level_readers": "{:.2f}",
            "avg_level_others":  "{:.2f}",
            "lift_avg_level":    "{:+.2f}",
            "pct_ra_readers":    "{:.1%}",
            "pct_ra_others":     "{:.1%}",
            "lift_pct_ra":       "{:+.1%}",
        }),
        use_container_width=True,
    )
    st.caption(
        f"'Others' = all other {stickiness_filter} readers in the mapped universe who did not read this book. "
        "Positive lift means readers of this book show stronger FTM progression."
    )

# -------------------------------------------------------
# Section 3: Book drill-down
# -------------------------------------------------------
st.divider()
st.header("Book drill-down")

available_books = sorted(
    df_filtered["base_book_id"]
    .fillna(df_filtered["book_id"])
    .dropna()
    .unique()
    .tolist()
)

selected_book = st.selectbox(
    "Select a book", available_books, key="book-details-drilldown"
)

if selected_book:
    c1, c2 = st.columns(2)

    # --- Cross-tab: user tier × stickiness ---
    with c1:
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
            st.caption(
                "Rows = overall book engagement tier (user-level). "
                "Columns = stickiness for this specific book. "
                "A Tier 3 user who Bounced on this book chose not to return despite being an engaged reader overall."
            )

    # --- Level breakdown ---
    with c2:
        st.subheader("Readers by book level")
        df_levels = bdh.build_book_level_breakdown(
            df_filtered=df_filtered,
            base_book_id=selected_book,
        )
        if df_levels.empty:
            st.info("No level data for this book.")
        else:
            st.dataframe(
                df_levels.style.format({
                    "unique_readers":  "{:,.0f}",
                    "total_events":    "{:,.0f}",
                    "avg_active_days": "{:.2f}",
                    "n_bounced":       "{:,.0f}",
                    "n_returned":      "{:,.0f}",
                    "n_hooked":        "{:,.0f}",
                }),
                use_container_width=True,
            )
            st.caption(
                "Some books have multiple levels (Lv1, Lv2, ...). "
                "Higher levels typically have fewer readers — a sharp drop may indicate difficulty or disinterest."
            )
