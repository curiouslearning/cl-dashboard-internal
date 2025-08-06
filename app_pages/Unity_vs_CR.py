import time
start = time.time()
import streamlit as st
st.write("Streamlit import", time.time() - start)
start = time.time()
from  settings import initialize
st.write("Settings import", time.time() - start)
start = time.time()
from  ui_components import create_funnels
st.write("UI Components", time.time() - start)
start = time.time()
import ui_widgets as ui
st.write("UI Widgets", time.time() - start)

initialize()

ui.display_definitions_table("Data Notes",ui.data_notes)

@st.cache_data
def load_countries():
    from users import get_country_list
    return get_country_list()

countries_list = load_countries()

ui.colorize_multiselect_options()

# --- Filter Row ---
col_date, col_lang, col_country = st.columns((1, 1, 1), gap="large")

with col_date:
    st.caption("Select a Date")
    selected_date, option = ui.calendar_selector(placement="middle")
    daterange = ui.convert_date_to_range(selected_date, option)

with col_lang:
    @st.cache_data
    def load_languages():
        from users import get_language_list
        return get_language_list()

    languages = load_languages()

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

    #delayed loading of import
    @st.cache_data(show_spinner="Loading user cohorts…")
    def get_user_cohort_list_lazy(daterange, languages, countries_list, app):
        from metrics import get_user_cohort_list
        return get_user_cohort_list(
            daterange=daterange,
            languages=languages,
            countries_list=countries_list,
            app=app
        )

    # --- Get user cohorts ---
    user_cohort_list_unity = get_user_cohort_list_lazy(
        daterange=daterange,
        languages=language,
        countries_list=countries_list,
        app="Unity"
    )
    user_cohort_list_cr = get_user_cohort_list_lazy(
        daterange=daterange,
        languages=language,
        countries_list=countries_list,
        app="CR"
    )

    col1, col2 = st.columns((1, 1), gap="large")

    # --- Funnel Charts ---
    with col1:
        create_funnels(
            countries_list=countries_list,
            daterange=daterange,
            app="Unity",
            key_prefix="u-1",
            languages=languages,
            user_list=user_cohort_list_unity
        )

    with col2:
        create_funnels(
            countries_list=countries_list,
            daterange=daterange,
            app="CR",
            funnel_size="compact",
            key_prefix="u-2",
            languages=languages,
            user_list=user_cohort_list_cr)
        
