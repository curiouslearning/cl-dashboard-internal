import streamlit as st
from rich import print as rprint
from millify import prettify
from  ui_components import create_funnels
import ui_widgets as ui
from ui_components import show_dual_metric_table
from metrics import get_user_cohort_list,get_metrics_for_cohort


from settings import initialize,init_cr_app_version_list
initialize()
init_cr_app_version_list()

from users import ensure_user_data_initialized,get_language_list,get_country_list
ensure_user_data_initialized()

ui.display_definitions_table("Data Notes",ui.data_notes)

languages = get_language_list()
countries_list = get_country_list()

distinct_apps = ui.get_apps()

col1, col2, col3 = st.columns(3)

with col1:
    languageA = ui.single_selector(languages, placement="col", title="Select a language", key="cf-2",index=20)
    countries_listA = ui.multi_select_all(countries_list, title="Country Selection", key="cf-3", placement="middle")
    selected_date, option = ui.calendar_selector(placement="col", key="crf-4", title="Select date user cohort", index=4,preset_index=4)
    daterangeA = ui.convert_date_to_range(selected_date, option)
    appA = ui.single_selector(distinct_apps, placement="col", title="Select an App", key="cf-5",include_All=False,index=1)

    if appA[0] == "Unity":
        user_idA = "user_pseudo_id"
    else:
        user_idA = "cr_user_id"

with col2:
    languageB = ui.single_selector(languages, placement="col", title="Select a language", key="cf-7",index=20)
    countries_listB = ui.multi_select_all(countries_list, title="Country Selection", key="cf-8", placement="middle")
    selected_date, option = ui.calendar_selector(placement="col", key="crf-9", title="Select date user cohort", index=4,preset_index=4)
    daterangeB = ui.convert_date_to_range(selected_date, option)
    appB = ui.single_selector(distinct_apps, placement="col", title="Select an App", key="cf-10",include_All=False,index=0)
    if appB[0] == "Unity":
        user_idB = "user_pseudo_id"
    else:
        user_idB = "cr_user_id"
        
with col3:
    languageC = ui.single_selector(languages, placement="col", title="Select a language", key="cf-20")
    countries_listC = ui.multi_select_all(countries_list, title="Country Selection", key="cf-21", placement="middle")
    selected_date, option = ui.calendar_selector(placement="col", key="cf-22", title="Select date user cohort", index=4,preset_index=4)
    daterangeC = ui.convert_date_to_range(selected_date, option)
    appC = ui.single_selector(distinct_apps, placement="col", title="Select an App", key="cf-23",include_All=False,index=5)
    if appC[0] == "Unity":
        user_idC = "user_pseudo_id"
    else:
        user_idC = "cr_user_id"

if len(countries_listA) and len(countries_listB)  and len(countries_listC) and len(daterangeA) == 2  and len(daterangeB) == 2 and  len(daterangeC) == 2:

    # Cohort A
    user_cohort_listA = get_user_cohort_list(
        daterange=daterangeA,
        languages=languageA,
        countries_list=countries_listA,
        app=appA,
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
        as_list=False,

    )
    user_listB = user_cohort_listB[user_idB]
    metrics_home_B = get_metrics_for_cohort(user_listB,appB)

    # Cohort C
    user_cohort_listC = get_user_cohort_list(
        daterange=daterangeC,
        languages=languageC,
        countries_list=countries_listC,
        app=appC,
        as_list=False,

    )
    user_listC = user_cohort_listC[user_idC]
    metrics_home_C = get_metrics_for_cohort(user_listC,appC)
    if (
        any(app == "Unity" or "standalone" in app.lower() for app in appA if app)
        or any(app == "Unity" or "standalone" in app.lower() for app in appB if app)
        or any(app == "Unity" or "standalone" in app.lower() for app in appC if app)    ):
        funnel_size = "compact"
    else:
        funnel_size = "medium"

    # --- Output Section ---
    with col1:
        show_dual_metric_table("Cohort A", metrics_home_A)
        create_funnels(
            daterange=daterangeA,
            countries_list=countries_listA,
            languages=languageA,
            key_prefix="cf-11",
            app=appA,
            funnel_size=funnel_size,
            user_list=user_listA,

        )
        csvA = ui.convert_for_download(user_cohort_listA)
        st.download_button(
            label="Download Cohort A CSV",
            data=csvA,
            file_name="user_cohort_listA.csv",
            key="cf-12",
            icon=":material/download:",
            mime="text/csv",
        )

    with col2:
        show_dual_metric_table("Cohort B", metrics_home_B)
        create_funnels(
            daterange=daterangeB,
            countries_list=countries_listB,
            languages=languageB,
            key_prefix="cf-13",
            funnel_size=funnel_size,
            app=appB,
            user_list=user_listB,

        )
        csvB = ui.convert_for_download(user_cohort_listB)
        
        st.download_button(
            label="Download Cohort B CSV",
            data=csvB,
            file_name="user_cohort_listB.csv",
            key="cf-14",
            icon=":material/download:",
            mime="text/csv",
        )
        
    with col3:
        show_dual_metric_table("Cohort C", metrics_home_C)
        create_funnels(
            daterange=daterangeC,
            countries_list=countries_listC,
            languages=languageC,
            key_prefix="cf-24",
            funnel_size=funnel_size,
            app=appC,
            user_list=user_listC,

        )
        csvC = ui.convert_for_download(user_cohort_listC)
        
        st.download_button(
            label="Download Cohort C CSV",
            data=csvC,
            file_name="user_cohort_listC.csv",
            key="cf-25",
            icon=":material/download:",
            mime="text/csv",
        )
