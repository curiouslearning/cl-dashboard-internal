import streamlit as st
import settings
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import users
import metrics

settings.initialize()
settings.init_user_list()
settings.init_cr_app_version_list()
ui.display_definitions_table("Data Notes",ui.data_notes)
countries_list = users.get_country_list()

ui.colorize_multiselect_options()


col1, col2, col3   = st.columns((1,1,1),gap="large")
col1.caption("Select a Date")
with col1:
    selected_date, option = ui.calendar_selector(placement="middle")
    daterange = ui.convert_date_to_range(selected_date, option)
with col2:
    languages = users.get_language_list()
    language = ui.single_selector(
        languages, placement="middle", title="Select a language", key="acq-1"
    )
with col3:
    countries_list = ui.multi_select_all(
    countries_list, title="Country Selection", key="acq-2",placement="middle"
    )

if len(daterange) == 2:
    start = daterange[0].strftime("%b %d, %Y")
    end = daterange[1].strftime("%b %d, %Y")
    st.write(start + " to " + end)

col1, col2  = st.columns((1,1),gap="large")
col1.markdown(
f"<strong><div style='text-align: center;'>Unity</div></strong>",
unsafe_allow_html=True,
)
col2.markdown(
f"<strong><div style='text-align: center;'>Curious Reader</div></strong>",
unsafe_allow_html=True,
)


if len(daterange) == 2:

    LR = metrics.get_totals_by_metric(
        daterange, countries_list, stat="LR", app="Unity", language=language
    )

    PC = metrics.get_totals_by_metric(
        daterange, countries_list, "PC", app="Unity", language=language
    )
    LA = metrics.get_totals_by_metric(
        daterange, countries_list, stat="LA", app="Unity", language=language
    )
    RA = metrics.get_totals_by_metric(
        daterange, countries_list, stat="RA", app="Unity", language=language
    )
    GC = metrics.get_totals_by_metric(
        daterange, countries_list, "GC", app="Unity", language=language
    )

    funnel_data = {
        "Title": [
            "Learners Reached",
            "Puzzle Completed",
            "Learners Acquired",
            "Readers Acquired",
            "Game Completed",
        ],
        "Count": [LR, PC, LA, RA, GC],
    }
    fig = uic.create_engagement_figure(funnel_data, "acq-3")
    col1.plotly_chart(fig, use_container_width=True,key="uvcr-1")

    LR = metrics.get_totals_by_metric(
        daterange, countries_list, stat="LR", app="CR", language=language
    )
    PC = metrics.get_totals_by_metric(
        daterange, countries_list, "PC", app="CR", language=language
    )
    LA = metrics.get_totals_by_metric(
        daterange, countries_list, stat="LA", app="CR", language=language
    )
    GC = metrics.get_totals_by_metric(
        daterange, countries_list, "GC", app="CR", language=language
    )
    RA = metrics.get_totals_by_metric(
        daterange, countries_list, "RA", app="CR", language=language
    )

    funnel_data = {
        "Title": [
            "Learners Reached",
            "Puzzle Completed",
            "Learners Acquired",
            "Readers Acquired",
            "Game Completed",
        ],
        "Count": [LR, PC, LA,RA, GC],
    }

    fig = uic.create_engagement_figure(funnel_data, "acq-4")
    col2.plotly_chart(fig, use_container_width=True,key="uvcr-2")

 