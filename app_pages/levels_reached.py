
from ui_components import levels_reached_chart
from settings import initialize
from users import ensure_user_data_initialized
from ui_widgets import get_apps
import streamlit as st

initialize()

ensure_user_data_initialized()

apps = get_apps()

apps = st.pills("Select apps to chart:", apps, selection_mode="multi",default=["Unity","CR","hindi-standalone"])

levels_reached_chart(apps)
        