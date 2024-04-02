import streamlit as st
import settings
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import users
import metrics


st.title("Curious Learning Internal")

settings.initialize()
settings.init_user_list()
settings.init_cr_app_version_list()

language = ui.language_selector()  # puts selection in session state

countries_list = users.get_country_list()
countries_list = ui.multi_select_all(
    countries_list, title="Country Selection", key="funnel_compare_key"
)

selected_date, option = ui.calendar_selector(placement="side")
daterange = ui.convert_date_to_range(selected_date, option)
start = daterange[0].strftime("%b %d, %Y")
end = daterange[1].strftime("%b %d, %Y")

st.sidebar.divider()

if len(daterange) == 2:
    st.subheader("Acquisition Funnel Comparison")
    st.subheader(start + " to " + end)

    col1, col2 = st.columns(2)

    LR = metrics.get_totals_by_metric(
        daterange, countries_list, stat="LR", app="Unity", language=language
    )
    PC = metrics.get_totals_by_metric(
        daterange, countries_list, "PC", app="Unity", language=language
    )
    LA = metrics.get_totals_by_metric(
        daterange, countries_list, stat="LA", app="Unity", language=language
    )
    GC = metrics.get_totals_by_metric(
        daterange, countries_list, "GC", app="Unity", language=language
    )

    funnel_data = {
        "Title": [
            "Learners Reached",
            "Puzzle Completed",
            "Learners Acquired",
            "Game Completed",
        ],
        "Count": [LR, PC, LA, GC],
    }
    fig = uic.create_engagement_figure(funnel_data, "key-1")
    col1.plotly_chart(fig, use_container_width=True)
    col1.markdown(
        f"<strong><div style='text-align: center;'>Unity</div></strong>",
        unsafe_allow_html=True,
    )

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

    funnel_data = {
        "Title": [
            "Learners Reached",
            "Puzzle Completed",
            "Learners Acquired",
            "Game Completed",
        ],
        "Count": [LR, PC, LA, GC],
    }

    fig = uic.create_engagement_figure(funnel_data, "key-2")
    col2.plotly_chart(fig, use_container_width=True)
    col2.markdown(
        f"<strong><div style='text-align: center;'>Curious Reader</div></strong>",
        unsafe_allow_html=True,
    )

    st.divider()
    st.subheader("Curious Reader")
    st.subheader(start + " to " + end)

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
            "Game Completed",
        ],
        "Count": [LR, DC, TS, SL, PC, LA, GC],
    }

    fig = uic.create_engagement_figure(funnel_data, "key-2")
    st.plotly_chart(fig, use_container_width=True)
