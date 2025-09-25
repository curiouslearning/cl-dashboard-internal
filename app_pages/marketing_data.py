import streamlit as st
from rich import print
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import datetime as dt
import campaigns
import pandas as pd
from metrics import filter_campaigns,get_totals_per_month_from_cohort,get_all_apps_combined_session_and_cohort_df,get_user_cohort_df,get_cohort_totals_by_metric,get_cohort_GC_avg,get_cohort_GPP_avg
from users import ensure_user_data_initialized,get_language_list,get_country_list
from settings import initialize,init_campaign_data
from users import ensure_user_data_initialized


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

ui.display_definitions_table("Data Notes", data_notes)

initialize()
ensure_user_data_initialized()
init_campaign_data()

ui.colorize_multiselect_options()

languages = get_language_list()

with st.sidebar:
    language = ui.single_selector_new(
        languages, title="Select a language", key="e-1"
    )

    countries_list = get_country_list()
    countries_list = ui.multi_select_all_new(
        countries_list, title="Country Selection", key="e-2"
    )

    selected_date, option = ui.calendar_selector_new()
    daterange = ui.convert_date_to_range(selected_date, option)

apps = ui.get_apps()

# In the case of datepicker, don't do anything until both start and end dates are picked
if len(daterange) == 2 and len(countries_list) > 0:

    # Cost calculations can only be reliable after naming conventions were 
    # implemented in May
    daterange[0] = max(daterange[0], dt.datetime(2024, 5, 1).date())
    date_start = daterange[0].strftime("%m-%d-%Y")
    date_end = daterange[1].strftime("%m-%d-%Y")
    st.subheader("General Engagement: All Apps")
    header = (f"**Selected date range :calendar::    :green[{date_start} to {date_end}]**" )
    st.markdown(header)

    col1, col2, col3 = st.columns(3)
    
    #******* LR *******
    session_df = get_all_apps_combined_session_and_cohort_df(
        stat="LR"
    )

    cohort_df = get_user_cohort_df(
        session_df=session_df,
        daterange=daterange,
        languages=language,
        countries_list=countries_list,
        )

    LR = get_cohort_totals_by_metric(cohort_df=cohort_df, stat="LR")
    col1.metric(label="Learners Reached", value=prettify(int(LR)))
    
    #******* LA *******
    session_df = get_all_apps_combined_session_and_cohort_df(
        stat="LA"
    )

    cohort_df = get_user_cohort_df(
        session_df=session_df,
        daterange=daterange,
        languages=language,
        countries_list=countries_list,
        )

    LA = get_cohort_totals_by_metric(cohort_df=cohort_df, stat="LA")
    col2.metric(label="Learners Acquired", value=prettify(int(LA)))

    RA = get_cohort_totals_by_metric(cohort_df=cohort_df, stat="RA")
    col3.metric(label="Readers Acquired", value=prettify(int(RA)))

    GC = get_cohort_totals_by_metric(cohort_df=cohort_df, stat="GC")
    col1.metric(label="Games Completed", value=prettify(int(GC)))

    GPP = get_cohort_GPP_avg(cohort_df)
    col2.metric(label="Game Progress Percent", value=f"{GPP:.2f}%")

    #******* GCC_AVG *******

    GC_AVG = get_cohort_GC_avg(cohort_df)
    col3.metric(label="Game Completion Avg", value=f"{GC_AVG:.2f}%")

    df_campaigns_all = st.session_state["df_campaigns_all"]
    df_campaigns = filter_campaigns(df_campaigns_all, daterange, language, countries_list)

    cost = df_campaigns["cost"].sum()
    col1.metric(label="Cost", value=f"${prettify(int(cost))}")

    col2.metric(label="LRC", value=f"${cost/LR:.2f}" if LR != 0 else "N/A")
    col3.metric(label="RAC", value=f"${cost/RA:.2f}" if RA != 0 else "N/A")
    
    csv = ui.convert_for_download(cohort_df) 
    col3.download_button(
            label="Download",
            data=csv,
            file_name="user_cohort.csv",
            key="md1",
            icon=":material/download:",
            mime="text/csv",
        )
    
    #**** LR vs LRC chart ****
    st.divider()
    st.markdown(header)
    session_df = get_all_apps_combined_session_and_cohort_df(
        stat="LR"
    )
    
    df_total_LR_per_month = get_totals_per_month_from_cohort(cohort_df=session_df, stat="LR", daterange=daterange)
    if len(df_total_LR_per_month) > 0:
        uic.lr_lrc_bar_chart(df_total_LR_per_month)
        
    csv = ui.convert_for_download(df_total_LR_per_month) 
    st.download_button(
            label="Download",
            data=csv,
            file_name="user_cohort.csv",
            key="md2",
            icon=":material/download:",
            mime="text/csv",
        )
    st.divider()

    st.subheader("Total Spend per Country")
    st.markdown(header)

    source = ui.ads_platform_selector()     

    df = uic.spend_by_country_map(df_campaigns, source)

    csv = ui.convert_for_download(df) 
    st.download_button(
            label="Download",
            data=csv,
            file_name="user_cohort.csv",
            key="md3",
            icon=":material/download:",
            mime="text/csv",
        )
    
    st.divider()
    st.subheader("LRC / LAC: : All apps")
    st.markdown(header)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        option = st.radio("Select a statistic", ("LRC", "LAC"), index=0, horizontal=True)
    with c2:
        display_category = st.radio(
            "Display by", ("Country", "Language"), index=0, horizontal=True, key="e-4"
        )

    session_df = get_all_apps_combined_session_and_cohort_df(
        stat="LR"
        )

    scatter_df = uic.lrc_scatter_chart(
        option=option,
        display_category=display_category,
        df_campaigns=df_campaigns,
        daterange=daterange,
        session_df=session_df,
        languages=language,
        countries_list=countries_list,
    )

    csv = ui.convert_for_download(scatter_df) 
    st.download_button(
            label="Download",
            data=csv,
            file_name="user_cohort.csv",
            key="md4",
            icon=":material/download:",
            mime="text/csv",
        )
        
    st.divider()   
    st.markdown(header)
    
    col = df_campaigns.pop("country")
    df_campaigns.insert(2, col.name, col)
    df_campaigns.reset_index(drop=True, inplace=True)

    col = df_campaigns.pop("app_language")
    df_campaigns.insert(3, col.name, col)
    df_campaigns.reset_index(drop=True, inplace=True)

    st.subheader("Marketing metrics table: : All apps")
    df_campaign_table = campaigns.build_campaign_table(df_campaigns, session_df, daterange)

    keys = [12, 13, 14, 15, 16]
    ui.paginated_dataframe(df_campaign_table, keys, sort_col="country")
