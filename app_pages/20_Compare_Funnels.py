import streamlit as st
import settings
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import users
import metrics
import pandas as pd


settings.initialize()
settings.init_cr_app_version_list()
from users import ensure_user_data_initialized
ensure_user_data_initialized()

def get_metrics_for_cohort(user_cohort_list):

    return {
        "Avg Sessions/User": metrics.calculate_average_metric_per_user(user_cohort_list=user_cohort_list, app="CR",column_name="engagement_event_count"),
        "Avg Total Time/User (min)": metrics.calculate_average_metric_per_user(user_cohort_list=user_cohort_list,app="CR",column_name="total_time_minutes"),
    }

def show_dual_metric_table(title, home_metrics):

    df = pd.DataFrame({
        "Metric": list(home_metrics.keys()),
        "App Calculated": [f"{v:.2f}" for v in home_metrics.values()],

    })
    df.set_index("Metric", inplace=True)  # 👈 hides default numeric index
    st.markdown(f"### {title}")
    st.table(df)




languages = users.get_language_list()
countries_list = users.get_country_list()

col1, col2 = st.columns(2)

with col1:
    app_versionsA = ui.app_version_selector(placement="col", key="cf-1")
    languageA = ui.single_selector(languages, placement="col", title="Select a language", key="cf-2")
    countries_listA = ui.multi_select_all(countries_list, title="Country Selection", key="cf-7", placement="middle")
    selected_date, option = ui.calendar_selector(placement="col", key="crf-4", title="Select date user cohort")
    daterangeA = ui.convert_date_to_range(selected_date, option)
    offline_filterA = ui.offline_filter(key="A")

with col2:
    app_versionsB = ui.app_version_selector(placement="col", key="cf-5")
    languageB = ui.single_selector(languages, placement="col", title="Select a language", key="cf-6")
    countries_listB = ui.multi_select_all(countries_list, title="Country Selection", key="cf-8", placement="middle")
    selected_date, option = ui.calendar_selector(placement="col", key="crf-9", title="Select date user cohort")
    daterangeB = ui.convert_date_to_range(selected_date, option)
    offline_filterB = ui.offline_filter(key="B")


# --- Logic and Output ---

if len(countries_listA) and len(countries_listB):

    # Cohort A
    user_cohort_listA = metrics.get_user_cohort_list(
        daterange=daterangeA,
        languages=languageA,
        countries_list=countries_listA,
        app="CR",
        cr_app_versions=app_versionsA,
        as_list=False,
        offline_filter=offline_filterA
        
    )
    user_listA = user_cohort_listA["cr_user_id"]
    metrics_home_A = get_metrics_for_cohort(user_listA)

    # Cohort B
    user_cohort_listB = metrics.get_user_cohort_list(
        daterange=daterangeB,
        languages=languageB,
        countries_list=countries_listB,
        app="CR",
        cr_app_versions=app_versionsB,
        as_list=False,
        offline_filter=offline_filterB
    )
    user_listB = user_cohort_listB["cr_user_id"]
    metrics_home_B = get_metrics_for_cohort(user_listB)

    funnel_size = "large" if "All" in app_versionsA and "All" in app_versionsB else "medium"


    # --- Output Section ---
    with col1:
        show_dual_metric_table("Cohort A", metrics_home_A)
        uic.create_funnels(
            daterange=daterangeA,
            countries_list=countries_listA,
            languages=languageA,
            key_prefix="cf-10",
            app="CR",
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
        uic.create_funnels(
            daterange=daterangeB,
            countries_list=countries_listB,
            languages=languageB,
            key_prefix="cf-20",
            funnel_size=funnel_size,
            app="CR",
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
