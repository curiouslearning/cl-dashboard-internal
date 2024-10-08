import streamlit as st
import settings
from millify import prettify
import campaigns

import ui_widgets as ui


## UI ##
settings.initialize()
settings.init_campaign_data()
settings.init_user_list()


col1, col2, col3 = st.columns(3)
with col1:
    selected_date, option = ui.calendar_selector(placement="middle", key="fh-3", index=0)
    daterange = ui.convert_date_to_range(selected_date, option)

# In the case of datepicker, don't do anything until both start and end dates are picked
if len(daterange) > 1:
    df_campaigns = campaigns.get_campaigns_by_date(daterange)

    # Drop the campaigns that don't meet the naming convention
    condition = (df_campaigns["app_language"].isna()) | (df_campaigns["country"].isna())
    df_campaigns = df_campaigns[~condition]

    col = df_campaigns.pop("country")
    df_campaigns.insert(2, col.name, col)
    df_campaigns.reset_index(drop=True, inplace=True)

    col = df_campaigns.pop("app_language")
    df_campaigns.insert(3, col.name, col)
    df_campaigns.reset_index(drop=True, inplace=True)

    st.header("Marketing Performance Table")
    df = campaigns.build_campaign_table(df_campaigns, daterange)
    keys = [12, 13, 14, 15, 16]
    ui.paginated_dataframe(df, keys, sort_col="country")

    dff = df_campaigns.query("source == 'Facebook'")

    if len(dff) > 0:
        keys = [2, 3, 4, 5, 6]
        ui.paginated_dataframe(dff, keys, sort_col="campaign_name")
    else:
        st.text("No data for selected period")


    st.header("Google Ads")
    dfg = df_campaigns.query("source == 'Google'")

    if len(dfg) > 0:
        keys = [7, 8, 9, 10, 11]
        dfg.sort_values(by="button_clicks")
        ui.paginated_dataframe(dfg, keys, sort_col="campaign_name")
    else:
        st.text("No data for selected period")
