import streamlit as st
from rich import print as rprint
from millify import prettify
from  ui_components import create_funnels
import ui_widgets as ui
from metrics import get_user_cohort_list,get_metrics_for_cohort,show_dual_metric_table


from settings import initialize,init_cr_app_version_list
initialize()
init_cr_app_version_list()

from users import ensure_user_data_initialized,get_language_list,get_country_list
ensure_user_data_initialized()

ui.display_definitions_table("Data Notes",ui.data_notes)

languages = get_language_list()
countries_list = get_country_list()

col1, col2 = st.columns(2)

with col1:
    app_versionsA = ui.app_version_selector(placement="col", key="cf-1")
    languageA = ui.single_selector(languages, placement="col", title="Select a language", key="cf-2")
    countries_listA = ui.multi_select_all(countries_list, title="Country Selection", key="cf-7", placement="middle")
    selected_date, option = ui.calendar_selector(placement="col", key="crf-4", title="Select date user cohort")
    daterangeA = ui.convert_date_to_range(selected_date, option)
    appA = ui.app_selector(placement="middle",key="cf-19")
    if appA == "Unity":
        user_idA = "user_pseudo_id"
    else:
        user_idA = "cr_user_id"

with col2:
    app_versionsB = ui.app_version_selector(placement="col", key="cf-5")
    languageB = ui.single_selector(languages, placement="col", title="Select a language", key="cf-6")
    countries_listB = ui.multi_select_all(countries_list, title="Country Selection", key="cf-8", placement="middle")
    selected_date, option = ui.calendar_selector(placement="col", key="crf-9", title="Select date user cohort")
    daterangeB = ui.convert_date_to_range(selected_date, option)
    appB = ui.app_selector(placement="middle",key="cf-20")
    if appB == "Unity":
        user_idB = "user_pseudo_id"
    else:
        user_idB = "cr_user_id"

# --- Logic and Output ---


if len(countries_listA) and len(countries_listB):

    # Cohort A
    user_cohort_listA = get_user_cohort_list(
        daterange=daterangeA,
        languages=languageA,
        countries_list=countries_listA,
        app=appA,
        cr_app_versions=app_versionsA,
        as_list=False,
        
    )
    user_listA = user_cohort_listA[user_idA]
    metrics_home_A = get_metrics_for_cohort(user_listA,appA)

    # Cohort B
    user_cohort_listB = get_user_cohort_list(
        daterange=daterangeB,
        languages=languageB,
        countries_list=countries_listB,
        app=appB,
        cr_app_versions=app_versionsB,
        as_list=False,

    )
    user_listB = user_cohort_listB[user_idB]

    metrics_home_B = get_metrics_for_cohort(user_listB,appB)

    if appA == "Unity" or appB == "Unity":
        funnel_size = "compact"
    elif "All" in app_versionsA and "All" in app_versionsB:
        funnel_size = "large"
    else:
        funnel_size = "medium"

    # --- Output Section ---
    with col1:
        show_dual_metric_table("Cohort A", metrics_home_A)
        create_funnels(
            daterange=daterangeA,
            countries_list=countries_listA,
            languages=languageA,
            key_prefix="cf-10",
            app=appA,
            funnel_size=funnel_size,
            user_list=user_listA,
            app_versions=app_versionsA,
        )
        csvA = ui.convert_for_download(user_cohort_listA)
        st.download_button(
            label="Download Cohort A CSV",
            data=csvA,
            file_name="user_cohort_listA.csv",
            key="cf-15",
            icon=":material/download:",
            mime="text/csv",
        )

    with col2:
        show_dual_metric_table("Cohort B", metrics_home_B)
        create_funnels(
            daterange=daterangeB,
            countries_list=countries_listB,
            languages=languageB,
            key_prefix="cf-20",
            funnel_size=funnel_size,
            app=appB,
            user_list=user_listB,
            app_versions=app_versionsB,
        )
        csvB = ui.convert_for_download(user_cohort_listB)
        
        st.download_button(
            label="Download Cohort B CSV",
            data=csvB,
            file_name="user_cohort_listB.csv",
            key="cf-25",
            icon=":material/download:",
            mime="text/csv",
        )
