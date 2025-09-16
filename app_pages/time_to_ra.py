import streamlit as st
import ui_widgets as ui
from metrics import get_cr_cohorts,calculate_average_metric_per_user

from settings import initialize
initialize()
from users import ensure_user_data_initialized
ensure_user_data_initialized()

col1, col2, col3 = st.columns(3)

with col1:
    from users import get_country_list
    countries_list = get_country_list()
    country = ui.single_selector_new(
        countries_list,
        title="Country Selection",
        key="la-2",
    )
    
    distinct_apps = ui.get_apps()
    app = ui.single_selector_new(distinct_apps, title="Select an App", key="a-10",include_All=False)

    by_months = st.toggle("Show by Months", value=False)
    
with col2:
    selected_date, option = ui.calendar_selector_new(key="SF-1", index=0, title="Select user cohort by date")
    daterange = ui.convert_date_to_range(selected_date, option)

with col3:
    st.write("Language selection")

    from users import get_language_list
    df = get_language_list()
    selected_languages = ui.multi_select_all_new(
        df,  title="Select languages", key="fa-1"
    )   

if (len(selected_languages) > 0 and len(selected_languages) > 0):
    
    user_cohort_df, user_cohort_df_LR = get_cr_cohorts(app, daterange, selected_languages, countries_list)
    
    average_days_to_ra= calculate_average_metric_per_user(user_cohort_df,column_name="days_to_ra")
    col1.metric(label="Avg Days to RA", value=f"{average_days_to_ra:.2f}")
    
    start = daterange[0].strftime("%b %d, %Y")
    end = daterange[1].strftime("%b %d, %Y")
    st.write("Timerange: " + start + " to " + end)  
    
    from ui_components import days_to_ra_chart,ra_ecdf_curve,avg_days_to_ra_by_dim_chart,ra_histogram_curve
    
    df_ra = user_cohort_df[user_cohort_df['days_to_ra'].notnull()].copy()
    df_ra['months_to_ra'] = df_ra['days_to_ra'] / 30.44
    csv = ui.convert_for_download(df_ra)
    st.sidebar.download_button(label="Download",data=csv,file_name="RAUsers.csv",key="a-12",icon=":material/download:",mime="text/csv")
    
    days_to_ra_chart(df_ra,by_months)
    st.divider()
    avg_days_to_ra_by_dim_chart(df_ra,app)
    st.divider()
    ra_ecdf_curve(df_ra,by_months)
    st.divider()
    ra_histogram_curve(df_ra,by_months)


    
    