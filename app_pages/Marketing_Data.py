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
import pandas as pd

data_notes = pd.DataFrame(
    [
        [
            "Campaign segment data",
            "Starting 05/01/2024, campaign names were changed to support an indication of \
             both language and country through a naming convention.  So we are only collecting \
             and reporting on daily campaign segment data from that day forward. "       ],

    ],
    columns=["Note", "Description"],
)
ui.display_definitions_table("Data Notes",data_notes)
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

# In the case of datepicker, don't do anything until both start and end dates are picked
if len(daterange) == 2 and len(countries_list) > 0:

    #Cost calculations can only be reliable after naming conventions were 
    #implemented in May
    daterange[0] = max(daterange[0], dt.datetime(2024, 5, 1).date())
    date_start = daterange[0].strftime("%m-%d-%Y")
    date_end = daterange[1].strftime("%m-%d-%Y")
    st.subheader("General Engagement")
    header = (f"**Selected date range :calendar::    :green[{date_start} to {date_end}]**" )
    st.markdown(header)

    col1, col2, col3 = st.columns(3)

    LR = metrics.get_totals_by_metric(
        daterange, countries_list, stat="LR", language=language
    )
    col1.metric(label="Learners Reached", value=prettify(int(LR)))

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

    df_campaigns_all = st.session_state["df_campaigns_all"]

    df_campaigns = metrics.filter_campaigns(df_campaigns_all,daterange,language,countries_list)

    cost = df_campaigns["cost"].sum()
    col1.metric(label="Cost", value=f"${prettify(int(cost))}")

    col2.metric(label="LRC", value=f"${cost/LR:.2f}" if LR != 0 else "N/A")
    # LR vs LRC chart
    st.divider()

    st.markdown(header)

    df_total_LR_per_month = metrics.get_totals_per_month(daterange,stat="LR",countries_list=countries_list,language=language)
    if len(df_total_LR_per_month) > 0:
        uic.lr_lrc_bar_chart(df_total_LR_per_month)
    st.divider()

    st.subheader("Total Spend per Country")
    st.markdown(header)

    source = ui.ads_platform_selector(placement="middle")     
    if (len(df_campaigns) > 0):
        uic.spend_by_country_map(df_campaigns,source)
    
        st.divider()
        st.subheader("LRC / LAC")
        st.markdown(header)

        c1, c2, c3,c4 = st.columns(4)
        with c1:
            option = st.radio("Select a statistic", ("LRC", "LAC"), index=0, horizontal=True)
        with c2:
            display_category = st.radio(
                "Display by", ("Country", "Language"), index=0, horizontal=True, key="e-4"
            )


            uic.lrc_scatter_chart(option,display_category,df_campaigns,daterange)
        
        st.divider()   
        st.markdown(header)
    
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


