
import streamlit as st
from users import get_cohort_user_ids,get_cohort_list, get_users_ftm_event_timeline
from ui_components import ftm_timeline_plot
import pandas as pd
from metrics import get_engagement_metrics_for_cohort

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

metrics_home = get_engagement_metrics_for_cohort(user_cohort_df)

