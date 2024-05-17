import streamlit as st
import settings
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import pandas as pd
import users

st.title("Curious Learning Internal")

settings.initialize()
settings.init_user_list()
settings.init_cr_app_version_list()

st.subheader("Funnel History")

ui.display_definitions_table(ui.level_percent_definitions)
languages = users.get_language_list()
language = ui.single_selector(
    languages, title="Select a language", placement="side", key="fh-1"
)
countries_list = users.get_country_list()
country = ui.single_selector(
    countries_list,
    placement="side",
    title="Country Selection",
    key="fh-2",
)

selected_date, option = ui.calendar_selector(placement="side", key="fh-3", index=4)
daterange = ui.convert_date_to_range(selected_date, option)
col1, col2 = st.columns(2)

col2.image(
    "funnel.jpg",
    caption="Sample Funnel",
)

toggle = ui.compare_funnel_level_widget(placement="middle", key="fh-4")
with st.spinner("Calculating..."):
    uic.funnel_change_line_chart(
        daterange=daterange, language=language, countries_list=country, toggle=toggle
    )
