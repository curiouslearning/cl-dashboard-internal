import streamlit as st
import ui_widgets as ui
from metrics import get_filtered_users, calculate_average_metric_per_user
from users import ensure_user_data_initialized, get_country_list, get_language_list, get_cohort_list
from settings import initialize, default_daterange

initialize()
ensure_user_data_initialized()

countries_list = get_country_list()
distinct_apps = ui.get_apps()
distinct_cohorts = get_cohort_list()

col1, col2, col3 = st.columns(3)

with col1:
    country = ui.single_selector(countries_list, title="Country Selection", key="la-2")
    filter_mode = st.radio("Filter by", ["App", "Cohort"], key="ra-filter-mode", horizontal=True)
    if filter_mode == "App":
        if "ra-cohort" in st.session_state:
            del st.session_state["ra-cohort"]
        app = ui.single_selector(distinct_apps, title="Select an App", key="ra-app", include_All=False, index=0)
        cohort = None
    else:
        if "ra-app" in st.session_state:
            del st.session_state["ra-app"]
        cohort = ui.single_selector(distinct_cohorts, title="Select a Cohort", key="ra-cohort", include_All=False, index=0)
        app = "All"
    by_months = st.toggle("Show by Months", value=False)

with col2:
    selected_languages = ui.multi_select_all(get_language_list(), title="Select languages", key="fa-1")

if len(selected_languages) > 0:
    user_df, cr_df_LR = get_filtered_users(app=app, daterange=default_daterange, language=selected_languages, countries_list=country, cohort=cohort)

    average_days_to_ra = calculate_average_metric_per_user(user_df, column_name="days_to_ra")

    with col1:
        ui.metric_tile(
            label="Avg Days to RA",
            value=f"{average_days_to_ra:.2f}",
            color="#DCEAFB",
            size="small",
            width=200
        )

    from ui_components import days_to_ra_chart, ra_ecdf_curve, avg_days_to_ra_by_dim_chart, ra_histogram_curve

    df_ra = user_df[user_df['days_to_ra'].notnull()].copy()
    df_ra['months_to_ra'] = df_ra['days_to_ra'] / 30.44

    csv = ui.convert_for_download(df_ra)
    st.sidebar.download_button(label="Download", data=csv, file_name="RAUsers.csv", key="a-12", icon=":material/download:", mime="text/csv")

    if filter_mode == "App":
        days_to_ra_chart(df_ra, by_months)
        st.divider()
        avg_days_to_ra_by_dim_chart(df_ra, app)
        st.divider()
    ra_ecdf_curve(df_ra, by_months)
    st.divider()
    ra_histogram_curve(df_ra, by_months)
    
    csv = ui.convert_for_download(df_ra)
    st.download_button(
        label="Download",
        data=csv,
        file_name="df_ra.csv",
        key="s6",
        icon=":material/download:",
        mime="text/csv",
    )