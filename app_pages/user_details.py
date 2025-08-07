import streamlit as st
from rich import print as rprint
from millify import prettify
import pandas as pd

import settings

settings.initialize()
from users import ensure_user_data_initialized
ensure_user_data_initialized()

def info_row(label, value, color="green"):
    st.markdown(f"<div style='margin-bottom: -10px'><span style='color:{color}; font-weight:500'>{label}</span> {value}</div>", unsafe_allow_html=True)

def safe_value(val, fallback="N/A"):
    return fallback if pd.isna(val) else val
col1, col2 = st.columns([2,4])

#if the cr_user_id is passed in, retrieve from the query params
value = ""
if "cr_user_id" in st.query_params:
    value = st.query_params["cr_user_id"]
    
#use the default initial setting of "value" which will either be blank or passed in     
with col1:
    cr_user_id = st.text_input(label="Enter cr_user_id",type="default",value=value)


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
        info_row("CR Last Event Date:", safe_value(user["last_event_date"].iloc[0]))
        info_row("Calculated Engagement events:", safe_value(user["engagement_event_count"].iloc[0]))
        info_row("Calculated Engagement time:", safe_value(user["total_time_minutes"].iloc[0]))
        info_row("App version:", safe_value(user["app_version"].iloc[0]))
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


    st.markdown("---")  # Optional: visual separator

    if st.button("Run Full Event Query for this User"):
        with st.spinner("Running BigQuery..."):
            gcp_credentials, bq_client = settings.get_gcp_credentials()

            sql = f"""
                    SELECT
                    a.event_name,
                    a.event_date,
                    CAST(TIMESTAMP_MICROS(a.event_timestamp) AS DATETIME) AS event_timestamp,
                    a.user_pseudo_id,
                    a.device.language AS device_language,

                    -- Only include web_app_title if the event_name is app_launch
                    IF(a.event_name = 'app_launch', 
                        (SELECT p.value.string_value 
                        FROM UNNEST(a.event_params) AS p 
                        WHERE p.key = 'web_app_title'), 
                        NULL) AS web_app_title

                    FROM
                    `ftm-b9d99.analytics_159643920.events_*` AS a
                    WHERE
                    _TABLE_SUFFIX BETWEEN '20240101' AND FORMAT_DATE('%Y%m%d', CURRENT_DATE())
                    AND EXISTS (
                        SELECT 1
                        FROM UNNEST(a.event_params) AS p
                        WHERE p.key = 'cr_user_id' AND p.value.string_value = '{cr_user_id}'
                    )
                    ORDER BY
                    event_timestamp ASC
            """

            try:
                df_events = bq_client.query(sql).to_dataframe()
                if df_events.empty:
                    st.info("No events found for this user.")
                else:
                    st.success(f"Found {len(df_events)} events.")
                    st.dataframe(df_events)

                    # Optional: Add CSV download
                    csv = df_events.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download as CSV",
                        data=csv,
                        file_name=f"events_{cr_user_id}.csv",
                        mime="text/csv",
                    )

            except Exception as e:
                st.error(f"Error running query: {e}")

    



    