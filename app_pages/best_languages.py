import streamlit as st
from ui_components import funnel_chart
import ui_widgets as ui
from metrics import get_filtered_cohort
from settings import default_daterange,initialize
from users import ensure_user_data_initialized, get_country_list,get_language_list


initialize()
ensure_user_data_initialized()

ui.display_definitions_table("Definitions",ui.level_percent_definitions)

countries_list = get_country_list()
selected_languages = get_language_list()

col1,col2 = st.columns(2)

distinct_apps = ui.get_apps()
with col1:
    app = ui.single_selector(distinct_apps, title="Select an App", key="sf-10",include_All=False)
    sort_by = st.radio(label="Sort By: ", options=["Percent","Total"])      

user_cohort_df, user_cohort_df_LR = get_filtered_cohort(app=app, language=selected_languages, countries_list=countries_list,daterange=default_daterange)

options = ["LR","PC","LA","RA","GC"]
with col2:
    selected_option = st.radio(label="Select a stat:",options=options,index=0,horizontal=True)     
    acsending_flag = st.radio(label="Performance",options=["Best","Worst"],horizontal=True)
  
title = f"{acsending_flag} Performing Languages by {selected_option}"  

if acsending_flag == "Best":
    ascending = False
else:
    ascending = True

df_values = funnel_chart(chart_title=title,
    cohort_df=user_cohort_df,
    cohort_df_LR=user_cohort_df_LR,   # For CR, otherwise just pass None or omit
    groupby_col="app_language",
    app=app,
    stat=selected_option, 
    use_top_ten=True,
    ascending=ascending,
    min_funnel=True,chart_type="bar",
    sort_by=sort_by
)
csv = ui.convert_for_download(df_values)
st.download_button(label="Download",data=csv,file_name="funnel_line_chart_percent.csv",key="sf-12",icon=":material/download:",mime="text/csv")

