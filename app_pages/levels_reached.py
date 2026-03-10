from ui_components import levels_reached_chart
from settings import initialize
from users import ensure_user_data_initialized, get_cohort_list
from ui_widgets import get_apps
import streamlit as st

initialize()
ensure_user_data_initialized()

apps = get_apps()
apps = [a for a in get_apps() if a != "All"]
cohorts = get_cohort_list()

# Combine into single list, prefixed to avoid name collisions
options = [f"app:{a}" for a in apps] + [f"cohort:{c}" for c in cohorts]
default = ["app:Unity", "app:CR"]

selected = st.pills("Select apps and cohorts to chart:", options, selection_mode="multi", default=default)

# Split back out for downstream use
selected_apps = [s.replace("app:", "") for s in selected if s.startswith("app:")]
selected_cohorts = [s.replace("cohort:", "") for s in selected if s.startswith("cohort:")]

levels_reached_chart(selected_apps, selected_cohorts)