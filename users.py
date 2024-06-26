import streamlit as st
import pandas as pd
from rich import print as print
import numpy as np
from pyinstrument import Profiler


# How far back to obtain user data.  Currently the queries pull back to 01/01/2021
start_date = "2021/01/01"


# Firebase returns two different formats of user_pseudo_id between
# web app events and android events, so we have to run multiple queries
# instead of a join because we don't have a unique key for both
# This would all be unncessery if dev had included the app user id per the spec.
@st.cache_data(ttl="1d", show_spinner="Gathering User List")
def get_users_list():
    #   p = Profiler(async_mode="disabled")
    #   with p:

    bq_client = st.session_state.bq_client
    sql_query = f"""
                SELECT *
                    FROM `dataexploration-193817.user_data.all_users_progress`
                WHERE
                    first_open BETWEEN PARSE_DATE('%Y/%m/%d','{start_date}') AND CURRENT_DATE() 
                """

    df_user_list = bq_client.query(sql_query).to_dataframe()

    df_unity_users = df_user_list[
        df_user_list["app_id"].str.lower().str.contains("feedthemonster")
    ]

    sql_query = f"""
            SELECT *
                FROM `dataexploration-193817.user_data.user_first_open_list_cr`
            WHERE
                first_open BETWEEN PARSE_DATE('%Y/%m/%d','{start_date}') AND CURRENT_DATE() 
            """

    df_cr_users = bq_client.query(sql_query).to_dataframe()

    df_first_open = pd.concat([df_cr_users, df_unity_users], ignore_index=True)

    df_first_open["app_language"] = df_first_open["app_language"].replace(
        "ukranian", "ukrainian"
    )
    df_first_open["app_language"] = df_first_open["app_language"].replace(
        "malgache", "malagasy"
    )
    df_user_list["app_language"] = df_user_list["app_language"].replace(
        "ukranian", "ukrainian"
    )
    df_user_list["app_language"] = df_user_list["app_language"].replace(
        "malgache", "malagasy"
    )

    return df_user_list, df_first_open


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
