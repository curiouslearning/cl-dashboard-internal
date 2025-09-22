import streamlit as st
from ui_components import funnel_chart
import ui_widgets as ui
from metrics import get_filtered_cohort
from settings import default_daterange


from settings import initialize
initialize()
from users import ensure_user_data_initialized
ensure_user_data_initialized()

ui.display_definitions_table("Definitions",ui.level_percent_definitions)


from users import get_country_list,get_language_list
countries_list = get_country_list()

distinct_apps = ui.get_apps()
app = ui.single_selector_new(distinct_apps, title="Select an App", key="sf-10",include_All=False)
selected_languages = get_language_list()


user_cohort_df, user_cohort_df_LR = get_filtered_cohort(app=app, language=selected_languages, countries_list=countries_list,daterange=default_daterange)
        

with st.spinner("Calculating..."):
        df_values = funnel_chart(
            cohort_df=user_cohort_df,
            cohort_df_LR=user_cohort_df_LR,   # For CR, otherwise just pass None or omit
            groupby_col="app_language",
            app=app,                          # e.g. ["CR"], ["Unity"], ["standalone-hi"], etc.
            use_top_ten=True,
            min_funnel=False,chart_type="line"
        )
        csv = ui.convert_for_download(df_values)
        st.download_button(label="Download",data=csv,file_name="funnel_line_chart_percent.csv",key="sf-12",icon=":material/download:",mime="text/csv")

