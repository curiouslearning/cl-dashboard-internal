import streamlit as st
import settings
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import metrics
import users

st.title("Curious Learning Internal")

settings.initialize()
settings.init_user_list()
settings.init_cr_app_version_list()

st.subheader("Curious Reader Funnel Comparison")
languages = users.get_language_list()
countries_list = users.get_country_list()

col1, col2 = st.columns(2)
with col1:

    app_version = ui.app_version_selector(placement="col", key="cf-1")

    language = ui.single_selector(
        languages, placement="col", title="Select a language", key="cf-2"
    )

    selected_country = ui.single_selector(
        countries_list, placement="col", title="Select a country", key="cf-3"
    )

    selected_date, option = ui.calendar_selector(placement="col", key="cf-4")
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
            countries_list=selected_country,
            app="CR",
        )
        SL = metrics.get_totals_by_metric(
            daterange,
            stat="SL",
            cr_app_version=app_version,
            language=language,
            countries_list=selected_country,
            app="CR",
        )
        TS = metrics.get_totals_by_metric(
            daterange,
            stat="TS",
            cr_app_version=app_version,
            language=language,
            countries_list=selected_country,
            app="CR",
        )

        PC = metrics.get_totals_by_metric(
            daterange,
            stat="PC",
            cr_app_version=app_version,
            language=language,
            countries_list=selected_country,
            app="CR",
        )
        LA = metrics.get_totals_by_metric(
            daterange,
            stat="LA",
            cr_app_version=app_version,
            language=language,
            countries_list=selected_country,
            app="CR",
        )
        LR = metrics.get_totals_by_metric(
            daterange,
            stat="LR",
            cr_app_version=app_version,
            language=language,
            countries_list=selected_country,
            app="CR",
        )
        GC = metrics.get_totals_by_metric(
            daterange,
            stat="GC",
            cr_app_version=app_version,
            language=language,
            countries_list=selected_country,
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

        fig = uic.create_engagement_figure(funnel_data, key="cf-5")
        st.plotly_chart(fig, use_container_width=True)


with col2:

    app_version = ui.app_version_selector(placement="col", key="cf-6")

    language = ui.single_selector(
        languages, placement="col", title="Select a language", key="cf-7"
    )

    selected_country = ui.single_selector(
        countries_list, placement="col", title="Select a country", key="cf-8"
    )

    selected_date, option = ui.calendar_selector(placement="col", key="cf-9")
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
            countries_list=selected_country,
            app="CR",
        )
        SL = metrics.get_totals_by_metric(
            daterange,
            stat="SL",
            cr_app_version=app_version,
            language=language,
            countries_list=selected_country,
            app="CR",
        )
        TS = metrics.get_totals_by_metric(
            daterange,
            stat="TS",
            language=language,
            cr_app_version=app_version,
            countries_list=selected_country,
            app="CR",
        )

        PC = metrics.get_totals_by_metric(
            daterange,
            stat="PC",
            cr_app_version=app_version,
            language=language,
            countries_list=selected_country,
            app="CR",
        )
        LA = metrics.get_totals_by_metric(
            daterange,
            stat="LA",
            cr_app_version=app_version,
            language=language,
            countries_list=selected_country,
            app="CR",
        )
        LR = metrics.get_totals_by_metric(
            daterange,
            stat="LR",
            cr_app_version=app_version,
            language=language,
            countries_list=selected_country,
            app="CR",
        )
        GC = metrics.get_totals_by_metric(
            daterange,
            stat="GC",
            cr_app_version=app_version,
            language=language,
            countries_list=selected_country,
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

        fig = uic.create_engagement_figure(funnel_data, "cf-10")
        st.plotly_chart(fig, use_container_width=True)
