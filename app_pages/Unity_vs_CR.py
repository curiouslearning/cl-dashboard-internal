import streamlit as st
import settings
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import users
import metrics

settings.initialize()
settings.init_user_list()

ui.display_definitions_table("Data Notes",ui.data_notes)
countries_list = users.get_country_list()

ui.colorize_multiselect_options()


col1, col2, col3   = st.columns((1,1,1),gap="large")
col1.caption("Select a Date")
with col1:
    selected_date, option = ui.calendar_selector(placement="middle")
    daterange = ui.convert_date_to_range(selected_date, option)
with col2:
    languages = users.get_language_list()
    language = ui.single_selector(
        languages, placement="middle", title="Select a language", key="acq-1"
    )
with col3:
    countries_list = ui.multi_select_all(
    countries_list, title="Country Selection", key="acq-2",placement="middle"
    )

if len(daterange) == 2:
    start = daterange[0].strftime("%b %d, %Y")
    end = daterange[1].strftime("%b %d, %Y")
    st.write(start + " to " + end)

col1, col2  = st.columns((1,1),gap="large")
col1.markdown(
f"<strong><div style='text-align: center;'>Unity</div></strong>",
unsafe_allow_html=True,
)
col2.markdown(
f"<strong><div style='text-align: center;'>Curious Reader</div></strong>",
unsafe_allow_html=True,
)


if len(daterange) == 2 and len(countries_list) > 0:
    
    user_cohort_list_unity = metrics.get_user_cohort_list(daterange=daterange,languages=language,countries_list=countries_list,app="Unity")

    user_cohort_list_cr = metrics.get_user_cohort_list(daterange=daterange,languages=language,countries_list=countries_list,app="CR")

    average_number_sessions_unity = metrics.calculate_average_metric_per_user(user_cohort_list_unity,app="Unity",column_name="engagement_event_count")
    average_total_sessions_time_unity = metrics.calculate_average_metric_per_user(user_cohort_list_unity,app="Unity",column_name="total_time_minutes")
    average_session_length_unity = metrics.calculate_average_metric_per_user(user_cohort_list_unity,app="Unity",column_name="avg_session_length_minutes")
    average_number_sessions_cr = metrics.calculate_average_metric_per_user(user_cohort_list_cr,app="CR",column_name="engagement_event_count")
    average_total_sessions_time_cr = metrics.calculate_average_metric_per_user(user_cohort_list_cr,app="CR",column_name="total_time_minutes")
    average_session_length_cr = metrics.calculate_average_metric_per_user(user_cohort_list_cr,app="CR",column_name="avg_session_length_minutes")

    col1.metric(label="Avg # Sessions / User", value=f"{average_number_sessions_unity:.2f}")
    col1.metric(label="Avg Total Play Time / User", value=f"{average_total_sessions_time_unity:.2f} min")
    col1.metric(label="Avg Session Length / User", value=f"{average_session_length_unity:.2f} min")
    col2.metric(label="Avg # Sessions / User", value=f"{average_number_sessions_cr:.2f}")
    col2.metric(label="Avg Total Play Time / User", value=f"{average_total_sessions_time_cr:.2f} min")
    col2.metric(label="Avg Session Length / User", value=f"{average_session_length_cr:.2f} min")
 
    with col1:
        uic.create_funnels(countries_list=countries_list,daterange=daterange,app="Unity",key_prefix="u-1",languages=languages,user_list=user_cohort_list_unity)
    with col2:
        uic.create_funnels(countries_list=countries_list,daterange=daterange,app="CR",funnel_size="compact",key_prefix="u-2",languages=languages,user_list=user_cohort_list_cr)
 