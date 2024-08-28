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

col1, col2 = st.columns((1,3),gap="large")


with col1:
    selected_date, option = ui.calendar_selector(placement="middle")
    daterange = ui.convert_date_to_range(selected_date, option)

    languages = users.get_language_list()
    language = ui.single_selector(
        languages, placement="middle", title="Select a language", key="acq-1"
    )
    countries_list = ui.multi_select_all(
    countries_list, title="Country Selection", key="acq-2",placement="middle"
)

if len(daterange) == 2:
    start = daterange[0].strftime("%b %d, %Y")
    end = daterange[1].strftime("%b %d, %Y")


    col2.subheader(start + " to " + end)

    LR = metrics.get_totals_by_metric(
        daterange, countries_list, stat="LR", app="CR", language=language
    )
    DC = metrics.get_totals_by_metric(
        daterange, countries_list, "DC", app="CR", language=language
    )
    SL = metrics.get_totals_by_metric(
        daterange, countries_list, "SL", app="CR", language=language
    )
    TS = metrics.get_totals_by_metric(
        daterange, countries_list, "TS", app="CR", language=language
    )

    PC = metrics.get_totals_by_metric(
        daterange, countries_list, "PC", app="CR", language=language
    )
    LA = metrics.get_totals_by_metric(
        daterange, countries_list, stat="LA", app="CR", language=language
    )
    RA = metrics.get_totals_by_metric(
        daterange, countries_list, stat="RA", app="CR", language=language
    )
    GC = metrics.get_totals_by_metric(
        daterange, countries_list, "GC", app="CR", language=language
    )

    funnel_data = {
        "Title": [
            "Learners Reached",
            "Download Completed",
            "Tapped Start",
            "Selected Level",
            "Puzzle Completed",
            "Learners Acquired",
            "Readers Acquired",
            "Game Completed",
        ],
        "Count": [LR, DC, TS, SL, PC, LA, RA,GC],
    }

    fig = uic.create_engagement_figure(funnel_data, "acq-5")
    col2.plotly_chart(fig, use_container_width=True)
