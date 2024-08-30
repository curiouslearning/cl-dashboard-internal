import streamlit as st
import settings
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import users
import metrics
from st_pages import add_page_title, get_nav_from_toml


settings.initialize()
settings.init_user_list()
settings.init_cr_app_version_list()

countries_list = users.get_country_list()

ui.colorize_multiselect_options()

languages = users.get_language_list()
countries_list = users.get_country_list()
app_versions = ui.app_version_selector(placement="col", key="crf-1")
displayLR = True
if app_versions != 'All':
    displayLR = False
uic.create_funnels(countries_list,languages,"cf-A",app_versions,displayLR)
