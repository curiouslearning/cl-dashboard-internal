import streamlit as st

from ui_components import levels_reached_chart


from settings import initialize
initialize()
from users import ensure_user_data_initialized
ensure_user_data_initialized()

from ui_widgets import get_apps
apps = get_apps()

levels_reached_chart(apps)
        
    