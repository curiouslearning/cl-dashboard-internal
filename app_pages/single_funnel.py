
import streamlit as st
from rich import print as rprint
from ui_components import create_engagement_funnel, show_dual_metric_tiles
import ui_widgets as ui
import metrics
from users import ensure_user_data_initialized, get_cohort_list, get_language_list, get_country_list
from settings import initialize

initialize()
ensure_user_data_initialized()

ui.display_definitions_table("Data Notes", ui.data_notes)

languages = get_language_list()
countries_list = get_country_list()

distinct_apps = ui.get_apps()
distinct_cohorts = get_cohort_list()

col1, col2 = st.columns(2)

with col1:
    language = ui.single_selector(
        languages,
        title="Select a language",
        key="s1",
        index=0,
    )

    countries_list = ui.multi_select_all(
        countries_list,
        title="Country Selection",
        key="s2",
    )

    filter_mode = st.radio(
        "Filter funnel by",
        ["App", "Cohort"],
        key="s_filter_mode",
        horizontal=True,
        help="Choose either App or Cohort. Only one can be active at a time.",
    )

    if filter_mode == "App":
        app = ui.single_selector(
            distinct_apps,
            title="Select an App",
            key="s4",
            include_All=False,
            index=0,
        )
        cohort = None
        st.caption("App filter is active. Cohort filter is not being applied.")

    else:
        cohort = ui.single_selector(
            distinct_cohorts,
            title="Select a cohort",
            key="s7",
            include_All=True,
            index=0,
        )
        app = "All"
        st.caption("Cohort filter is active. App filter is not being applied.")

with col2:
    selected_date, option = ui.calendar_selector(
        key="s3",
        title="Select a date range",
        index=0,
    )
    daterange = ui.convert_date_to_range(selected_date, option)

if len(countries_list) and len(daterange) == 2:
    # --- Cohort Dataframes ---
    user_cohort_df, user_cr_df_LR = metrics.get_filtered_users(
        app=app,
        daterange=daterange,
        language=language,
        countries_list=countries_list,
        cohort=cohort,
    )

    metrics_home = metrics.get_engagement_metrics(user_cohort_df)

    if app == "CR":
        funnel_size = "large"
    else:        
        funnel_size = "compact"

    # --- Output Section ---
    create_engagement_funnel(
        user_df=user_cohort_df,       # main progress cohort
        cr_df_LR=user_cr_df_LR, # app_launch cohort for LR only
        key_prefix="s5",
        funnel_size=funnel_size,
        app=app,
    )

    show_dual_metric_tiles("Metrics", home_metrics=metrics_home, size="small")

    csv = ui.convert_for_download(user_cohort_df)
    st.download_button(
        label="Download",
        data=csv,
        file_name="user_cohort_list.csv",
        key="s6",
        icon=":material/download:",
        mime="text/csv",
    )