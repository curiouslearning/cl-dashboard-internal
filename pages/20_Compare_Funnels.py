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

    selected_date, option = ui.calendar_selector(placement="col", key="cal-1")
    daterange = ui.convert_date_to_range(selected_date, option)

    if len(daterange) == 2:
        start = daterange[0].strftime("%b %d, %Y")
        end = daterange[1].strftime("%b %d, %Y")
        st.caption(start + " to " + end)

        SL = metrics.get_totals_by_metric(
            daterange,
            stat="SL",
            cr_app_version=app_version,
            app="CR",
        )
        TS = metrics.get_totals_by_metric(
            daterange,
            stat="TS",
            cr_app_version=app_version,
            app="CR",
        )

        PC = metrics.get_totals_by_metric(
            daterange,
            stat="PC",
            cr_app_version=app_version,
            app="CR",
        )
        LA = metrics.get_totals_by_metric(
            daterange,
            stat="LA",
            cr_app_version=app_version,
            app="CR",
        )
        GC = metrics.get_totals_by_metric(
            daterange,
            stat="GC",
            cr_app_version=app_version,
            app="CR",
        )

        funnel_data = {
            "Title": [
                "Tapped Start",
                "Selected Level",
                "Puzzle Completed",
                "Learners Acquired",
                "Game Completed",
            ],
            "Count": [TS, SL, PC, LA, GC],
        }

        fig = uic.create_engagement_figure(funnel_data, "funnel-1")
        st.plotly_chart(fig, use_container_width=True)


with col2:

    app_version = ui.app_version_selector(placement="col", key="version-2")

    selected_date, option = ui.calendar_selector(placement="col", key="cal-2")
    daterange = ui.convert_date_to_range(selected_date, option)

    if len(daterange) == 2:
        start = daterange[0].strftime("%b %d, %Y")
        end = daterange[1].strftime("%b %d, %Y")
        st.caption(start + " to " + end)
        # Add CR only events and allow for version filtering
        SL = metrics.get_totals_by_metric(
            daterange,
            stat="SL",
            cr_app_version=app_version,
            app="CR",
        )
        TS = metrics.get_totals_by_metric(
            daterange,
            stat="TS",
            cr_app_version=app_version,
            app="CR",
        )

        PC = metrics.get_totals_by_metric(
            daterange,
            stat="PC",
            cr_app_version=app_version,
            app="CR",
        )
        LA = metrics.get_totals_by_metric(
            daterange,
            stat="LA",
            cr_app_version=app_version,
            app="CR",
        )
        GC = metrics.get_totals_by_metric(
            daterange,
            stat="GC",
            cr_app_version=app_version,
            app="CR",
        )

        funnel_data = {
            "Title": [
                "Tapped Start",
                "Selected Level",
                "Puzzle Completed",
                "Learners Acquired",
                "Game Completed",
            ],
            "Count": [TS, SL, PC, LA, GC],
        }

        fig = uic.create_engagement_figure(funnel_data, "funnel-2")
        st.plotly_chart(fig, use_container_width=True)
