import streamlit as st
import settings
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import pandas as pd
import users
import metrics


settings.initialize()
settings.init_user_list()
settings.init_cr_app_version_list()

ui.display_definitions_table(ui.level_percent_definitions)

st.markdown(
    """
    :red-background[NOTE:]
    :green[This chart lets you see the individual levels in the funnel across time]
    """
)
col1, col2, col3 = st.columns((1,1,2))


df_languages = metrics.get_counts(
    type="app_language",
    app="CR",
    language=["All"],
)

df_top10 = (
    df_languages[["app_language", "LR"]].sort_values(by="LR", ascending=False).head(10)
)
countries_list = users.get_country_list()

with col1:
    country = ui.single_selector(
        countries_list,
        placement="middle",
        title="Country Selection",
        key="la-2",
    )
    
    selected_date, option = ui.calendar_selector(placement="middle", key="fa-3", index=4)
    daterange = ui.convert_date_to_range(selected_date, option)
 

with col3:

    if st.toggle(label="Use Top 10 LR Languages", value=True):
        selected_languages = df_top10["app_language"].to_list()
    else:
        df = users.get_language_list()
        selected_languages = ui.multi_select_all(
            df, placement="middle", title="Select languages", key="fa-1"
        )

with col2:
    toggle = ui.compare_funnel_level_widget(placement="middle", key="fa-4")


if len(selected_languages) > 0:
    with st.spinner("Calculating..."):
        uic.funnel_change_line_chart(
            daterange=daterange,
            languages=selected_languages,
            countries_list=country,
            toggle=toggle,
        )

