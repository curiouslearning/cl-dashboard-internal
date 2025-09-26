import streamlit as st
from ui_components import funnel_chart
import ui_widgets as ui
from metrics import get_filtered_cohort


from settings import initialize
initialize()
from users import ensure_user_data_initialized
ensure_user_data_initialized()

ui.display_definitions_table("Definitions",ui.level_percent_definitions)

col1, col2, col3 = st.columns(3)

from users import get_country_list,get_language_list
countries_list = get_country_list()
with col1:
    country = ui.single_selector(
        countries_list,
        title="Country Selection",
        key="la-2",
    )
    distinct_apps = ui.get_apps()
    app = ui.single_selector(distinct_apps, title="Select an App", key="sf-10",include_All=False)

    
with col2:
    selected_date, option = ui.calendar_selector(key="SF-1", index=0, title="Select user cohort by date")
    daterange = ui.convert_date_to_range(selected_date, option)

with col3:
    selected_languages = get_language_list()
    st.write("Language selection")
    top_ten_flag = st.toggle(label="Use Top 10 LR Languages", value=True)
    if not top_ten_flag:
        from users import get_language_list
        df = get_language_list()
        selected_languages = ui.multi_select_all(
            df, title="Select languages", key="fa-1"
        )   

    if (len(selected_languages) > 0) and len(daterange) == 2:
        user_cohort_df, user_cohort_df_LR = get_filtered_cohort(app, daterange, selected_languages, countries_list)
        
        start = daterange[0].strftime("%b %d, %Y")
        end = daterange[1].strftime("%b %d, %Y")
        st.write("Timerange: " + start + " to " + end)  
        

if (len(selected_languages) > 0):   

    df_values = funnel_chart(
        cohort_df=user_cohort_df,
        cohort_df_LR=user_cohort_df_LR,   # For CR, otherwise just pass None or omit
        groupby_col="app_language",
        app=app,                          # e.g. ["CR"], ["Unity"], ["standalone-hi"], etc.
        use_top_ten=top_ten_flag,
        min_funnel=False,chart_type="line"
    )
    csv = ui.convert_for_download(df_values)
    st.download_button(label="Download",data=csv,file_name="funnel_line_chart_percent.csv",key="sf-12",icon=":material/download:",mime="text/csv")

    df_download = funnel_chart(
        cohort_df=user_cohort_df,
        cohort_df_LR=user_cohort_df_LR,   # For CR, otherwise just pass None or omit
        groupby_col="app_language",
        app=app,                          # e.g. ["CR"], ["Unity"], ["standalone-hi"], etc.
        use_top_ten=top_ten_flag,
        min_funnel=False,chart_type="bar"
    )

    csv = ui.convert_for_download(df_download)
    st.download_button(label="Download",data=csv,file_name="funnel_line_chart_percent.csv",key="sf-13",icon=":material/download:",mime="text/csv")

