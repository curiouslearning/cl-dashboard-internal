import streamlit as st
import settings
from rich import print
import metrics
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import users
import datetime as dt

ui.display_definitions_table("Data Notes",ui.data_notes)
settings.initialize()
settings.init_user_list()
settings.init_campaign_data()

ui.colorize_multiselect_options()

selected_date, option = ui.calendar_selector()
daterange = ui.convert_date_to_range(selected_date, option)

#Cost calculations can only be reliable after naming conventions were 
#implemented in April
daterange[0] = max(daterange[0], dt.datetime(2024, 4, 1).date())

languages = users.get_language_list()
language = ui.single_selector(
    languages, placement="side", title="Select a language", key="md-1"
)

countries_list = users.get_country_list()
countries_list = ui.multi_select_all(
    countries_list, title="Country Selection", key="md-2"
)
# In the case of datepicker, don't do anything until both start and end dates are picked
if len(daterange) == 2 and len(countries_list) > 0:
    date_start = daterange[0].strftime("%Y-%m-%d")
    date_end = daterange[1].strftime("%Y-%m-%d")
    st.subheader("General Engagement")
    st.markdown("**Selected Range:**")
    st.text(date_start + " to " + date_end)

    col1, col2, col3 = st.columns(3)

    total = metrics.get_totals_by_metric(
        daterange, countries_list, stat="LR", language=language
    )
    col1.metric(label="Learners Reached", value=prettify(int(total)))

    total = metrics.get_totals_by_metric(
        daterange, countries_list, "LA",  language=language
    )
    col2.metric(label="Learners Acquired", value=prettify(int(total)))

    total = metrics.get_totals_by_metric(
        daterange, countries_list, "RA",  language=language
    )
    col3.metric(label="Readers Acquired", value=prettify(int(total)))


    total = metrics.get_totals_by_metric(
        daterange, countries_list, "GC",  language=language
    )
    col1.metric(label="Games Completed", value=prettify(int(total)))

    total = metrics.get_GPP_avg(daterange, countries_list,  language=language)
    col2.metric(label="Game Progress Percent", value=f"{total:.2f}%")

    total = metrics.get_GC_avg(daterange, countries_list, language=language)
    col3.metric(label="Game Completion Avg", value=f"{total:.2f}%")

    df_campaigns = metrics.filter_campaigns(daterange,language,countries_list)
    cost = df_campaigns["cost"].sum()
    col1.metric(label="Cost", value=f"${prettify(int(cost))}")

    st.divider()
