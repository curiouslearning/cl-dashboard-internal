import streamlit as st
import settings
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import users
import datetime as dt
import metrics
import pandas as pd

st.title("Curious Learning Internal")

settings.initialize()
settings.init_user_list()
settings.init_cr_app_version_list()

st.subheader("Curious Reader Funnel Comparison")
min_date = dt.datetime(2021, 1, 1).date()
max_date = dt.date.today()

col1, col2 = st.columns(2)
with col1:

    app_version = ui.app_version_selector(placement="col", key="version-1")
    language = ui.language_selector(placement="col", key="lang-a")
    countries_list = ui.country_selector(
        placement="col", title="Country Selection", key="country-a"
    )

    selected_date, option = ui.calendar_selector(placement="col", key="cal-1")
    daterange = ui.convert_date_to_range(selected_date, option)

    if len(daterange) == 2:
        start = daterange[0].strftime("%b %d, %Y")
        end = daterange[1].strftime("%b %d, %Y")
        st.caption(start + " to " + end)

        DC = metrics.get_totals_by_metric(
            daterange,
            stat="DC",
            cr_app_version=app_version,
            language=language,
            countries_list=countries_list,
            app="CR",
        )
        SL = metrics.get_totals_by_metric(
            daterange,
            stat="SL",
            cr_app_version=app_version,
            language=language,
            countries_list=countries_list,
            app="CR",
        )
        TS = metrics.get_totals_by_metric(
            daterange,
            stat="TS",
            cr_app_version=app_version,
            language=language,
            countries_list=countries_list,
            app="CR",
        )

        PC = metrics.get_totals_by_metric(
            daterange,
            stat="PC",
            cr_app_version=app_version,
            language=language,
            countries_list=countries_list,
            app="CR",
        )
        LA = metrics.get_totals_by_metric(
            daterange,
            stat="LA",
            cr_app_version=app_version,
            language=language,
            countries_list=countries_list,
            app="CR",
        )
        LR = metrics.get_totals_by_metric(
            daterange,
            stat="LR",
            cr_app_version=app_version,
            language=language,
            countries_list=countries_list,
            app="CR",
        )
        GC = metrics.get_totals_by_metric(
            daterange,
            stat="GC",
            cr_app_version=app_version,
            language=language,
            countries_list=countries_list,
            app="CR",
        )

        funnel_data = {
            "Title": [
                "Learner Reached",
                "Download Completed",
                "Tapped Start",
                "Selected Level",
                "Puzzle Completed",
                "Learners Acquired",
                "Game Completed",
            ],
            "Count": [LR, DC, TS, SL, PC, LA, GC],
        }

        fig = uic.create_engagement_figure(funnel_data, "funnel-1")
        st.plotly_chart(fig, use_container_width=True)


with col2:

    app_version = ui.app_version_selector(placement="col", key="version-2")
    language = ui.language_selector(placement="col", key="lang-b")

    countries_list = ui.country_selector(
        placement="col", title="Country Selection", key="country-b"
    )

    selected_date, option = ui.calendar_selector(placement="col", key="cal-2")
    daterange = ui.convert_date_to_range(selected_date, option)

    if len(daterange) == 2:
        start = daterange[0].strftime("%b %d, %Y")
        end = daterange[1].strftime("%b %d, %Y")
        st.caption(start + " to " + end)

        DC = metrics.get_totals_by_metric(
            daterange,
            stat="DC",
            cr_app_version=app_version,
            language=language,
            countries_list=countries_list,
            app="CR",
        )
        SL = metrics.get_totals_by_metric(
            daterange,
            stat="SL",
            cr_app_version=app_version,
            language=language,
            countries_list=countries_list,
            app="CR",
        )
        TS = metrics.get_totals_by_metric(
            daterange,
            stat="TS",
            language=language,
            cr_app_version=app_version,
            countries_list=countries_list,
            app="CR",
        )

        PC = metrics.get_totals_by_metric(
            daterange,
            stat="PC",
            cr_app_version=app_version,
            language=language,
            countries_list=countries_list,
            app="CR",
        )
        LA = metrics.get_totals_by_metric(
            daterange,
            stat="LA",
            cr_app_version=app_version,
            language=language,
            countries_list=countries_list,
            app="CR",
        )
        LR = metrics.get_totals_by_metric(
            daterange,
            stat="LR",
            cr_app_version=app_version,
            countries_list=countries_list,
            app="CR",
        )
        GC = metrics.get_totals_by_metric(
            daterange,
            stat="GC",
            cr_app_version=app_version,
            language=language,
            countries_list=countries_list,
            app="CR",
        )

        funnel_data = {
            "Title": [
                "Learner Reached",
                "Download Completed",
                "Tapped Start",
                "Selected Level",
                "Puzzle Completed",
                "Learners Acquired",
                "Game Completed",
            ],
            "Count": [LR, DC, TS, SL, PC, LA, GC],
        }

        fig = uic.create_engagement_figure(funnel_data, "funnel-2")
        st.plotly_chart(fig, use_container_width=True)
