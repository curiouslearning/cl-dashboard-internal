import streamlit as st
import pandas as pd
from rich import print as print
import campaigns
from collections import defaultdict


@st.cache_data(show_spinner="Fetching Google Campaign Data", ttl="1d")
def get_google_campaign_data():
    bq_client = st.session_state.bq_client
    sql_query = f"""
        SELECT
        metrics.campaign_id,
        metrics.segments_date as segment_date,
        campaigns.campaign_name,
        0 as mobile_app_install,
        metrics_clicks as clicks,
        metrics_impressions as impressions,
        metrics_cost_micros as cost,
        metrics_average_cpc as cpc,
        campaigns.campaign_start_date,
        campaigns.campaign_end_date, 
        0 as reach,
        "Google" as source
        FROM dataexploration-193817.marketing_data.p_ads_CampaignStats_6687569935 as metrics
        inner join dataexploration-193817.marketing_data.ads_Campaign_6687569935 as campaigns
        on metrics.campaign_id = campaigns.campaign_id
        and campaigns.campaign_start_date >= '2021-01-01'
        group by 1,2,3,4,5,6,7,8,9,10   
    """

    df = bq_client.query(sql_query).to_dataframe()

    df["campaign_id"] = df["campaign_id"].astype(str).str.replace(",", "")
    df["cost"] = df["cost"].divide(1000000).round(2)
    df["cpc"] = df["cpc"].divide(1000000)
    df["segment_date"] = pd.to_datetime(df["segment_date"])
    df["segment_date"] = df["segment_date"].values.astype("datetime64[D]")

    df = df.convert_dtypes()

    return df


@st.cache_data(show_spinner="Fetching Facebook Campaign Data", ttl="1d")
def get_fb_campaign_data():
    bq_client = st.session_state.bq_client
    sql_query = f"""
            SELECT 
            campaign_id,
            data_date_start as segment_date ,
            campaign_name,
            PARSE_NUMERIC(a.value) as mobile_app_install,  
            clicks,
            impressions,
            spend as cost,
            cpc,
            start_time as campaign_start_date, 
            end_time as campaign_end_date,
            reach,
            "Facebook" as source,
            0 as button_clicks,
            FROM dataexploration-193817.marketing_data.facebook_ads_data as d
            JOIN UNNEST(actions) as a
            WHERE a.action_type = 'mobile_app_install'
            and
            d.start_time >= '2021-01-01'
            order by data_date_start desc;

             """

    df = bq_client.query(sql_query).to_dataframe()

    df["campaign_start_date"] = pd.to_datetime(
        df.campaign_start_date, utc=True
    ).dt.strftime("%Y/%m/%d")
    df["campaign_end_date"] = pd.to_datetime(
        df.campaign_end_date, utc=True
    ).dt.strftime("%Y/%m/%d")

    df["segment_date"] = pd.to_datetime(df["segment_date"])
    df["segment_date"] = df["segment_date"].values.astype("datetime64[D]")

    df["mobile_app_install"] = pd.to_numeric(df["mobile_app_install"])

    return df


@st.cache_data(ttl="1d", show_spinner=False)
# Looks for the string following the dash and makes that the associated country.
# This requires a strict naming convention of "[anything without dashes] - [country]]"
def add_country_and_language(df):

    # Define the regex pattern to match campaign names with the format ": text -"
    regex_pattern = r":\s*([^-]+?)\s*-"

    # Filter rows based on the regex pattern
    df1 = df[df["campaign_name"].str.contains(regex_pattern, regex=True, na=False)]

    # Set country to everything after the dash and remove padding
    country_regex_pattern = r"-\s*(.*)"
    df1["country"] = (
        df1["campaign_name"].str.extract(country_regex_pattern)[0].str.strip()
    )

    # Remove the word "Campaign" if it exists
    campaign_regex_pattern = r"\s*(.*)Campaign"
    extracted = df1["country"].str.extract(campaign_regex_pattern)

    # Replace NaN values (no match) with the original values
    df1["country"] = extracted[0].fillna(df1["country"]).str.strip()

    # Set the language based on the pattern
    language_regex_pattern = r":\s*([^-]+?)\s*-"
    df1["app_language"] = (
        df1["campaign_name"].str.extract(language_regex_pattern)[0].str.strip()
    )
    return df1


@st.cache_data(ttl="1d", show_spinner=False)
def get_google_campaign_conversions():
    bq_client = st.session_state.bq_client
    sql_query = f"""
                SELECT campaign_id,
                metrics_conversions as button_clicks,
                FROM `dataexploration-193817.marketing_data.ads_CampaignConversionStats_6687569935`
                where segments_conversion_action_name like '%CTA_Gplay%';
                """

    df = bq_client.query(sql_query).to_dataframe()

    df["campaign_id"] = df["campaign_id"].astype(str).str.replace(",", "")

    return df


# This function takes a campaign based dataframe and sums it up into a single row per campaign.  The original dataframe
# has many entries per campaign based on daily extractions.
def rollup_campaign_data(df):
    aggregation = {
        "segment_date": "last",
        "campaign_start_date": "first",
        "campaign_end_date": "first",
        "mobile_app_install": "sum",
        "source": "first",
        "clicks": "sum",
        "reach": "sum",
        "cost": "sum",
        "cpc": "sum",
        "impressions": "sum",
    }
    optional_columns = ["country", "app_language"]
    for col in optional_columns:
        if col in df.columns:
            aggregation[col] = "first"

    # This will roll everything up except when there is multiple campaign names
    # for a campaign_id.  This happens when campaigns are renamed.
    df = df.groupby(["campaign_id", "campaign_name"], as_index=False).agg(aggregation)

    # find duplicate campaign_ids, create a dataframe for them and remove from original
    duplicates = df[df.duplicated("campaign_id", keep=False)]
    df = df.drop_duplicates("campaign_id", keep=False)

    # Get the newest campaign info according to segment date and use its campaign_name
    # for the other campaign names.
    duplicates = duplicates.sort_values(by="segment_date", ascending=False)

    duplicates["campaign_name"] = duplicates.groupby("campaign_id")[
        "campaign_name"
    ].transform("first")

    # Do another rollup on the duplicates.  This time the campaign name will be the same
    # so we can take any of them
    aggregation = {
        "campaign_name": "first",
        "campaign_start_date": "first",
        "campaign_end_date": "first",
        "mobile_app_install": "first",
        "source": "first",
        "clicks": "first",
        "reach": "first",
        "cost": "first",
        "cpc": "first",
        "impressions": "first",
    }

    combined = duplicates.groupby(["campaign_id"], as_index=False).agg(aggregation)

    # put it all back together
    df = pd.concat([df, combined])

    return df


# Get the button clicks from BigQuery, add them to the dataframe
# and rollup the sum per campaign_id
def add_google_button_clicks(df):

    df_goog_conversions = campaigns.get_google_campaign_conversions()

    df_goog = pd.merge(
        df,
        df_goog_conversions,
        on="campaign_id",
        how="left",
        suffixes=("", ""),
    )

    df_goog = df_goog.groupby("campaign_id", as_index=False).agg(
        {
            "campaign_name": "last",
            "app_language": "first",
            "country": "first",
            "campaign_start_date": "first",
            "campaign_end_date": "first",
            "mobile_app_install": "first",
            "source": "first",
            "button_clicks": "sum",
            "clicks": "first",
            "reach": "first",
            "cost": "first",
            "cpc": "first",
            "impressions": "first",
        }
    )

    return df_goog
