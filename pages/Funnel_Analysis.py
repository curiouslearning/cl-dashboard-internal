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
st.markdown(
    """
    :red-background[NOTE:]
    :green[This chart lets you compare one specific level across the languages selected.
    It compares the selected level % drop from the selected upper level.]
    """
)
col1, col2, col3 = st.columns(3)

col3.image(
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


if st.sidebar.toggle(label="Use Top 10 LR Languages", value=True):
    selected_languages = df_top10["app_language"].to_list()
else:
    df = users.get_language_list()
    selected_languages = ui.multi_select_all(
        df, placement="side", title="Select languages", key="fa-1"
    )


countries_list = users.get_country_list()
with col1:
    country = ui.single_selector(
        countries_list,
        placement="side",
        title="Country Selection",
        key="la-2",
    )
selected_date, option = ui.calendar_selector(placement="side", key="fa-3", index=4)
daterange = ui.convert_date_to_range(selected_date, option)

with col1:
    upper_level, bottom_level = ui.level_comparison_selector(placement="middle")

with st.spinner("Calculating..."):
    uic.funnel_change_by_language_chart(
        selected_languages,
        country,
        upper_level=upper_level,
        bottom_level=bottom_level,
        daterange=daterange,
    )

st.divider()

st.subheader("Sideways Funnels by Language")
st.markdown(
    """
    :red-background[NOTE:]
    :green[This chart lets you compare the funnels of selected languages]
    """
)
if len(selected_languages) > 0:
    uic.top_tilted_funnel(
        languages=selected_languages,
        countries_list=countries_list,
        daterange=daterange,
        option="LR",
    )
st.divider()
st.subheader("Levels Across Time")
st.markdown(
    """
    :red-background[NOTE:]
    :green[This chart lets you see the individual levels in the funnel across time]
    """
)

col1, col2 = st.columns(2)

with col1:
    toggle = ui.compare_funnel_level_widget(placement="middle", key="fa-4")
if len(selected_languages) > 0:
    with st.spinner("Calculating..."):
        uic.funnel_change_line_chart(
            daterange=daterange,
            languages=selected_languages,
            countries_list=country,
            toggle=toggle,
        )
