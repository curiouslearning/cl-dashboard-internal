import streamlit as st
import settings
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import metrics
import users

st.title("Curious Learning Internal")

settings.initialize()
settings.init_user_list()
settings.init_cr_app_version_list()

st.subheader("Curious Reader Funnel Comparison")
languages = users.get_language_list()
countries_list = users.get_country_list()

col1, col2 = st.columns(2)
with col1:
    app_versionsA = ui.app_version_selector(placement="col", key="cf-1")
with col2:  
    app_versionsB = ui.app_version_selector(placement="col", key="cf-2")

# if either of the funnels uses app_version, eliminate LR for both
displayLR = True
if app_versionsA != 'All' or app_versionsB != 'All':
    displayLR = False
with col1:
    uic.create_funnels(countries_list,languages,"cf-A",app_versionsA,displayLR)
with col2:  
    uic.create_funnels(countries_list,languages,"cf-B",app_versionsB,displayLR)
