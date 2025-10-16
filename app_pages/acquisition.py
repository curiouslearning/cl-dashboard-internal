import streamlit as st
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import users
from metrics import get_filtered_cohort,get_cohort_totals_by_metric
from settings import initialize,init_campaign_data
from users import ensure_user_data_initialized

initialize()
ensure_user_data_initialized()
init_campaign_data()

ensure_user_data_initialized()

ui.colorize_multiselect_options()

st.subheader("Learners Over Time")

col1, col2 = st.columns(2, gap="large")

with col1:
    countries_list = users.get_country_list()
    countries_list = ui.multi_select_all(
        countries_list,
        title="Country Selection",
        key="LA_LR_Time",
    )
    
    languages = users.get_language_list()
    language = ui.single_selector(
        languages, title="Select a language", key="a-2"
    )
    selected_date, option = ui.calendar_selector(key="fa-3", index=1)
    daterange = ui.convert_date_to_range(selected_date, option)

with col2:
    distinct_apps = ui.get_apps()
    app = ui.single_selector(distinct_apps, title="Select an App", key="a-10",include_All=False)

    display_category = st.radio(
        "Display by", ("Country", "Language"), index=0, horizontal=True, key="a-3"
    )


if (len(countries_list)) > 0 and (len(daterange) == 2):
    start = daterange[0].strftime("%b %d, %Y")
    end = daterange[1].strftime("%b %d, %Y")
    st.write("Timerange: " + start + " to " + end)
    
    user_cohort_df, user_cohort_df_LR = get_filtered_cohort(app, daterange, language, countries_list)
    
    is_cr = (app == ["CR"] or app == "CR")
    if is_cr:
        user_cohort_df = user_cohort_df_LR
    
    LR = get_cohort_totals_by_metric(user_cohort_df,stat="LR")

    st.metric(label="Total Learners Reached", value=prettify(int(LR)))
      
    uic.LR_LA_line_chart_over_time(
        user_cohort_df=user_cohort_df,display_category=display_category,aggregate=False
    )

    uic.LR_LA_line_chart_over_time(
        user_cohort_df=user_cohort_df,display_category=display_category,aggregate=True
    )

    csv = ui.convert_for_download(user_cohort_df)
    st.download_button(label="Download CSV",data=csv,file_name="LR_LA_line_chart_over_time.csv",key="a-13",icon=":material/download:",mime="text/csv")




