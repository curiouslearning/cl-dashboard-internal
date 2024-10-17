import streamlit as st
import settings
from rich import print
import metrics
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import users
import datetime as dt
import campaigns

ui.display_definitions_table("Data Notes",ui.data_notes)
settings.initialize()
settings.init_user_list()
settings.init_campaign_data()

ui.colorize_multiselect_options()


languages = users.get_language_list()
language = ui.single_selector(
    languages, title="Select a language", placement="side", key="e-1"
)

countries_list = users.get_country_list()
countries_list = ui.multi_select_all(
    countries_list, title="Country Selection", key="e-2"
)

selected_date, option = ui.calendar_selector()
daterange = ui.convert_date_to_range(selected_date, option)

#Cost calculations can only be reliable after naming conventions were 
#implemented in April
daterange[0] = max(daterange[0], dt.datetime(2024, 4, 1).date())

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
    st.subheader("Total Spend per Country")
    source = ui.ads_platform_selector(placement="middle")       
    uic.spend_by_country_map(df_campaigns,source)
    
    st.divider()
    st.subheader("LRC / LAC")
    c1, c2, c3,c4 = st.columns(4)
    with c1:
        option = st.radio("Select a statistic", ("LRC", "LAC"), index=0, horizontal=True)
    with c2:
        display_category = st.radio(
            "Display by", ("Country", "Language"), index=0, horizontal=True, key="e-4"
        )

    uic.lrc_scatter_chart(option,display_category,df_campaigns,daterange)
    
    st.divider()    
    col = df_campaigns.pop("country")
    df_campaigns.insert(2, col.name, col)
    df_campaigns.reset_index(drop=True, inplace=True)

    col = df_campaigns.pop("app_language")
    df_campaigns.insert(3, col.name, col)
    df_campaigns.reset_index(drop=True, inplace=True)

    st.subheader("Marketing metrics table")
    df = campaigns.build_campaign_table(df_campaigns, daterange)
    keys = [12, 13, 14, 15, 16]
    ui.paginated_dataframe(df, keys, sort_col="country")


    
    st.divider()