import streamlit as st
import pandas as pd
from rich import print as print
import numpy as np
from pyinstrument import Profiler
import logging
import asyncio

# How far back to obtain user data.  Currently the queries pull back to 01/01/2021
start_date = "2021/01/01"

# Firebase returns two different formats of user_pseudo_id between
# web app events and android events, so we have to run multiple queries
# instead of a join because we don't have a unique key for both
# This would all be unncessery if dev had included the app user id per the spec.


import logging
import streamlit as st

async def get_users_list():
    p = Profiler(async_mode="disabled")
    with p:

        bq_client = st.session_state.bq_client

        # Helper function to run BigQuery in a thread
        async def run_query(query):
            return await asyncio.to_thread(bq_client.query(query).to_dataframe)

        # Define the queries
        sql_unity_users = f"""
            SELECT *
            FROM `dataexploration-193817.user_data.unity_user_progress`
            WHERE first_open BETWEEN PARSE_DATE('%Y/%m/%d','{start_date}') AND CURRENT_DATE()
        """
        sql_cr_first_open = f"""
            SELECT *
            FROM `dataexploration-193817.user_data.cr_first_open`
            WHERE first_open BETWEEN PARSE_DATE('%Y/%m/%d','{start_date}') AND CURRENT_DATE()
        """
        sql_cr_users = f"""
            SELECT *
            FROM `dataexploration-193817.user_data.cr_user_progress`
            WHERE first_open BETWEEN PARSE_DATE('%Y/%m/%d','{start_date}') AND CURRENT_DATE()
        """
        sql_cr_app_launch = f"""
            SELECT *
            FROM `dataexploration-193817.user_data.cr_app_launch`
            WHERE first_open BETWEEN PARSE_DATE('%Y/%m/%d','{start_date}') AND CURRENT_DATE()
        """

        # Run all the queries asynchronously
        df_unity_users, df_cr_first_open, df_cr_users, df_cr_app_launch = await asyncio.gather(
            run_query(sql_unity_users),
            run_query(sql_cr_first_open),
            run_query(sql_cr_users),
            run_query(sql_cr_app_launch),
        )

        # Eliminate duplicate cr users (multiple language combinations) - just keep the first one
        df_cr_app_launch = df_cr_app_launch.drop_duplicates(subset='user_pseudo_id', keep="first")

        # Fix data typos
        df_cr_app_launch["app_language"] = df_cr_app_launch["app_language"].replace(
            "ukranian", "ukrainian"
        )
        df_cr_app_launch["app_language"] = df_cr_app_launch["app_language"].replace(
            "malgache", "malagasy"
        )
        df_cr_users["app_language"] = df_cr_users["app_language"].replace(
            "ukranian", "ukrainian"
        )
        df_cr_users["app_language"] = df_cr_users["app_language"].replace(
            "malgache", "malagasy"
        )
        df_unity_users["app_language"] = df_unity_users["app_language"].replace(
            "ukranian", "ukrainian"
        )
        df_unity_users["app_language"] = df_unity_users["app_language"].replace(
            "malgache", "malagasy"
        )
        
        missing_users = df_cr_users[~df_cr_users["cr_user_id"].isin(df_cr_app_launch["cr_user_id"])]
        print(f"Users in df_funnel but missing from df_app_launch: {missing_users['cr_user_id'].nunique()}")
        missing_users.to_csv("missing.csv")
        print (f"Before clean: df_cr_app_launch = {len(df_cr_app_launch)}, df_cr_users =  {len(df_cr_users)}" )
        df_cr_app_launch,df_cr_users = clean_users_to_single_language(df_cr_app_launch,df_cr_users)
        print (f"After clean: df_cr_app_launch = {len(df_cr_app_launch)}, df_cr_users =  {len(df_cr_users)}" )

        max_level_indices_unity = df_unity_users.groupby('user_pseudo_id')['max_user_level'].idxmax()
        df_unity_users = df_unity_users.loc[max_level_indices_unity].reset_index()

    p.print(color="red")
    


    return df_cr_users, df_unity_users, df_cr_first_open, df_cr_app_launch


@st.cache_data(ttl="1d", show_spinner=False)
def get_language_list():
    lang_list = ["All"]
    if "bq_client" in st.session_state:
        bq_client = st.session_state.bq_client
        sql_query = f"""
                    SELECT display_language
                    FROM `dataexploration-193817.user_data.language_max_level`
                    ;
                    """
        rows_raw = bq_client.query(sql_query)
        rows = [dict(row) for row in rows_raw]
        if len(rows) == 0:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        df.drop_duplicates(inplace=True)
        lang_list = np.array(df.values).flatten().tolist()
        lang_list = [x.strip(" ") for x in lang_list]
    return lang_list


@st.cache_data(ttl="1d", show_spinner=False)
def get_country_list():
    countries_list = []
    if "bq_client" in st.session_state:
        bq_client = st.session_state.bq_client
        sql_query = f"""
                    SELECT *
                    FROM `dataexploration-193817.user_data.active_countries`
                    order by country asc
                    ;
                    """
        rows_raw = bq_client.query(sql_query)
        rows = [dict(row) for row in rows_raw]
        if len(rows) == 0:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        countries_list = np.array(df.values).flatten().tolist()
    return countries_list


@st.cache_data(ttl="1d", show_spinner=False)
def get_app_version_list():
    app_versions = []
    if "bq_client" in st.session_state:
        bq_client = st.session_state.bq_client
        sql_query = f"""
                    SELECT *
                    FROM `dataexploration-193817.user_data.cr_app_versions`
                    """
        rows_raw = bq_client.query(sql_query)
        rows = [dict(row) for row in rows_raw]
        if len(rows) == 0:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        conditions = [
            f"app_version >=  'v1.0.25'",
        ]
        query = " and ".join(conditions)
        df = df.query(query)

        app_versions = np.array(df.values).flatten().tolist()
        app_versions.insert(0, "All")

    return app_versions


@st.cache_data(ttl="1d", show_spinner=False)
def get_funnel_snapshots(daterange,languages):

    if "bq_client" in st.session_state:
        bq_client = st.session_state.bq_client
    else:
        st.write ("No database connection")
        return

    languages_str = ', '.join([f"'{lang}'" for lang in languages])

    sql_query = f"""
            SELECT *
            FROM `dataexploration-193817.user_data.funnel_snapshots`
            WHERE language IN ({languages_str})
            AND
            DATE(date) BETWEEN '{daterange[0].strftime("%Y-%m-%d")}' AND '{daterange[1].strftime("%Y-%m-%d")}' ;

            """

    df = bq_client.query(sql_query).to_dataframe() 
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    return df

# Users who play multiple languages or have multiple countries are consolidated
# to a single entry based on which combination took them the furthest in the game.
# If its a tie, will take the first entry.

def clean_users_to_single_language(df_app_launch, df_funnel):
    
    # ✅ Step 1: Filter to only 'tsonga' or 'afrikaans'
    df_app_launch = df_app_launch[df_app_launch["app_language"].isin(["tsonga", "afrikaans"])]
    df_funnel = df_funnel[df_funnel["app_language"].isin(["tsonga", "afrikaans"])]
    
    missing_users = df_funnel[~df_funnel["cr_user_id"].isin(df_app_launch["cr_user_id"])]
    print(f"Users in df_funnel but missing from df_app_launch: {missing_users['cr_user_id'].nunique()}")

    
    
    print(f"Before clean: df_cr_app_launch = {df_app_launch.shape[0]}, df_cr_users = {df_funnel.shape[0]}")

    # ✅ Step 2: Identify and remove all duplicates from df_app_launch, but SAVE them
    duplicate_user_ids = df_app_launch[df_app_launch.duplicated(subset='cr_user_id', keep=False)]
    
    print("Before duplicate removal:", df_app_launch.shape)
    df_app_launch = df_app_launch[~df_app_launch["cr_user_id"].isin(duplicate_user_ids["cr_user_id"])]
    print("After duplicate removal:", df_app_launch.shape)

    # ✅ Step 3: Get list of users that had duplicates
    unique_duplicate_ids = duplicate_user_ids['cr_user_id'].unique().tolist()

    # ✅ Step 4: Define event ranking
    event_order = ["download_completed", "tapped_start", "selected_level", "puzzle_completed", "level_completed"]
    event_rank = {event: rank for rank, event in enumerate(event_order)}

    # ✅ Step 5: Ensure "furthest_event" has no missing values
    df_funnel["furthest_event"] = df_funnel["furthest_event"].fillna("unknown")

    # ✅ Step 6: Map event to numeric rank
    df_funnel["event_rank"] = df_funnel["furthest_event"].map(event_rank)

    # ✅ Step 7: Flag whether event is "level_completed"
    df_funnel["is_level_completed"] = df_funnel["furthest_event"] == "level_completed"

    # ✅ Step 8: Find the best progress per user
    level_completed_users = df_funnel[df_funnel["is_level_completed"]]
    max_level_idx = level_completed_users.groupby("cr_user_id")["max_user_level"].idxmax()

    other_users = df_funnel[~df_funnel["is_level_completed"]]
    max_event_idx = other_users.groupby("cr_user_id")["event_rank"].idxmax()

    # ✅ Step 9: Merge both selections and clean NaN indices
    best_progress_idx = pd.concat([max_level_idx, max_event_idx]).dropna().astype(int)

    # ✅ Step 10: Keep only the best row per user in df_funnel
    df_funnel = df_funnel.loc[best_progress_idx]

    # ✅ Step 11: Remove duplicate cr_user_id values from df_funnel
    df_funnel = df_funnel.drop_duplicates(subset="cr_user_id", keep="first")

    # ✅ Step 12: Add back the correct user rows in df_app_launch
    users_to_add_back = duplicate_user_ids[duplicate_user_ids["cr_user_id"].isin(unique_duplicate_ids)]
    
    df_app_launch = pd.concat([df_app_launch, users_to_add_back])

    # ✅ Step 13: Ensure df_app_launch has only unique cr_user_id
    df_app_launch = df_app_launch.drop_duplicates(subset="cr_user_id", keep="first")

    # ✅ Step 14: Final debugging checks
    df_app_launch = df_app_launch[df_app_launch["app_language"].isin(["tsonga"])]
    df_funnel = df_funnel[df_funnel["app_language"].isin(["tsonga"])]
    print("Duplicate cr_user_id count in df_funnel:", df_funnel["cr_user_id"].duplicated().sum())
    print("Duplicate cr_user_id count in df_app_launch:", df_app_launch["cr_user_id"].duplicated().sum())

    print(f"After clean: df_cr_app_launch = {df_app_launch.shape[0]}, df_cr_users = {df_funnel.shape[0]}")
    

    df_app_launch.to_csv("app_launch.csv")
    df_app_launch.to_csv("df_cr_users.csv")
    return df_app_launch, df_funnel



