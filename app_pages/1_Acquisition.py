import streamlit as st
import settings
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import users
import pandas as pd
import datetime as dt

settings.initialize()
settings.init_campaign_data()
settings.init_user_list()
ui.display_definitions_table("Definitions",ui.level_definitions)

ui.colorize_multiselect_options()

data_notes = pd.DataFrame(
    [
        [
            "Minimum LR",
            "Scatter chart currently set to LR and LA groups > 200",
        ],
        [
            "Date selection",
            "Cost based charts only include data for campaigns that match our naming conventions that were running before and or after the date the names were changed",
        ],
    ],
    columns=["Note", "Description"],
)

ui.display_definitions_table("Data Notes",data_notes)



st.divider()
st.subheader("Learners Over Time")

col1, col2 = st.columns(2, gap="large")

with col1:
    countries_list = users.get_country_list()
    countries_list = ui.multi_select_all(
        countries_list,
        title="Country Selection",
        key="LA_LR_Time",
        placement="middle",
    )
    languages = users.get_language_list()
    language = ui.single_selector(
        languages, placement="middle", title="Select a language", key="a-2"
    )
    selected_date, option = ui.calendar_selector(placement="middle", key="fa-3", index=1)
    daterange = ui.convert_date_to_range(selected_date, option)

with col2:
    app = ui.app_selector(placement="middle")
    option = st.radio(
        "Select a statistic", ("LR", "LA"), index=0, horizontal=True, key="a-1"
    )
    display_category = st.radio(
        "Display by", ("Country", "Language"), index=0, horizontal=True, key="a-3"
    )


if (len(countries_list)) > 0 and (len(daterange) == 2):
    start = daterange[0].strftime("%b %d, %Y")
    end = daterange[1].strftime("%b %d, %Y")
    st.write("Timerange: " + start + " to " + end)
    uic.LR_LA_line_chart_over_time(
        daterange, countries_list, app=app, language=language, option=option,display_category=display_category,aggregate=False
    )
    uic.LR_LA_line_chart_over_time(
        daterange, countries_list, app=app, language=language, option=option,display_category=display_category,aggregate=True
    )



