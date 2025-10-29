import streamlit as st
from rich import print as rprint
from millify import prettify
import pandas as pd
from users import ensure_user_data_initialized
from settings import initialize
from ui_components import ftm_timeline_plot
from users import get_ftm_user_events,get_users_ftm_event_timeline
from ui_widgets import highlight_success

initialize()
ensure_user_data_initialized()

def info_row(label, value, color="green"):
    st.markdown(f"<div style='margin-bottom: -10px'><span style='color:{color}; font-weight:500'>{label}</span> {value}</div>", unsafe_allow_html=True)

def safe_value(val, fallback="N/A"):
    return fallback if pd.isna(val) else val
col1, col2 = st.columns([2,4])

# --- Sync at the very top: ---
if "cr_user_id" not in st.session_state:
    st.session_state.cr_user_id = ""

# Priority: query param > session state (but must update BEFORE text_input)
if "cr_user_id" in st.query_params and st.query_params["cr_user_id"]:
    if st.session_state.cr_user_id != st.query_params["cr_user_id"]:
        st.session_state.cr_user_id = st.query_params["cr_user_id"]

with col1:
    cr_user_id = st.text_input(
        "Enter cr_user_id",
        value=st.session_state.cr_user_id,
        type="default",
        key="cr_user_id"
    )

# DO NOT set st.session_state.cr_user_id after this point!
# Always use the value of st.session_state.cr_user_id (or cr_user_id, they're in sync)

# Optionally, update the query param for shareability:
if st.session_state.cr_user_id:
    st.query_params["cr_user_id"] = st.session_state.cr_user_id
elif "cr_user_id" in st.query_params:
    del st.query_params["cr_user_id"]

if (len(cr_user_id) > 0):
    df_cr_users = st.session_state.df_cr_users
    df_cr_app_launch = st.session_state.df_cr_app_launch

    df_cr_app_launch["first_open"] = pd.to_datetime(df_cr_app_launch["first_open"])
    df_filtered = df_cr_app_launch[df_cr_app_launch['first_open'] >= pd.to_datetime('2025-01-01')]
    
    user = df_cr_app_launch.loc[df_cr_app_launch['cr_user_id'] == cr_user_id]
    user_pseudo_id = None

    # CR App Launch
    user = df_cr_app_launch.loc[df_cr_app_launch['cr_user_id'] == cr_user_id]
    if not user.empty:
        #the engagement table doesn't have cr_user_id so have to cross reference with user_pseudo_id
        user_pseudo_id = user["user_pseudo_id"].iloc[0]
        info_row("CR user_pseudo_id:", safe_value(user_pseudo_id))
        info_row("Country:", safe_value(user["country"].iloc[0]))
        info_row("Language:", safe_value(user["app_language"].iloc[0]))
        info_row("CR First Open:", safe_value(user["first_open"].iloc[0]))
    else:
        st.warning("No CR App Launch data found for this cr_user_id.")

    # CR Users / FTM
    user = df_cr_users.loc[df_cr_users['cr_user_id'] == cr_user_id]
    if not user.empty:
        info_row("FTM First Open:", safe_value(user["first_open"].iloc[0]))
        info_row("FTM Furthest Event:", safe_value(user["furthest_event"].iloc[0]))
        info_row("FTM Level:", safe_value(user["max_user_level"].iloc[0]))    
        info_row("Learner Acquired Date :", safe_value(user["la_date"].iloc[0]))
        info_row("CR Last Event Date:", safe_value(user["last_event_date"].iloc[0]))
        info_row("Calculated Engagement events:", safe_value(user["engagement_event_count"].iloc[0]))
        info_row("Calculated Engagement time:", safe_value(user["total_time_minutes"].iloc[0]))

    else:
        st.warning("No FTM data found for this cr_user_id.")

    st.markdown("---")  # Optional: visual separator
    
    # Timeline section (assumes get_gcp_credentials returns a BQ client)
    cr_user_id_list = [cr_user_id]
    user_ftm_df = get_users_ftm_event_timeline(cr_user_id_list)
    st.markdown("#### FTM Progress Timeline")
    ftm_timeline_plot(user_ftm_df)

    st.markdown("---")  # Optional: visual separator


    df_user_events = get_ftm_user_events(cr_user_id)
    st.markdown("#### FTM Session & Game Event Timeline")
    # Only works in st.dataframe (not st.table)

    styled_df = df_user_events.style.apply(highlight_success, axis=1)
    st.dataframe(styled_df, use_container_width=True)
