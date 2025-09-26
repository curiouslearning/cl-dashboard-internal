import streamlit as st
from rich import print as rprint
from  ui_components import create_funnels_by_cohort,show_dual_metric_table
import ui_widgets as ui
from metrics import get_filtered_cohort,get_metrics_for_cohort
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
    languageA = ui.single_selector(languages, title="Select a language", key="cf-2",index=20)
    countries_listA = ui.multi_select_all(countries_list, title="Country Selection", key="cf-3")
    selected_date, option = ui.calendar_selector( key="crf-4", title="Select date user cohort", index=4,preset_index=4)
    daterangeA = ui.convert_date_to_range(selected_date, option)
    appA = ui.single_selector(distinct_apps,title="Select an App", key="cf-5",include_All=False,index=1)

with col2:
    languageB = ui.single_selector(languages,  title="Select a language", key="cf-7",index=20)
    countries_listB = ui.multi_select_all(countries_list, title="Country Selection", key="cf-8")
    selected_date, option = ui.calendar_selector(key="crf-9", title="Select date user cohort", index=4,preset_index=4)
    daterangeB = ui.convert_date_to_range(selected_date, option)
    appB = ui.single_selector(distinct_apps, title="Select an App", key="cf-10",include_All=False,index=0)
        
with col3:
    languageC = ui.single_selector(languages, title="Select a language", key="cf-20")
    countries_listC = ui.multi_select_all(countries_list, title="Country Selection", key="cf-21")
    selected_date, option = ui.calendar_selector( key="cf-22", title="Select date user cohort", index=4,preset_index=4)
    daterangeC = ui.convert_date_to_range(selected_date, option)
    appC = ui.single_selector(distinct_apps, title="Select an App", key="cf-23",include_All=False,index=5)

if (
    len(countries_listA) and len(countries_listB) and len(countries_listC)
    and len(daterangeA) == 2 and len(daterangeB) == 2 and len(daterangeC) == 2
):
    # --- Cohort Dataframes ---
    user_cohort_dfA, user_cohort_dfA_LR = get_filtered_cohort(appA, daterangeA, languageA, countries_listA)
    user_cohort_dfB, user_cohort_dfB_LR =  get_filtered_cohort(appB, daterangeB, languageB, countries_listB)
    user_cohort_dfC, user_cohort_dfC_LR =  get_filtered_cohort(appC, daterangeC, languageC, countries_listC)

    metrics_home_A = get_metrics_for_cohort(user_cohort_dfA)
    metrics_home_B = get_metrics_for_cohort(user_cohort_dfB)
    metrics_home_C = get_metrics_for_cohort(user_cohort_dfC)

    def is_compact(apps):
        # Handles string or list
        if isinstance(apps, list):
            return any((a == "Unity" or (isinstance(a, str) and "standalone" in a.lower())) for a in apps if a)
        else:
            a = apps
            return (a == "Unity" or (isinstance(a, str) and "standalone" in a.lower()))

    if is_compact(appA) or is_compact(appB) or is_compact(appC):
        funnel_size = "compact"
    else:
        funnel_size = "large"

    # --- Output Section ---
    with col1:
        create_funnels_by_cohort(
            cohort_df=user_cohort_dfA,         # main progress cohort
            cohort_df_LR=user_cohort_dfA_LR,   # app_launch cohort for LR only
            key_prefix="cf-11",
            funnel_size=funnel_size,
            app=appA
        )
        show_dual_metric_table("Cohort A", metrics_home_A)
        csvA = ui.convert_for_download(user_cohort_dfA)
        st.download_button(
            label="Download",
            data=csvA,
            file_name="user_cohort_listA.csv",
            key="cf-12",
            icon=":material/download:",
            mime="text/csv",
        )

    with col2:
        create_funnels_by_cohort(
            cohort_df=user_cohort_dfB,
            cohort_df_LR=user_cohort_dfB_LR,
            key_prefix="cf-12",
            funnel_size=funnel_size,
            app=appB
        )
        show_dual_metric_table("Cohort B", metrics_home_B)
        csvB = ui.convert_for_download(user_cohort_dfB)
        st.download_button(
            label="Download",
            data=csvB,
            file_name="user_cohort_listB.csv",
            key="cf-13",
            icon=":material/download:",
            mime="text/csv",
        )

    with col3:
        create_funnels_by_cohort(
            cohort_df=user_cohort_dfC,
            cohort_df_LR=user_cohort_dfC_LR,
            key_prefix="cf-14",
            funnel_size=funnel_size,
            app=appC 
            )
        
        show_dual_metric_table("Cohort C", metrics_home_C)
        csvC = ui.convert_for_download(user_cohort_dfC)
        st.download_button(
            label="Download",
            data=csvC,
            file_name="user_cohort_listC.csv",
            key="cf-15",
            icon=":material/download:",
            mime="text/csv",
        )
