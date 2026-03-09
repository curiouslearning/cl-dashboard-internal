import streamlit as st
from ui_components import funnel_chart
import ui_widgets as ui
from metrics import get_filtered_users
from users import ensure_user_data_initialized, get_country_list, get_language_list, get_cohort_list
from settings import initialize

initialize()
ensure_user_data_initialized()

ui.display_definitions_table("Definitions", ui.level_percent_definitions)

countries_list = get_country_list()
distinct_apps = ui.get_apps()
distinct_cohorts = get_cohort_list()

col1, col2, col3 = st.columns(3)

with col1:
    country = ui.single_selector(countries_list, title="Country Selection", key="la-2")
    selected_date, option = ui.calendar_selector(key="SF-1", index=0, title="Select user cohort by date")
    daterange = ui.convert_date_to_range(selected_date, option)

with col2:
    filter_mode = st.radio("Filter by", ["App", "Cohort"], key="sf-filter-mode", horizontal=True)
    if filter_mode == "App":
        if "sf-cohort" in st.session_state:
            del st.session_state["sf-cohort"]
        app = ui.single_selector(distinct_apps, title="Select an App", key="sf-app", include_All=False, index=0)
        cohort = "All"
    else:
        if "sf-app" in st.session_state:
            del st.session_state["sf-app"]
        cohort = ui.single_selector(distinct_cohorts, title="Select a Cohort", key="sf-cohort", include_All=False, index=0)
        app = "All"

with col3:
    top_ten_flag = st.toggle(label="Use Top 10 LR Languages", value=True)
    if not top_ten_flag:
        selected_languages = ui.multi_select_all(get_language_list(), title="Select languages", key="fa-1")
    else:
        selected_languages = ["All"]  # skip language filtering, funnel_chart handles top 10

if len(selected_languages) > 0 and len(daterange) == 2:

    user_df, cr_df_LR = get_filtered_users(app, daterange, selected_languages, country, cohort=cohort)
    
    start = daterange[0].strftime("%b %d, %Y")
    end = daterange[1].strftime("%b %d, %Y")
    st.write("Timerange: " + start + " to " + end)

    df_values = funnel_chart(
        cohort_df=user_df,
        cr_df_LR=cr_df_LR,
        groupby_col="app_language",
        app=app,
        use_top_ten=top_ten_flag,
        min_funnel=False,
        chart_type="line"
    )
    csv = ui.convert_for_download(df_values)
    st.download_button(label="Download", data=csv, file_name="funnel_line_chart_percent.csv", key="sf-12", icon=":material/download:", mime="text/csv")

    df_download = funnel_chart(
        cohort_df=user_df,
        cr_df_LR=cr_df_LR,
        groupby_col="app_language",
        app=app,
        use_top_ten=top_ten_flag,
        min_funnel=False,
        chart_type="bar"
    )
    csv = ui.convert_for_download(df_download)
    st.download_button(label="Download", data=csv, file_name="funnel_bar_chart_percent.csv", key="sf-13", icon=":material/download:", mime="text/csv")