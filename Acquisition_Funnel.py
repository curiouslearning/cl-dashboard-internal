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

ui.language_selector()  # puts selection in session state
countries_list = users.get_country_list()
countries_list = ui.multi_select_all(
    countries_list, title="Country Selection", key="funnel_compare_key"
)

selected_date, option = ui.calendar_selector()
daterange = ui.convert_date_to_range(selected_date, option)
start = daterange[0].strftime("%b %d, %Y")
end = daterange[1].strftime("%b %d, %Y")
if len(daterange) == 2:
    st.subheader("Acquisition Funnel Comparison")
    st.subheader(start + " to " + end)

    col1, col2 = st.columns(2)

    st.session_state.app = "Unity"
    LR = metrics.get_totals_by_metric(daterange, countries_list, stat="LR")
    PC = metrics.get_totals_by_metric(daterange, countries_list, "PC")
    LA = metrics.get_totals_by_metric(daterange, countries_list, stat="LA")
    GC = metrics.get_totals_by_metric(daterange, countries_list, "GC")

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
    st.session_state.app = "CR"

    LR = metrics.get_totals_by_metric(daterange, countries_list, stat="LR")
    PC = metrics.get_totals_by_metric(daterange, countries_list, "PC")
    LA = metrics.get_totals_by_metric(daterange, countries_list, stat="LA")
    GC = metrics.get_totals_by_metric(daterange, countries_list, "GC")

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

    # These two are only available in Curious Reader
    SL = metrics.get_totals_by_metric(daterange, countries_list, "SL")
    TS = metrics.get_totals_by_metric(daterange, countries_list, "TS")

    st.subheader("Curious Reader")
    st.subheader(start + " to " + end)
    funnel_data = {
        "Title": [
            "Learners Reached",
            "Tapped Start",
            "Selected Level",
            "Puzzle Completed",
            "Learners Acquired",
            "Game Completed",
        ],
        "Count": [LR, TS, SL, PC, LA, GC],
    }

    fig = uic.create_engagement_figure(funnel_data, "key-2")
    st.plotly_chart(fig, use_container_width=True)
