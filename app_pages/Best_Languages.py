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

st.subheader("Top and worst performing languages")
st.markdown(
    """
    :red-background[NOTE:]
    :green[The best and worst performing funnel levels.  Percentage of remaining 
    users from previous level]
    """
)
selection = st.radio(
    label="Choose view", options=["Top performing", "Worst performing"], horizontal=True
)
uic.bottom_languages_per_level(selection)
