import streamlit as st
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import users
import datetime as dt
from dateutil.relativedelta import relativedelta
import settings
import metrics


settings.initialize()
settings.init_user_list()
settings.init_cr_app_version_list()

ui.display_definitions_table("Definitions",ui.level_percent_definitions)

col1, col2 = st.columns(2)

languages = users.get_language_list()
countries_list = users.get_country_list()

with col1:
    language = ui.single_selector(
        languages, placement="col", title="Select a language", key="crf-2"
    )   
with col2:
    countries_list = ui.multi_select_all(
        countries_list,
        title="Country Selection",
        key="LA_LR_Time",
        placement="middle",
    )

# Callback function for radio button
def radio_callback():
    st.session_state["buffer_time"] = st.session_state["radio_selection"]
    if "slider_date" in st.session_state:
        del st.session_state["slider_date"]
    if "max_date" in st.session_state:
        del st.session_state["max_date"]

# Initialize buffer_time in session state if not already set
if "buffer_time" not in st.session_state:
    st.session_state["buffer_time"] = 30  # Default selection

# Ensure the radio button is rendered only once
if "radio_selection" not in st.session_state:
    st.session_state["radio_selection"] = st.session_state["buffer_time"]

st.markdown("")
st.markdown("")
st.markdown(":orange[Select the amount of days prior to today to become the date window for the user cohort.]")
# Radio button with session state and callback
buffer_time = st.radio(
    label="Days",
    options=[15, 30, 60, 90],
    horizontal=True,
    index=[15, 30, 60, 90].index(st.session_state["radio_selection"]),
    key="radio_selection",
    on_change=radio_callback
)
# Date calculation logic
today = dt.datetime.now().date()
if "slider_date" not in st.session_state:
    max_date = today - relativedelta(days=st.session_state["buffer_time"])
    min_date = dt.date(2023, 10, 1)
    st.session_state.max_date = max_date
else:
    min_date, max_date = st.session_state.slider_date

# Render the slider
selected_date = ui.custom_date_selection_slider(min_date, max_date, placement="middle")
daterange = ui.convert_date_to_range(selected_date, option="")

if len(countries_list) > 0:
    # Get all of the users in the user selected window - this is the cohort
    df_user_cohort = metrics.filter_user_data(daterange=daterange,countries_list=countries_list,app="CR",language=languages)

    # All we need is their cr_user_id
    user_cohort_list = df_user_cohort["cr_user_id"]

    # Get superset of  the users up through today
    daterange = [daterange[0],today]
    df = metrics.filter_user_data(daterange=daterange,countries_list=countries_list,app="CR",language=languages,user_list=user_cohort_list)

    uic.create_funnels(countries_list=countries_list,daterange=daterange,key_prefix="dc-1",app_versions="All",languages=languages,displayLR=True,user_list=user_cohort_list,display_FO=False)

