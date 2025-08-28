import streamlit as st
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import users
import settings
import metrics


settings.initialize()
from users import ensure_user_data_initialized
ensure_user_data_initialized()

ui.display_definitions_table("Definitions",ui.level_percent_definitions)
ui.display_definitions_table("Data Notes",ui.data_notes)
col1, col2 = st.columns(2)


languages = users.get_language_list()
countries_list = users.get_country_list()


with col2:
    language = ui.single_selector(
    languages, placement="col", title="Select a language", key="crf-2"
)   
    countries_list = ui.multi_select_all(
        countries_list,
        title="Country Selection",
        key="LA_LR_Time",
        placement="middle",
    )

    selected_date, option = ui.calendar_selector(placement="middle", key="DC-1", index=0, title="Select user cohort by date")
    daterange = ui.convert_date_to_range(selected_date, option)


if len(countries_list) > 0  and (len(daterange) == 2):
    user_cohort_list = metrics.get_user_cohort_list(daterange=daterange,languages=language,countries_list=countries_list,app="CR")
    
    average_number_sessions_cl = metrics.calculate_average_metric_per_user(user_cohort_list,column_name="engagement_event_count",app="CR")
    average_total_sessions_time_cl = metrics.calculate_average_metric_per_user(user_cohort_list,column_name="total_time_minutes",app="CR")
    average_level_reached= metrics.calculate_average_metric_per_user(user_cohort_list,column_name="max_user_level",app="CR")
    average_days_to_ra= metrics.calculate_average_metric_per_user(user_cohort_list,column_name="days_to_ra",app="CR")

    col1.metric(label="Avg # Sessions / User", value=f"{average_number_sessions_cl:.2f}")
    col1.metric(label="Avg Total Session Time / User", value=f"{average_total_sessions_time_cl:.2f} min")
    col1.metric(label="Avg Level Reached", value=f"{average_level_reached:.2f}")
    col1.metric(label="Avg Time to RA", value=f"{average_days_to_ra:.2f}")

    uic.create_funnels(countries_list=countries_list,daterange=daterange,key_prefix="dc-1",languages=languages,funnel_size="large",user_list=user_cohort_list)

