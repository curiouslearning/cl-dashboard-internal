import streamlit as st
import ui_widgets as ui

from settings import initialize
initialize()
from users import ensure_user_data_initialized
ensure_user_data_initialized()

col1, col2, col3 = st.columns(3)

with col1:
    from users import get_country_list
    countries_list = get_country_list()
    country = ui.single_selector(
        countries_list,
        placement="middle",
        title="Country Selection",
        key="la-2",
    )
    
    app = ui.app_selector(placement="middle")
    by_months = st.toggle("Show by Months", value=False)
    
with col2:
    selected_date, option = ui.calendar_selector(placement="middle", key="SF-1", index=0, title="Select user cohort by date")
    daterange = ui.convert_date_to_range(selected_date, option)

with col3:
    st.write("Language selection")

    from users import get_language_list
    df = get_language_list()
    selected_languages = ui.multi_select_all(
        df, placement="middle", title="Select languages", key="fa-1"
    )   

if (len(selected_languages) > 0 and len(selected_languages) > 0):
    from metrics import get_user_cohort_list     
    user_cohort_list = get_user_cohort_list(daterange=daterange,languages=selected_languages,countries_list=countries_list,app=app)
    
    from metrics import calculate_average_metric_per_user
    average_days_to_ra= calculate_average_metric_per_user(user_cohort_list,column_name="days_to_ra",app=app)

    col1.metric(label="Avg Days to RA", value=f"{average_days_to_ra:.2f}")

    
    start = daterange[0].strftime("%b %d, %Y")
    end = daterange[1].strftime("%b %d, %Y")
    st.write("Timerange: " + start + " to " + end)  
    
    from ui_components import days_to_ra_chart,ra_ecdf_curve,avg_days_to_ra_by_dim_chart,ra_histogram_curve
    
    from metrics import filter_user_data
    df = filter_user_data(countries_list=countries_list,stat="RA",app=app,language=selected_languages,user_list=user_cohort_list)

    days_to_ra_chart(df,by_months)
    st.divider()
    avg_days_to_ra_by_dim_chart(df,app)
    st.divider()
    ra_ecdf_curve(df,by_months)
    st.divider()
    ra_histogram_curve(df,by_months)


    
    