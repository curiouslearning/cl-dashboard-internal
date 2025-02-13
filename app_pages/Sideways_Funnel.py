import streamlit as st
import settings
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import users
import metrics
from dateutil.relativedelta import relativedelta
import datetime as dt

settings.initialize()
settings.init_user_list()
settings.init_cr_app_version_list()

ui.display_definitions_table("Definitions",ui.level_percent_definitions)

st.markdown(
    """
    :green-background[NOTE:]
    :green[This chart lets you compare one specific level across the languages selected.
    It compares the selected level % drop from the selected upper level.]
    """
)

# Callback function for radio button
def radio_callback():
    st.session_state["buffer_time"] = st.session_state["radio_selection"]
    if "slider_date" in st.session_state:
        del st.session_state["slider_date"]
    if "max_date" in st.session_state:
        del st.session_state["max_date"]
        
# Initialize buffer_time in session state if not already set
if "buffer_time" not in st.session_state:
    st.session_state["buffer_time"] = 30  # Default selection

# Ensure the radio button is rendered only once
if "radio_selection" not in st.session_state:
    st.session_state["radio_selection"] = st.session_state["buffer_time"]

col1, col2, col3 = st.columns(3)

df_languages = metrics.get_counts(
    type="app_language",
    app="CR",
    language=["All"],
)

df_top10 = (
    df_languages[["app_language", "LR"]].sort_values(by="LR", ascending=False).head(10)
)

countries_list = users.get_country_list()
with col1:
    country = ui.single_selector(
        countries_list,
        placement="middle",
        title="Country Selection",
        key="la-2",
    )

with col3:
    buffer_time = st.radio(
        label="Days",
        options=[15, 30, 60, 90],
        horizontal=True,
        index=[15, 30, 60, 90].index(st.session_state["radio_selection"]),
        key="radio_selection",
        on_change=radio_callback
    )
    
with col3:


    # Date calculation logic
    today = dt.datetime.now().date()
    if "slider_date" not in st.session_state:
        max_date = today - relativedelta(days=st.session_state["buffer_time"])
        min_date = dt.date(2023, 10, 1)
        st.session_state.max_date = max_date
    else:
        min_date, max_date = st.session_state.slider_date

    # Render the slider
    selected_date = ui.custom_date_selection_slider(min_date, max_date, placement="middle")
    daterange = ui.convert_date_to_range(selected_date, option="")

with col2:
    st.write("Language selection")
    if st.toggle(label="Use Top 10 LR Languages", value=True):
        selected_languages = df_top10["app_language"].to_list()
    else:
        df = users.get_language_list()
        selected_languages = ui.multi_select_all(
            df, placement="middle", title="Select languages", key="fa-1"
        )   

    if (len(selected_languages) > 0):     
        df_user_cohort = metrics.filter_user_data(daterange=daterange,countries_list=countries_list,app="CR",language=selected_languages,stat="LR")

        # All we need is their cr_user_id
        user_cohort_list = df_user_cohort["cr_user_id"]

        # Get superset of  the users up through today
        daterange = [daterange[0],today]

    if (len(selected_languages) == 0 ):  # 40 is an arbitrary choice
        st.markdown(
            """
        :red[Please select one or more languages.  ]
        """
        )
    else:
        start = daterange[0].strftime("%b %d, %Y")
        end = daterange[1].strftime("%b %d, %Y")
        st.write("Timerange: " + start + " to " + end)  
        
tab1, tab2, = st.tabs(["Funnel % by language", "Funnel bar chart totals"])
with tab1:


        with st.spinner("Calculating..."):
            uic.funnel_line_chart_percent(
                languages=selected_languages,
                countries_list=countries_list,
                daterange=daterange,
                user_cohort_list=user_cohort_list
            )

with tab2:
    
    if (
        len(selected_languages) == 0 or len(selected_languages) > 40
    ):  # 40 is an arbitrary choice
        st.markdown(
            """
        :red[Please select one or more languages.  "All" is not an acceptable selection for this chart.]
        """
        )
    else:
        start = daterange[0].strftime("%b %d, %Y")
        end = daterange[1].strftime("%b %d, %Y")
        st.write("Timerange: " + start + " to " + end)
        with st.spinner("Calculating..."):
            uic.funnel_bar_chart(
                languages=selected_languages,
                countries_list=countries_list,
                daterange=daterange
            )

