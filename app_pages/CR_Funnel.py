import streamlit as st
import settings
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import users
from st_pages import add_page_title, get_nav_from_toml


settings.initialize()
settings.init_user_list()
settings.init_cr_app_version_list()
ui.display_definitions_table("Data Notes",ui.data_notes)

countries_list = users.get_country_list()

ui.colorize_multiselect_options()
col1, col2 = st.columns(2)

languages = users.get_language_list()
countries_list = users.get_country_list()

with col1:
    app_versions = ui.app_version_selector(placement="col", key="crf-1")
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
    
    selected_date, option = ui.calendar_selector(placement="col", key="crf-4")
    daterange = ui.convert_date_to_range(selected_date, option)

displayLR = True
if app_versions != 'All':
    displayLR = False

uic.create_funnels(countries_list=countries_list,
                   languages=language,
                   key_prefix="cf-A",
                   app_versions=app_versions,
                   displayLR=True,
                   daterange=daterange)
