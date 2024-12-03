import streamlit as st
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import users
import datetime as dt
from dateutil.relativedelta import relativedelta
import settings


settings.initialize()
settings.init_user_list()
settings.init_cr_app_version_list()

ui.display_definitions_table("Definitions",ui.level_percent_definitions)


bake_time = st.radio(label="Select the time in days elapsed since first open required:",
                     options=[15,30,60,90],
                     horizontal=True,
                     index=1,
                     )


languages = users.get_language_list()
countries_list = users.get_country_list()

selected_country = ui.single_selector(
        countries_list, placement="col", title="Select a country", key="dc-1"
    )

st.write(f"[Main Script] Session State Before Slider: {st.session_state.get('slider_date')}")


today = dt.datetime.now().date()
if "slider_date" not in st.session_state:
    max_date = today - relativedelta(days=bake_time)
    min_date = dt.date(2023, 10, 1)
else:
    min_date = st.session_state.slider_date[0]
    max_date = today - relativedelta(days=bake_time)


selected_date = ui.custom_date_selection_slider(min_date, max_date, placement="middle")


daterange = ui.convert_date_to_range(selected_date, option="")
selected_date

