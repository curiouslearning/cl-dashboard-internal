import streamlit as st
import settings
from millify import prettify
import campaigns
import metrics
import ui_widgets as ui
import ui_components as uic
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
## UI ##
settings.initialize()
settings.init_campaign_data()

ui.display_definitions_table("Campaign Data Notes",data_notes)

rollup = st.toggle("Rollup daily segments",value=True)

df_campaigns_all = st.session_state["df_campaigns_all"]
if rollup:
    df_campaigns_all = campaigns.rollup_campaign_data(df_campaigns_all)

st.header("Facebook Ads")
dff = df_campaigns_all.query("source == 'Facebook'")

if len(dff) > 0:
    keys = [2, 3, 4, 5, 6]
    ui.paginated_dataframe(dff, keys, sort_col="campaign_name")
else:
    st.text("No data for selected period")


st.header("Google Ads")
dfg = df_campaigns_all.query("source == 'Google'")

if len(dfg) > 0:
    keys = [7, 8, 9, 10, 11]
    ui.paginated_dataframe(dfg, keys, sort_col="campaign_name")
else:
    st.text("No data for selected period")

