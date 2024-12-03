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

# Callback function for radio button
def radio_callback():
    st.session_state["bake_time"] = st.session_state["radio_selection"]
    if "slider_date" in st.session_state:
        del st.session_state["slider_date"]
    if "max_date" in st.session_state:
        del st.session_state["max_date"]

# Initialize bake_time in session state if not already set
if "bake_time" not in st.session_state:
    st.session_state["bake_time"] = 30  # Default selection

# Ensure the radio button is rendered only once
if "radio_selection" not in st.session_state:
    st.session_state["radio_selection"] = st.session_state["bake_time"]

# Radio button with session state and callback
bake_time = st.radio(
    label="Select the time in days elapsed since first open required:",
    options=[15, 30, 60, 90],
    horizontal=True,
    index=[15, 30, 60, 90].index(st.session_state["radio_selection"]),
    key="radio_selection",
    on_change=radio_callback
)

# Fetch other inputs
languages = users.get_language_list()
countries_list = users.get_country_list()

selected_country = ui.single_selector(
    countries_list, placement="col", title="Select a country", key="dc-1"
)

# Date calculation logic
today = dt.datetime.now().date()
if "slider_date" not in st.session_state:
    max_date = today - relativedelta(days=st.session_state["bake_time"])
    min_date = dt.date(2023, 10, 1)
    st.session_state.max_date = max_date
else:
    min_date, max_date = st.session_state.slider_date

# Render the slider
selected_date = ui.custom_date_selection_slider(min_date, max_date, placement="middle")

daterange = ui.convert_date_to_range(selected_date, option="")

