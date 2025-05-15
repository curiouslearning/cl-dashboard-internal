import streamlit as st
import settings
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import users
import metrics


settings.initialize()
settings.init_user_list()

ui.display_definitions_table("Definitions",ui.level_percent_definitions)

st.markdown(
    """
    :green-background[NOTE:]
    :green[This chart lets you compare one specific level across the languages selected.
    It compares the selected level % drop from the selected upper level.]
    """
)
col1, col2 = st.columns(2)


countries_list = users.get_country_list()
with col2:
    country = ui.single_selector(
        countries_list,
        placement="middle",
        title="Country Selection",
        key="la-2",
    )

with col2:
    selected_date, option = ui.calendar_selector(placement="middle", key="fa-3", index=4)
    daterange = ui.convert_date_to_range(selected_date, option)
    
df_languages = metrics.get_counts(
    type="app_language",
    daterange=daterange,
    app="CR",
    language=["All"],
)
df_top10 = (
    df_languages[["app_language", "LR"]].sort_values(by="LR", ascending=False).head(6)
)

with col1:
    upper_level, bottom_level = ui.level_comparison_selector(placement="middle")
    if st.toggle(label="Use Top 6 LR Languages for Date Range", value=True):
        selected_languages = df_top10["app_language"].to_list()
    else:
        df = users.get_language_list()
        selected_languages = ui.multi_select_all(
            df, placement="middle", title="Select languages", key="fa-1"
        )
if len(selected_languages) == 0 or len(selected_languages) > 40:
    st.markdown(
        """
    :red[Please select one or more languages.  "All" is not an acceptable selection for this chart.]
    """
    )
else:
    if len(daterange) == 2:       
        user_cohort_list = metrics.get_user_cohort_list(daterange=daterange,languages=selected_languages,countries_list=country,app="CR")
        with st.spinner("Calculating..."):
            start = daterange[0].strftime("%b %d, %Y")
            end = daterange[1].strftime("%b %d, %Y")
            st.write("Timerange: " + start + " to " + end)
            df_download = uic.funnel_change_by_language_chart(
                selected_languages,
                country,
                upper_level=upper_level,
                bottom_level=bottom_level,
                daterange=daterange,
                user_list=user_cohort_list
            )
            csv = ui.convert_for_download(df_download)
            st.download_button(label="Download CSV",data=csv,file_name="funnel_change_by_language_chart.csv",key="fc-10",icon=":material/download:",mime="text/csv")

