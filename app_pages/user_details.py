import streamlit as st
from rich import print as rprint
from millify import prettify
import pandas as pd

import settings


settings.initialize()
settings.init_user_list()

def info_row(label, value, color="green"):
    st.markdown(f"<div style='margin-bottom: -10px'><span style='color:{color}; font-weight:500'>{label}</span> {value}</div>", unsafe_allow_html=True)

def safe_value(val, fallback="N/A"):
    return fallback if pd.isna(val) else val


col1, col2 = st.columns([2,4])
with col1:
    cr_user_id = st.text_input(label="Enter cr_user_id",type="default")


if (len(cr_user_id) > 0):
    df_cr_users = st.session_state.df_cr_users
    df_cr_app_launch = st.session_state.df_cr_app_launch
    df_cr_engagement = st.session_state.df_cr_engagement
    df_filtered = df_cr_app_launch[df_cr_app_launch['first_open'] >= pd.to_datetime('2025-01-01')]
    df_filtered.to_csv("df_filtered.csv")

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
        st.warning("No CR data found for this cr_user_id.")

    # CR Users / FTM
    user = df_cr_users.loc[df_cr_users['cr_user_id'] == cr_user_id]
    if not user.empty:
        info_row("FTM First Open:", safe_value(user["first_open"].iloc[0]))
        info_row("FTM Furthest Event:", safe_value(user["furthest_event"].iloc[0]))
        info_row("FTM Level:", safe_value(user["max_user_level"].iloc[0]))    
        info_row("Learner Acquired Date :", safe_value(user["la_date"].iloc[0]))
    else:
        st.warning("No FTM data found for this cr_user_id.")

    # CR Engagement
    user = df_cr_engagement.loc[df_cr_engagement['user_pseudo_id'] == user_pseudo_id]
    if not user.empty:
        info_row("Engagement Events:", safe_value(user["engagement_event_count"].iloc[0]))
        seconds = safe_value(user["total_time_seconds"].iloc[0])
        minutes = (seconds / 60).round(2)
        info_row("Total Time (m):", minutes)

    else:
        st.warning("No engagement data found for this cr_user_id.")



    



    