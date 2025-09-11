import streamlit as st
import settings
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import pandas as pd


data_notes = pd.DataFrame(
    [
        [
            "Minimum LR",
            "Currently examining only languages with at least 4000 LR to eliminate random languages with only a few hundred users"
        ],
        [
            "Edge case",
            "Because imported users have the possibility of having multiple entries using user_pseudo_id, app_language,  \
            and country combination, there is an edge case where LR can be less than a DC or TS \
            number due to how the removal of multiple user entries is done  \
            (If the entry with different country is kept, then the ones with other languages are dropped). \
            In these cases, LR is set to DC or TS.  Occurence of this is very rare.",
        ],
    ],
    columns=["Note", "Description"],
)



settings.initialize()
from users import ensure_user_data_initialized
ensure_user_data_initialized()

ui.display_definitions_table("Definitions",ui.level_percent_definitions)
ui.display_definitions_table("Data Notes",data_notes)

st.subheader("Top and worst performing languages")
st.markdown(
    """
    :red-background[NOTE:]
    :green[The best and worst performing funnel levels.  Percentage of remaining 
    users from previous level]
    """
)
selection = st.radio(
    label="Choose view", options=["Top performing", "Worst performing"], horizontal=True
)
#min_LR sets the minimum sample size to use in determining whether a language is included
uic.top_and_bottom_languages_per_level(selection,min_LR=4000)
