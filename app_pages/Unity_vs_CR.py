import streamlit as st
import settings
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import users
import metrics
from settings import get_logger

settings.initialize()
settings.init_user_list()

ui.display_definitions_table("Data Notes",ui.data_notes)
countries_list = users.get_country_list()

ui.colorize_multiselect_options()

logger = settings.get_logger()

# --- Filter Row ---
col_date, col_lang, col_country = st.columns((1, 1, 1), gap="large")

with col_date:
    st.caption("Select a Date")
    selected_date, option = ui.calendar_selector(placement="middle")
    daterange = ui.convert_date_to_range(selected_date, option)

with col_lang:
    languages = users.get_language_list()
    language = ui.single_selector(
        languages, placement="middle", title="Select a language", key="acq-1"
    )

with col_country:
    countries_list = ui.multi_select_all(
        countries_list,
        title="Country Selection",
        key="acq-2",
        placement="middle"
    )

# --- Date Display ---
if len(daterange) == 2:
    start = daterange[0].strftime("%b %d, %Y")
    end = daterange[1].strftime("%b %d, %Y")
    st.write(f"{start} to {end}")

# --- Header Row ---
col_unity_head, col_cr_head = st.columns((1, 1), gap="large")
with col_unity_head:
    st.markdown("<strong><div style='text-align: center;'>Unity</div></strong>", unsafe_allow_html=True)
with col_cr_head:
    st.markdown("<strong><div style='text-align: center;'>Curious Reader</div></strong>", unsafe_allow_html=True)


if len(daterange) == 2 and countries_list:

    # --- Get user cohorts ---
    user_cohort_list_unity = metrics.get_user_cohort_list(
        daterange=daterange,
        languages=language,
        countries_list=countries_list,
        app="Unity"
    )
    user_cohort_list_cr = metrics.get_user_cohort_list(
        daterange=daterange,
        languages=language,
        countries_list=countries_list,
        app="CR"
    )

    col1, col2 = st.columns((1, 1), gap="large")

    # --- Funnel Charts ---
    with col1:
        uic.create_funnels(
            countries_list=countries_list,
            daterange=daterange,
            app="Unity",
            key_prefix="u-1",
            languages=languages,
            user_list=user_cohort_list_unity
        )

    with col2:
        uic.create_funnels(
            countries_list=countries_list,
            daterange=daterange,
            app="CR",
            funnel_size="compact",
            key_prefix="u-2",
            languages=languages,
            user_list=user_cohort_list_cr)
        
