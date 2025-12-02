
import streamlit as st
from users import get_cohort_user_ids,get_cohort_list, get_users_ftm_event_timeline,get_book_summary_for_cohort,get_books_for_user
from ui_components import ftm_timeline_plot,show_dual_metric_tiles,display_metrics_for_users
import pandas as pd
from metrics import get_engagement_metrics_for_cohort

from users import ensure_user_data_initialized
ensure_user_data_initialized()

col1,col2 = st.columns([1,2])
cohorts = get_cohort_list()
cohort = col1.selectbox("Select a cohort",cohorts)
cohort_ids = get_cohort_user_ids(cohort_name=cohort)

# 2. Load the event data for just those users
df = get_users_ftm_event_timeline(cohort_ids)

# 3. Usual filters/plot
if not pd.api.types.is_datetime64_any_dtype(df["event_timestamp"]):
    df["event_timestamp"] = pd.to_datetime(df["event_timestamp"], errors="coerce")

all_users = sorted(df["cr_user_id"].unique())
users = st.multiselect("Users", all_users, default=all_users)

events = st.multiselect(
    "Event types",
    sorted(df["event_name"].dropna().unique().tolist()),
    default=["puzzle_completed", "level_completed"]
)

subset = df[df["cr_user_id"].isin(users) & df["event_name"].isin(events)].copy()
subset = subset.sort_values(["cr_user_id", "event_timestamp"])
if subset.empty:
    st.error("Subset is empty after filters.")
    st.stop()

ftm_timeline_plot(subset)
df = st.session_state["df_cr_users"]

user_cohort_df = df[df["cr_user_id"].isin(users)].copy()
st.divider()
st.subheader("Individual metrics")
display_metrics_for_users(user_cohort_df)

st.divider()
metrics_home = get_engagement_metrics_for_cohort(user_cohort_df)
show_dual_metric_tiles("Metrics",home_metrics=metrics_home,size="small")

st.divider()
st.subheader("Book access summary for cohort users")

book_summary_df = get_book_summary_for_cohort(cohort_ids)

if book_summary_df.empty:
    st.info("No book interactions found for this cohort.")
else:
    st.dataframe(book_summary_df, use_container_width=True)

    # --- NEW: click-style flow to see books for a single user ---
    st.markdown("#### View books read by a single user")

    user_choices = book_summary_df["cr_user_id"].tolist()

    colA, colB = st.columns([2, 3])   # wider selectbox, narrow button

    with colA:
        selected_user = st.selectbox(
            "User", 
            user_choices,
            label_visibility="collapsed",   # hides label for ultra-clean UI
        )

    with colB:
        show_btn = st.button("Show")

    if show_btn and selected_user:
        user_books_df = get_books_for_user(selected_user)

        with st.expander(f"Books read by {selected_user}", expanded=True):
            st.dataframe(user_books_df, use_container_width=True)

