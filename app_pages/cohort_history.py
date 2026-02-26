import streamlit as st
import pandas as pd

from users import (
    ensure_user_data_initialized,
    get_cohort_list,
    get_cohort_user_ids,
    get_users_ftm_event_timeline,
    get_book_summary_for_cohort,
    get_books_for_user,
)
from ui_components import (
    ftm_timeline_plot,
    show_dual_metric_tiles,
    display_metrics_for_users,
)
from metrics import get_engagement_metrics_for_cohort

# ----------------------------
# Page-level styling
# ----------------------------
st.markdown(
    """
<style>
/* Pagination controls: make them stand out */
div[data-testid="stHorizontalBlock"] button[kind="primary"] {
  font-weight: 700 !important;
  border-radius: 10px !important;
  padding: 0.55rem 1rem !important;
}

/* Center label styling */
.pagination-center {
  text-align: center;
  padding-top: 6px;
  font-size: 16px;
  font-weight: 700;
}
.pagination-sub {
  font-size: 13px;
  color: rgba(49, 51, 63, 0.65);
  font-weight: 500;
}
</style>
""",
    unsafe_allow_html=True,
)

ensure_user_data_initialized()

# ----------------------------
# Small helpers
# ----------------------------
def _paginate(items, page: int, page_size: int):
    total = len(items)
    if total == 0:
        return [], 0
    total_pages = (total + page_size - 1) // page_size
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end], total_pages


def _coerce_ts(df: pd.DataFrame) -> pd.DataFrame:
    if not pd.api.types.is_datetime64_any_dtype(df["event_timestamp"]):
        df["event_timestamp"] = pd.to_datetime(df["event_timestamp"], errors="coerce")
    return df


# ----------------------------
# Controls
# ----------------------------
col1, col2 = st.columns([1, 2])

cohorts = get_cohort_list()
cohort = col1.selectbox("Select a cohort", cohorts)

cohort_ids = get_cohort_user_ids(cohort_name=cohort)

# Base user table for cohort user list + sorting
df_users_all = st.session_state["df_cr_users"].copy()
cohort_users_df = df_users_all[df_users_all["cr_user_id"].isin(cohort_ids)].copy()

search = col1.text_input("Search user (optional)", value="").strip().lower()

# If you know these columns exist, keep this explicit and simple.
sort_options = {
    "User ID (A→Z)": ("cr_user_id", True),
    "Max Level (high→low)": ("max_user_level", False),
    "Total Play Time (high→low)": ("total_play_time_min", False),
    "Active Span (high→low)": ("active_span_days", False),
    "Days to RA (low→high)": ("days_to_ra", True),
}
sort_label = col1.selectbox("Order users by", list(sort_options.keys()))
sort_col, asc = sort_options[sort_label]

# Fixed paging size (chart height constraint)
page_size = 20

# Page state (keyed by cohort so each cohort keeps its own position)
page_key = f"timeline_page::{cohort}"
if page_key not in st.session_state:
    st.session_state[page_key] = 1

# Apply search + sorting
if search:
    cohort_users_df = cohort_users_df[
        cohort_users_df["cr_user_id"].astype(str).str.lower().str.contains(search, na=False)
    ]

cohort_users_df = cohort_users_df.sort_values(sort_col, ascending=asc, na_position="last")

user_ids_ordered = cohort_users_df["cr_user_id"].astype(str).tolist()
page = st.session_state[page_key]
page_user_ids, total_pages = _paginate(user_ids_ordered, page, page_size)

if total_pages == 0:
    st.warning("No users match this cohort / filter.")
    st.stop()

# Clamp page if it ran past the end
if page > total_pages:
    st.session_state[page_key] = total_pages
    page = total_pages
    page_user_ids, total_pages = _paginate(user_ids_ordered, page, page_size)

# ----------------------------
# Event filters (page-scoped)
# ----------------------------
df_events = get_users_ftm_event_timeline(page_user_ids)
df_events = _coerce_ts(df_events)

events = col1.multiselect(
    "Event types",
    sorted(df_events["event_name"].dropna().unique().tolist()),
    default=["puzzle_completed", "level_completed"],
)

subset = df_events[df_events["event_name"].isin(events)].copy()
subset = subset.sort_values(["cr_user_id", "event_timestamp"])

if subset.empty:
    st.info("No events found for this page after filters.")
else:
    ftm_timeline_plot(subset)

# ----------------------------
# Pagination controls (below chart)
# ----------------------------
st.divider()

pcol1, pcol2, pcol3 = st.columns([1, 2, 1])

with pcol1:
    prev_disabled = (page <= 1)
    if st.button(
        "◀ Previous",
        disabled=prev_disabled,
        key=f"prev::{page_key}",
        type="primary",
    ):
        st.session_state[page_key] = page - 1
        st.rerun()

with pcol2:
    st.markdown(
        f"""
        <div class="pagination-center">
            Page {page} of {total_pages}<br>
            <span class="pagination-sub">
                Showing {len(page_user_ids)} of {len(user_ids_ordered)} users
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with pcol3:
    next_disabled = (page >= total_pages)
    if st.button(
        "Next ▶",
        disabled=next_disabled,
        key=f"next::{page_key}",
        type="primary",
    ):
        st.session_state[page_key] = page + 1
        st.rerun()

# ----------------------------
# Individual metrics (page-scoped)
# ----------------------------
st.divider()
st.subheader("Individual metrics (this page)")

user_page_df = df_users_all[df_users_all["cr_user_id"].isin(page_user_ids)].copy()
display_metrics_for_users(user_page_df)

st.divider()
metrics_home = get_engagement_metrics_for_cohort(user_page_df)
show_dual_metric_tiles("Metrics (this page)", home_metrics=metrics_home, size="small")

with st.expander("Full cohort metrics", expanded=False):
    metrics_all = get_engagement_metrics_for_cohort(cohort_users_df)
    show_dual_metric_tiles("Metrics (full cohort)", home_metrics=metrics_all, size="small")

# ----------------------------
# Book summary (page-scoped by default)
# ----------------------------
st.divider()
st.subheader("Book access summary")

scope = st.radio(
    "Scope",
    ["This page of users", "Full cohort"],
    horizontal=True,
)

book_user_ids = page_user_ids if scope == "This page of users" else cohort_ids
book_summary_df = get_book_summary_for_cohort(book_user_ids)

if book_summary_df.empty:
    st.info("No book interactions found for this selection.")
else:
    st.dataframe(book_summary_df, use_container_width=True)

    st.markdown("#### View books read by a single user")

    user_choices = book_summary_df["cr_user_id"].astype(str).tolist()

    colA, colB = st.columns([2, 3])
    with colA:
        selected_user = st.selectbox(
            "User",
            user_choices,
            label_visibility="collapsed",
        )
    with colB:
        show_btn = st.button("Show")

    if show_btn and selected_user:
        user_books_df = get_books_for_user(selected_user)
        with st.expander(f"Books read by {selected_user}", expanded=True):
            st.dataframe(user_books_df, use_container_width=True)