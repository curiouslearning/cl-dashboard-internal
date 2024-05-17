import streamlit as st
import settings
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import pandas as pd
import users
import metrics

st.title("Curious Learning Internal")

settings.initialize()
settings.init_user_list()
settings.init_cr_app_version_list()

ui.display_definitions_table(ui.level_percent_definitions)
st.subheader("Engagement Improvement by Level")
col1, col2 = st.columns(2)

col2.image(
    "funnel.jpg",
    caption="Sample Funnel",
)

df_languages = metrics.get_counts(
    type="app_language",
    app="CR",
    language=["All"],
)

df_top10 = (
    df_languages[["app_language", "LR"]].sort_values(by="LR", ascending=False).head(10)
)


df = users.get_language_list()

selected_languages = ui.multi_select_all(
    df, placement="side", title="Select languages", key="la-1"
)
if "la_first_run" not in st.session_state:
    st.session_state["la_first_run"] = "true"
    selected_languages = df_top10["app_language"].to_list()

countries_list = users.get_country_list()
country = ui.single_selector(
    countries_list,
    placement="side",
    title="Country Selection",
    key="la-2",
)
selected_date, option = ui.calendar_selector(placement="side", key="la-3", index=4)
daterange = ui.convert_date_to_range(selected_date, option)

upper_level, bottom_level = ui.level_comparison_selector(placement="middle")
if st.toggle(label="Load Top 10 Learners Reached"):
    selected_languages = df_top10["app_language"].to_list()
with st.spinner("Calculating..."):
    uic.funnel_change_by_language_chart(
        selected_languages,
        country,
        upper_level=upper_level,
        bottom_level=bottom_level,
        daterange=daterange,
    )
