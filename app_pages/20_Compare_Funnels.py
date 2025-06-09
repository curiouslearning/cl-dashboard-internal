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
settings.init_cr_app_version_list()


ui.display_definitions_table("Data Notes",ui.data_notes)

st.subheader("Curious Reader Funnel Comparison")
languages = users.get_language_list()
countries_list = users.get_country_list()

col1, col2 = st.columns(2)
with col1:
    app_versionsA = ui.app_version_selector(placement="col", key="cf-1")

    languageA = ui.single_selector(
        languages, placement="col", title="Select a language", key="cf-2"
    )   
    countries_listA = ui.multi_select_all(
        countries_list,
        title="Country Selection",
        key="cf-7",
        placement="middle",
    )
    selected_date, option = ui.calendar_selector(placement="col", key="crf-4",title="Select date user cohort")
    daterangeA = ui.convert_date_to_range(selected_date, option)

    
with col2:  
    app_versionsB = ui.app_version_selector(placement="col", key="cf-5")

    languageB = ui.single_selector(
        languages, placement="col", title="Select a language", key="cf-6"
    )  
    countries_listB = ui.multi_select_all(
        countries_list,
        title="Country Selection",
        key="cf-8",
        placement="middle",
    ) 
    selected_date, option = ui.calendar_selector(placement="col", key="crf-9",title="Select date user cohort")
    daterangeB = ui.convert_date_to_range(selected_date, option)
 

if len(countries_listA) and  len(countries_listB ) > 0:
    
    user_cohort_listA = metrics.get_user_cohort_list(daterange=daterangeA,languages=languageA,countries_list=countries_listA,app="CR",cr_app_versions=app_versionsA,as_list=False)
    average_total_sessions_timeA = metrics.calculate_average_metric_per_user(user_cohort_listA["cr_user_id"],column_name="total_time_minutes")
    average_number_sessionsA = metrics.calculate_average_metric_per_user(user_cohort_listA["cr_user_id"],column_name="engagement_event_count")

    user_cohort_listB = metrics.get_user_cohort_list(daterange=daterangeB,languages=languageB,countries_list=countries_listB,app="CR",cr_app_versions=app_versionsB,as_list=False)
    average_total_sessions_timeB = metrics.calculate_average_metric_per_user(user_cohort_listB["cr_user_id"],column_name="total_time_minutes")
    average_number_sessionsB = metrics.calculate_average_metric_per_user(user_cohort_listB["cr_user_id"],column_name="engagement_event_count")


    displayLR = True
    if 'All' not in app_versionsA or 'All' not in app_versionsB:
        displayLR = False
    with col1:
        st.metric(label="Average Number Sessions per User", value=f"{average_number_sessionsA:.2f}")
        st.metric(label="Average Total Session Time per User", value=f"{average_total_sessions_timeA:.2f} min")
        uic.create_funnels(daterange=daterangeA,countries_list=countries_listA,languages=languageA,key_prefix="cf-10",displayLR=displayLR,user_list=user_cohort_listA["cr_user_id"],app_versions=app_versionsA)
        csvA = ui.convert_for_download(user_cohort_listA)
        st.download_button(label="Download CSV",data=csvA,file_name="user_cohort_listA.csv",key="cf-15",icon=":material/download:",mime="text/csv")

 
    with col2:  
        st.metric(label="Average Number Sessions per User", value=f"{average_number_sessionsB:.2f}")
        st.metric(label="Average Total Session Time per User", value=f"{average_total_sessions_timeB:.2f} min")
        uic.create_funnels(daterange=daterangeB,countries_list=countries_listB,languages=languageB,key_prefix="cf-11",displayLR=displayLR,user_list=user_cohort_listB["cr_user_id"],app_versions=app_versionsB)
        csvB = ui.convert_for_download(user_cohort_listB)
        st.download_button(label="Download CSV",data=csvB,file_name="user_cohort_listB.csv",key="cf-20",icon=":material/download:",mime="text/csv")

