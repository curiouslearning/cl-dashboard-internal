import streamlit as st
import pandas as pd
from rich import print as print
import asyncio
from pyinstrument import Profiler
import settings
import metrics

start_date = '2024-05-01'
# Starting 05/01/2024, campaign names were changed to support an indication of 
# both language and country through a naming convention.  So we are only collecting
# and reporting on daily campaign segment data from that day forward.

# Combined function to fetch Google and Facebook campaign data concurrently

async def get_campaign_data():
    p = Profiler(async_mode="disabled")
    with p:
        _, bq_client = settings.get_gcp_credentials()

        # Helper function to run BigQuery queries asynchronously
        async def run_query(query):
            return await asyncio.to_thread(bq_client.query(query).to_dataframe)

        # Google Ads Query
        google_ads_query = f"""
            SELECT
                metrics.campaign_id,
                metrics.segments_date as segment_date,
                campaigns.campaign_name,
                metrics_cost_micros as cost,
                campaigns.campaign_start_date,
                "Google" as source
            FROM dataexploration-193817.marketing_data.p_ads_CampaignStats_6687569935 as metrics
            INNER JOIN dataexploration-193817.marketing_data.ads_Campaign_6687569935 as campaigns
            ON metrics.campaign_id = campaigns.campaign_id
            AND metrics.segments_date >= '{start_date}'
           GROUP BY 1,2,3,4,5
        """

        # Facebook Ads Query
        facebook_ads_query = f"""
            SELECT 
                d.campaign_id,
                d.data_date_start as segment_date,
                d.campaign_name,
                d.spend as cost,
                d.start_time as campaign_start_date, 
                "Facebook" as source
            FROM dataexploration-193817.marketing_data.facebook_ads_data as d
            WHERE d.data_date_start >= '{start_date}'
            ORDER BY d.data_date_start DESC;
        """

        # Run both queries concurrently using asyncio.gather
        google_ads_data, facebook_ads_data = await asyncio.gather(
            run_query(google_ads_query),
            run_query(facebook_ads_query)
        )

        # Process Google Ads Data
        google_ads_data["campaign_id"] = google_ads_data["campaign_id"].astype(str).str.replace(",", "")
        google_ads_data["cost"] = google_ads_data["cost"].divide(1000000).round(2)
  #      google_ads_data["segment_date"] = pd.to_datetime
        google_ads_data["segment_date"] = pd.to_datetime(google_ads_data["segment_date"])
    p.print(color="red")
    return google_ads_data, facebook_ads_data

@st.cache_data(ttl="1d", show_spinner=False)
# Looks for the string following the dash and makes that the associated country.
# This requires a strict naming convention of "[anything without dashes] - [country]]"
def add_country_and_language(df):

    # Define the regex patterns
    country_regex_pattern = r"-\s*(.*)"
    language_regex_pattern = r":\s*([^-]+?)\s*-"
    campaign_regex_pattern = r"\s*(.*)Campaign"

    # Extract the country
    df["country"] = (
        df["campaign_name"].str.extract(country_regex_pattern)[0].str.strip()
    )

    # Remove the word "Campaign" if it exists in the country field
    extracted = df["country"].str.extract(campaign_regex_pattern)
    df["country"] = extracted[0].fillna(df["country"]).str.strip()

    # Extract the language
    df["app_language"] = (
        df["campaign_name"].str.extract(language_regex_pattern)[0].str.strip()
    )

    # Set default values to None where there's no match
    country_contains_pattern = r"-\s*(?:.*)"
    language_contains_pattern = r":\s*(?:[^-]+?)\s*-"

    df["country"] = df["country"].where(
        df["campaign_name"].str.contains(
            country_contains_pattern, regex=True, na=False
        ),
        None,
    )
    df["app_language"] = df["app_language"].where(
        df["campaign_name"].str.contains(
            language_contains_pattern, regex=True, na=False
        ),
        None,
    ).str.lower()

    return df


# This function takes a campaign based dataframe and sums it up into a single row per campaign.  The original dataframe
# has many entries per campaign based on daily extractions.
def rollup_campaign_data(df):
    aggregation = {
        "segment_date": "last",
        "campaign_start_date": "first",
        "source": "first",
        "cost": "sum",
    }
    optional_columns = ["country", "app_language"]
    for col in optional_columns:
        if col in df.columns:
            aggregation[col] = "first"

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
    aggregation["campaign_name"] = "first"
    combined = duplicates.groupby(["campaign_id"], as_index=False).agg(aggregation)

    # put it all back together
    df = pd.concat([df, combined])
    df = df.drop(columns=["segment_date"])

    return df


@st.cache_data(ttl="1d", show_spinner=True)
def build_campaign_table(df_campaigns, session_df, daterange):
    """
    df_campaigns: DataFrame with columns ['country', 'app_language', 'cost', ...]
    session_df: the user cohort DataFrame (already filtered for daterange, apps, etc)
    daterange: (start, end) date tuple for filtering

    Returns: DataFrame with metrics for each (country, app_language) group
    """
    # 1. Get all unique country/language pairs in campaign data
    group_cols = ["country", "app_language"]
    group_keys = df_campaigns[group_cols].drop_duplicates().values.tolist()

    rows = []
    for country, app_language in group_keys:
        # 2. Filter user data for this group (and current date range)
        cohort_df = metrics.get_user_cohort_df(
            session_df=session_df,
            daterange=daterange,
            countries_list=[country],
            languages=[app_language],
            app=None
        )
        # 3. Metrics for this group
        LR = metrics.get_cohort_totals_by_metric(cohort_df, stat="LR")
        PC = metrics.get_cohort_totals_by_metric(cohort_df, stat="PC")
        LA = metrics.get_cohort_totals_by_metric(cohort_df, stat="LA")
        RA = metrics.get_cohort_totals_by_metric(cohort_df, stat="RA")
        # 4. Total cost for this country/lang (can groupby sum if multiple campaigns per group)
        cost = df_campaigns[
            (df_campaigns["country"] == country) &
            (df_campaigns["app_language"] == app_language)
        ]["cost"].sum()
        # 5. Calculate cost-per-metric and conversion rates
        row = {
            "country": country,
            "app_language": app_language,
            "cost": cost,
            "LR": LR,
            "PC": PC,
            "LA": LA,
            "RA": RA,
            "LRC": (cost / LR) if LR else 0,
            "PCC": (cost / PC) if PC else 0,
            "LAC": (cost / LA) if LA else 0,
            "RAC": (cost / RA) if RA else 0,
            "PC_LR %": (PC / LR * 100) if LR else 0,
            "LA_LR %": (LA / LR * 100) if LR else 0,
            "RA_LR %": (RA / LR * 100) if LR else 0,
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    # Optional: round currency columns
    for col in ["LRC", "PCC", "LAC", "RAC"]:
        df[col] = df[col].round(2)
    for col in ["PC_LR %", "LA_LR %", "RA_LR %"]:
        df[col] = df[col].round(2)
    df[["cost", "LR", "PC", "LA", "RA"]] = df[["cost", "LR", "PC", "LA", "RA"]].fillna(0)
    return df

