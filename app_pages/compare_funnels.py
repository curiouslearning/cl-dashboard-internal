import streamlit as st
from ui_components import create_engagement_funnel, show_dual_metric_tiles
import ui_widgets as ui
from metrics import get_filtered_users, get_engagement_metrics
from users import ensure_user_data_initialized, get_language_list, get_country_list, get_cohort_list
from settings import initialize

initialize()
ensure_user_data_initialized()

ui.display_definitions_table("Data Notes", ui.data_notes)

languages = get_language_list()
countries_list = get_country_list()
distinct_apps = ui.get_apps()
distinct_cohorts = get_cohort_list()

col1, col2, col3 = st.columns(3)

with col1:
    languageA = ui.single_selector(languages, title="Select a language", key="cf-2", index=0)
    countries_listA = ui.multi_select_all(countries_list, title="Country Selection", key="cf-3")
    with st.expander("📅 Date Range", expanded=False):
        selected_date, option = ui.calendar_selector(key="crf-4", title="Select date user cohort", index=0, preset_index=4)
        daterangeA = ui.convert_date_to_range(selected_date, option)
    st.caption(f"📅 {daterangeA[0]} → {daterangeA[1]}" if len(daterangeA) == 2 else "No date selected")
    filter_modeA = st.radio("Filter by", ["App", "Cohort"], key="cf-mode-A", horizontal=True)

    if filter_modeA == "App":
        if "cf-cohort-A" in st.session_state:
            del st.session_state["cf-cohort-A"]
        appA = ui.single_selector(distinct_apps, title="Select an App", key="cf-app-A", include_All=False, index=1)
        cohortA = "All"
    else:
        if "cf-app-A" in st.session_state:
            del st.session_state["cf-app-A"]
        cohortA = ui.single_selector(distinct_cohorts, title="Select a Cohort", key="cf-cohort-A", include_All=False, index=0)
        appA = "All"

with col2:
    languageB = ui.single_selector(languages, title="Select a language", key="cf-7", index=0)
    countries_listB = ui.multi_select_all(countries_list, title="Country Selection", key="cf-8")
    with st.expander("📅 Date Range", expanded=False):
        selected_date, option = ui.calendar_selector(key="crf-9", title="Select date user cohort", index=0, preset_index=4)
        daterangeB = ui.convert_date_to_range(selected_date, option)
    st.caption(f"📅 {daterangeB[0]} → {daterangeB[1]}" if len(daterangeB) == 2 else "No date selected")
    filter_modeB = st.radio("Filter by", ["App", "Cohort"], key="cf-mode-B", horizontal=True)

    if filter_modeB == "App":
        if "cf-cohort-B" in st.session_state:
            del st.session_state["cf-cohort-B"]
        appB = ui.single_selector(distinct_apps, title="Select an App", key="cf-app-B", include_All=False, index=0)
        cohortB = "All"
    else:
        if "cf-app-B" in st.session_state:
            del st.session_state["cf-app-B"]
        cohortB = ui.single_selector(distinct_cohorts, title="Select a Cohort", key="cf-cohort-B", include_All=False, index=0)
        appB = "All"

with col3:
    languageC = ui.single_selector(languages, title="Select a language", key="cf-20")
    countries_listC = ui.multi_select_all(countries_list, title="Country Selection", key="cf-21")
    with st.expander("📅 Date Range", expanded=False):
        selected_date, option = ui.calendar_selector(key="cf-22", title="Select date user cohort", index=0, preset_index=4)
        daterangeC = ui.convert_date_to_range(selected_date, option)
    st.caption(f"📅 {daterangeC[0]} → {daterangeC[1]}" if len(daterangeC) == 2 else "No date selected")
    filter_modeC = st.radio("Filter by", ["App", "Cohort"], key="cf-mode-C", horizontal=True, index=1)
    
    if filter_modeC == "App":
        if "cf-cohort-C" in st.session_state:
            del st.session_state["cf-cohort-C"]
        appC = ui.single_selector(distinct_apps, title="Select an App", key="cf-app-C", include_All=False, index=0)
        cohortC = "All"
    else:
        if "cf-app-C" in st.session_state:
            del st.session_state["cf-app-C"]
        cohortC = ui.single_selector(distinct_cohorts, title="Select a Cohort", key="cf-cohort-C", include_All=False, index=0)
        appC = "All"

if (
    len(countries_listA) and len(countries_listB) and len(countries_listC)
    and len(daterangeA) == 2 and len(daterangeB) == 2 and len(daterangeC) == 2
):
    user_dfA, cr_df_LR_A = get_filtered_users(appA, daterangeA, languageA, countries_listA, cohort=cohortA)
    user_dfB, cr_df_LR_B = get_filtered_users(appB, daterangeB, languageB, countries_listB, cohort=cohortB)
    user_dfC, cr_df_LR_C = get_filtered_users(appC, daterangeC, languageC, countries_listC, cohort=cohortC)

    metrics_A = get_engagement_metrics(user_dfA)
    metrics_B = get_engagement_metrics(user_dfB)
    metrics_C = get_engagement_metrics(user_dfC)
    
    labelA = cohortA[0] if filter_modeA == "Cohort" else appA[0]
    labelB = cohortB[0] if filter_modeB == "Cohort" else appB[0]
    labelC = cohortC[0] if filter_modeC == "Cohort" else appC[0]

    funnel_size = "compact" if any(app == "Unity" for app in [appA, appB, appC]) else "large"

    with col1:
        create_engagement_funnel(user_df=user_dfA, cr_df_LR=cr_df_LR_A, key_prefix="cf-11", funnel_size=funnel_size, app=appA)
        show_dual_metric_tiles(labelA, home_metrics=metrics_A, size="small")
        csvA = ui.convert_for_download(user_dfA)
        st.download_button(label="Download", data=csvA, file_name="user_cohort_listA.csv", key="cf-12", icon=":material/download:", mime="text/csv")

    with col2:
        create_engagement_funnel(user_df=user_dfB, cr_df_LR=cr_df_LR_B, key_prefix="cf-13", funnel_size=funnel_size, app=appB)
        show_dual_metric_tiles(labelB, home_metrics=metrics_B, size="small")
        csvB = ui.convert_for_download(user_dfB)
        st.download_button(label="Download", data=csvB, file_name="user_cohort_listB.csv", key="cf-14", icon=":material/download:", mime="text/csv")

    with col3:
        create_engagement_funnel(user_df=user_dfC, cr_df_LR=cr_df_LR_C, key_prefix="cf-15", funnel_size=funnel_size, app=appC)
        show_dual_metric_tiles(labelC, home_metrics=metrics_C, size="small")
        csvC = ui.convert_for_download(user_dfC)
        st.download_button(label="Download", data=csvC, file_name="user_cohort_listC.csv", key="cf-16", icon=":material/download:", mime="text/csv")