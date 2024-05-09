import streamlit as st
import settings
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import pandas as pd


st.title("Curious Learning Internal")

settings.initialize()
settings.init_user_list()
settings.init_cr_app_version_list()

st.subheader("Funnel History")

language = ui.language_selector(placement="side", key="lang-funnel-changes")
countries_list = ui.country_selector(
    placement="side", title="Country Selection", key="country--funnel-changes"
)
expander = st.expander("Definitions")
# CSS to inject contained in a string
hide_table_row_index = """
                <style>
                thead tr th:first-child {display:none}
                tbody th {display:none}
                </style>
                """
# Inject CSS with Markdown
st.markdown(hide_table_row_index, unsafe_allow_html=True)
def_df = pd.DataFrame(
    [
        [
            "DC over LR",
            "Downloads Completed divided by Learners Reached",
        ],
        [
            "TS over LR",
            "Tapped Start divided by Learners Reached",
        ],
        [
            "SL over LR",
            "Selected Level divided by Learners Reached",
        ],
        [
            "PC over LR",
            "Puzzle Completed divided by Learners Reached",
        ],
        [
            "LA over LR",
            "Learner Acquired (Level completed) divided by Learners Reached",
        ],
        [
            "GC over LR",
            "Game Complted divided by Learners Reached",
        ],
    ],
    columns=["Name", "Definition"],
)
expander.table(def_df)

(
    col1,
    col2,
) = cols = st.columns(2)

col2.image(
    "funnel.jpg",
    caption="Sample Funnel",
)

toggle = col1.radio(
    options=[
        "Compare to Initial",
        "Compare to Previous",
    ],
    label="",
    horizontal=True,
    index=0,
)

uic.funnel_change_line_chart(language, countries_list, toggle)
