import streamlit as st
from rich import print as rprint
from ui_components import show_dual_metric_table,create_funnels
import ui_widgets as ui
import users
import settings
from metrics import get_metrics_for_cohort,get_user_cohort_list


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
    user_cohort_list = get_user_cohort_list(daterange=daterange,languages=language,countries_list=countries_list,app=["CR"])
    
    metrics = get_metrics_for_cohort(user_cohort_list,app="CR")
    with col1:
        show_dual_metric_table("CR", metrics)

    create_funnels(countries_list=countries_list,daterange=daterange,key_prefix="dc-1",languages=languages,funnel_size="large",user_list=user_cohort_list)

