import streamlit as st
from rich import print
import pandas as pd
import numpy as np
import datetime as dt


default_daterange = [dt.datetime(2021, 1, 1).date(), dt.date.today()]


@st.cache_data(ttl="1d", show_spinner=False)
def get_cohort_totals_by_metric(
    cohort_df,
    stat="LR"
):
    """
    Given a cohort_df (already filtered!), count users in each funnel stage or apply stat-specific filter.
    - cohort_df: DataFrame, filtered to your user cohort (one row per user)
    - stat: string, which funnel metric to count ("LR", "DC", "TS", "SL", "PC", "LA", "RA", "GC")
    """

    if cohort_df.empty:
        return 0

    # Stat-specific filters (formerly in filter_user_data)
    if stat == "LA":
        # Learners Acquired: max_user_level >= 1
        return (cohort_df['max_user_level'] >= 1).sum()
    elif stat == "RA":
        # Readers Acquired: max_user_level >= 25
        return (cohort_df['max_user_level'] >= 25).sum()
    elif stat == "GC":
        # Game Completed: max_user_level >= 1 AND gpc >= 90
        return ((cohort_df['max_user_level'] >= 1) & (cohort_df['gpc'] >= 90)).sum()
    elif stat == "LR":
        # Learner Reached: all users in cohort
        return len(cohort_df)

    # Otherwise: classic funnel by furthest_event
    furthest = cohort_df["furthest_event"]

    download_completed_count = (furthest == "download_completed").sum()
    tapped_start_count      = (furthest == "tapped_start").sum()
    selected_level_count    = (furthest == "selected_level").sum()
    puzzle_completed_count  = (furthest == "puzzle_completed").sum()
    level_completed_count   = (furthest == "level_completed").sum()

    if stat == "DC":
        return (
            download_completed_count
            + tapped_start_count
            + selected_level_count
            + puzzle_completed_count
            + level_completed_count
        )
    if stat == "TS":
        return (
            tapped_start_count
            + selected_level_count
            + puzzle_completed_count
            + level_completed_count
        )
    if stat == "SL":
        return (
            selected_level_count
            + puzzle_completed_count
            + level_completed_count
        )
    if stat == "PC":
        return (
            puzzle_completed_count
            + level_completed_count
        )

    return 0  # default fallback

# Takes the complete user lists (cr_user_id) and filters based on input data, and returns
# a new filtered dataset
def filter_user_data(
    daterange=default_daterange,
    countries_list=["All"],
    cr_app_versions=["All"],
    stat="LR",
    app=["CR"],
    language=["All"],
    user_list=None,
    offline_filter=None
):
    # Check if necessary dataframes are available
    if not all(key in st.session_state for key in ["df_cr_users", "df_unity_users",  "df_cr_app_launch"]):
        print("PROBLEM!")
        return pd.DataFrame()

    # Select the appropriate dataframe and user_list_key
    df, user_list_key = select_user_dataframe(app, stat, st.session_state)

    # Initialize a boolean mask
    mask = (
        df["first_open"] >= pd.to_datetime(daterange[0])
    ) & (
        df["first_open"] <= pd.to_datetime(daterange[1])
    )

    if "All" not in cr_app_versions and app == "CR":
        mask &= df["app_version"].isin(cr_app_versions)
    
    # Apply country filter if not "All"
    if countries_list[0] != "All":
        mask &= df['country'].isin(set(countries_list))

    # Apply language filter if not "All" 
    if language[0] != "All":
        mask &= df['app_language'].isin(set(language))
  
    # Apply started_in_offline_mode filter if not None
    if offline_filter is not None:
        if offline_filter is True:
            mask &= df["started_in_offline_mode"] == True
        else:  # offline_filter is False
            mask &= df["started_in_offline_mode"] != True

    # Apply stat-specific filters
    if stat == "LA":
        mask &= (df['max_user_level'] >= 1)
    elif stat == "RA":
        mask &= (df['max_user_level'] >= 25)
    elif stat == "GC":  # Game completed
        mask &= (df['max_user_level'] >= 1) & (df['gpc'] >= 90)
    elif stat == "LR":
        pass  # No additional filters for these stats beyond daterange and optional countries/language

    # Filter the dataframe with the combined mask 
    df = df.loc[mask]

    # If user list subset was passed in, filter on that as well
    if user_list is not None:
        if len(user_list) == 0:
            return pd.DataFrame()  # No matches — return empty
        df = df[df[user_list_key].isin(user_list)]

    return df

def select_user_dataframe(app, stat, session_state):
    """
    Returns the correct dataframe based on app(s) and stat.
    - app: str or list of str (single app or multiple apps)
    - stat: string ('LR', etc.)
    - session_state: Streamlit session_state
    """
    # Always treat app as a list for logic
    apps = [app] if isinstance(app, str) else app

    # Unity (if selected among apps)
    if "Unity" in apps:
        df = session_state.df_unity_users
        user_list_key = "user_pseudo_id"
        return df, user_list_key

    # Any -standalone
    elif any(a.endswith("-standalone") for a in apps if isinstance(a, str)):
        df = session_state.df_cr_users
        # Only filter if not "All" (defensive)
        if "All" not in apps:
            df = df[df["app"].isin(apps)]
        user_list_key = "cr_user_id"
        return df, user_list_key

    # CR special case (only CR selected and stat == "LR")
    elif apps == ["CR"] and stat == "LR":
        df = session_state.df_cr_app_launch
        user_list_key = "cr_user_id"
        return df, user_list_key

    # All other cases: general CR users table
    else:
        df = session_state.df_cr_users
        user_list_key = "cr_user_id"
        return df, user_list_key

def select_user_dataframe_new(app, stat=None):
    apps = [app] if isinstance(app, str) else app

    if "Unity" in apps:
        df = st.session_state.df_unity_users
        return df

    elif any(a.endswith("-standalone") for a in apps if isinstance(a, str)):
        df = st.session_state.df_cr_users
        if "All" not in apps:
            df = df[df["app"].isin(apps)]
        return df

    elif apps == ["CR"] and stat == "LR":
        df = st.session_state.df_cr_app_launch
        return df

    else:
        df = st.session_state.df_cr_users
        return df


@st.cache_data(ttl="1d", show_spinner=False)
def get_cohort_GPP_avg(cohort_df):
    """
    Calculates average 'gpc' for the LA cohort only (furthest_event == 'level_completed').
    Returns 0 if no such users.
    """
    if cohort_df.empty:
        return 0
    la_df = cohort_df[cohort_df["furthest_event"] == "level_completed"]
    if la_df.empty:
        return 0
    return np.average(la_df["gpc"].fillna(0))


@st.cache_data(ttl="1d", show_spinner=False)
def get_cohort_GC_avg(cohort_df):
    """
    Returns the percentage of LA users (furthest_event == 'level_completed') with gpc >= 90.
    """
    if cohort_df.empty:
        return 0
    la_df = cohort_df[cohort_df["furthest_event"] == "level_completed"]
    if la_df.empty:
        return 0
    gpc = la_df["gpc"].fillna(0)
    gc_count = (gpc >= 90).sum()
    la_count = len(la_df)
    return gc_count / la_count * 100


def weeks_since(daterange):
    current_date = dt.datetime.now()
    daterange_datetime = dt.datetime.combine(daterange[0], dt.datetime.min.time())

    difference = current_date - daterange_datetime

    return difference.days // 7


# Returns a DataFrame list of counts by language or counts by country

@st.cache_data(ttl="1d", show_spinner=False)
def get_counts(
    type="app_language",
    daterange=default_daterange,
    countries_list=["All"],
    app=["CR"],
    language=["All"],
    user_list=None
):
    dfLR = (
        filter_user_data(
            daterange=daterange, countries_list=countries_list, stat="LR", app=app, language=language,user_list=user_list
        )
        .groupby(type)
        .size()
        .to_frame(name="LR")
        .reset_index()
    )
    dfLA = (
        filter_user_data(daterange=daterange, countries_list=countries_list, stat="LA", app=app, language=language,user_list=user_list)
        .groupby(type)
        .size()
        .to_frame(name="LA")
        .reset_index()
    )    
    dfRA = (
        filter_user_data(daterange=daterange, countries_list=countries_list,  stat="RA", app=app, language=language,user_list=user_list)
        .groupby(type)
        .size()
        .to_frame(name="RA")
        .reset_index()
    )
    
    counts = (
        dfLR
        .merge(dfLA, on=type, how="left")
        .merge(dfRA, on=type, how="left")
        .fillna(0)
    )

    #### GPP ###
    df = filter_user_data(
       daterange=daterange, countries_list=countries_list, stat="LA", app=app, language=language,user_list=user_list
       )
    avg_gpc_per_type = df.groupby(type)["gpc"].mean().round(2)
    dfGPP = pd.DataFrame(
          {
              type: avg_gpc_per_type.index,
             "GPP": avg_gpc_per_type.values,
            }
    ).fillna(0)

    counts = counts.merge(dfGPP, on=type, how="left").fillna(0)

    dfPC = (
        filter_user_data(daterange=daterange, countries_list=countries_list, stat="PC", app=app, language=language,user_list=user_list)
        .groupby(type)
        .size()
        .to_frame(name="PC")
        .reset_index()
    )

    counts = counts.merge(dfPC, on=type, how="left").fillna(0)
    df = filter_user_data(
        daterange=daterange, countries_list=countries_list, stat="LA", app=app, language=language,user_list=user_list
    )
    gpc_gt_90_counts = df[df["gpc"] >= 90].groupby(type)["user_pseudo_id"].count()
    total_user_counts = df.groupby(type)["user_pseudo_id"].count()

    # Reset index to bring "country" back as a column
    gpc_gt_90_counts = gpc_gt_90_counts.reset_index()
    total_user_counts = total_user_counts.reset_index()

    # Merge the counts into a single DataFrame
    gca = pd.merge(
        gpc_gt_90_counts.rename(columns={"user_pseudo_id": "gpc_gt_90_users"}),
        total_user_counts.rename(columns={"user_pseudo_id": "total_users"}),
        on=type,
    )

    # Calculate the percentage and add it as a new column
    gca["GCA"] = gca["gpc_gt_90_users"] / gca["total_users"] * 100
    counts = counts.merge(gca, on=type, how="left").round(2).fillna(0)
    return counts

@st.cache_data(ttl="1d", show_spinner=False)
def get_counts_new(
    user_cohort_df,          # DataFrame with all the new columns
    groupby_col="app_language",  # or "country", or any grouping column you want
):
    grouped = user_cohort_df.groupby(groupby_col)

    summary = grouped.agg(
        LR=("lr_flag", "sum"),
        LA=("la_flag", "sum"),
        RA=("ra_flag", "sum"),
        GC=("gc_flag", "sum"),
        GPP=("gpc", "mean"),
        total_users=("user_pseudo_id", "count"),
    ).reset_index()

    # Calculate gpc >= 90 users separately
    summary["gpc_gt_90_users"] = grouped.apply(lambda g: (g["gpc"] >= 90).sum()).values
    
    # Clean up columns (drop temp calculation columns)
    summary = summary.drop(columns=["gpc_gt_90_users", "total_users"])
    summary = summary.fillna(0).round(2)
    return summary


# Get the campaign data and filter by date, language, and country selections
@st.cache_data(ttl="1d", show_spinner=False)
def filter_campaigns(df_campaigns_all,daterange,selected_languages,countries_list):

    # Drop the campaigns that don't meet the naming convention
    condition = (df_campaigns_all["app_language"].isna()) | (df_campaigns_all["country"].isna())
    df_campaigns = df_campaigns_all[~condition]

    mask = (df_campaigns['segment_date'].dt.date >= daterange[0]) & (df_campaigns['segment_date'].dt.date <= daterange[1])
    df_campaigns = df_campaigns.loc[mask]
    # Apply country filter if not "All"

    if countries_list[0] != "All":
      mask &= df_campaigns['country'].isin(set(countries_list))

    # Apply language filter if not "All" 
    if selected_languages[0] != "All" :
        mask &= df_campaigns['app_language'].isin(set(selected_languages))

    df_campaigns = df_campaigns.loc[mask]

    col = df_campaigns.pop("country")
    df_campaigns.insert(2, col.name, col)
    df_campaigns.reset_index(drop=True, inplace=True)

    col = df_campaigns.pop("app_language")
    df_campaigns.insert(3, col.name, col)
    df_campaigns.reset_index(drop=True, inplace=True)

    return df_campaigns


def get_month_ranges(start_date, end_date):
    # This function returns a list of start and end dates for each month in the range
    month_ranges = []
    current_date = start_date.replace(day=1)
    
    while current_date <= end_date:
        next_month = current_date.replace(day=28) + dt.timedelta(days=4)  # This will get you to the next month
        month_end = min(end_date, next_month.replace(day=1) - dt.timedelta(days=1))  # End of the current month
        month_ranges.append((current_date, month_end))
        current_date = next_month.replace(day=1)  # Move to the first day of the next month
    
    return month_ranges

def get_totals_per_month_from_cohort(cohort_df, stat, daterange, date_col="first_open"):
    """
    Calculates totals per month by slicing a pre-built cohort_df on date_col for each month.
    """
    month_ranges = get_month_ranges(daterange[0], daterange[1])
    df_campaigns_all = st.session_state["df_campaigns_all"]
    totals_by_month = []

    for start_date, end_date in month_ranges:
        clipped_start_date = start_date
        clipped_end_date = end_date
        clipped_range = [clipped_start_date, clipped_end_date]

        # Slice the cohort_df by date_col for this month
        start = pd.to_datetime(clipped_start_date)
        end = pd.to_datetime(clipped_end_date)
        cohort_df[date_col] = pd.to_datetime(cohort_df[date_col])  # Ensures column type
        df_month = cohort_df[
            (cohort_df[date_col] >= start) & (cohort_df[date_col] <= end)
        ]
        total = get_cohort_totals_by_metric(df_month, stat=stat)

        # Filter campaigns based on the clipped date range
        df_campaigns = filter_campaigns(df_campaigns_all, clipped_range, cohort_df["app_language"].unique(), cohort_df["country"].unique())
        cost = df_campaigns["cost"].sum()
        lrc = (cost / total).round(2) if total != 0 else 0

        totals_by_month.append({
            "month": clipped_start_date.strftime("%B-%Y"),
            "total": total,
            "cost": cost,
            "LRC": lrc
        })

    return pd.DataFrame(totals_by_month)

#@st.cache_data(ttl="1d", show_spinner=False)
def get_user_cohort_list(
    daterange=default_daterange,
    languages=["All"],
    cr_app_versions="All",
    countries_list=["All"],
    app=["CR"],
    as_list=True,
    offline_filter=None
):
    """
    Returns a list of user identifiers (default) or a DataFrame of cohort info based on first_open date,
    country, language, and app type. Use as_list=False to return full DataFrame.
    """
    df_user_cohort = filter_user_data(
        daterange=daterange,
        countries_list=countries_list,
        app=app,
        language=languages,
        user_list=None
    )

    apps = [app] if isinstance(app, str) else app
    # If any selected app is CR or endswith -standalone, use cr_user_id; else user_pseudo_id
    if "CR" in apps or any(a.endswith("-standalone") for a in apps if isinstance(a, str)):
        user_cohort_df = df_user_cohort[["cr_user_id", "first_open", "country", "app_language", "app_version"]]
        user_id_col = "cr_user_id"
    else:
        user_cohort_df = df_user_cohort[["user_pseudo_id"]]
        user_id_col = "user_pseudo_id"

    if as_list:
        return user_cohort_df[user_id_col].dropna().tolist()
    else:
        return user_cohort_df

def get_user_cohort_df(
    session_df,
    daterange=None,
    languages=["All"],
    countries_list=["All"],
    app=None,
):
    """
    Returns a DataFrame (all columns) for the cohort matching filters.
    - df: DataFrame to filter (already chosen by select_user_dataframe)
    - user_list_key: which column uniquely identifies users
    """
    cohort_df = session_df.copy()

    # Apply filters
    if daterange is not None and len(daterange) == 2:
        start = pd.to_datetime(daterange[0])
        end = pd.to_datetime(daterange[1])
        cohort_df = cohort_df[
        (cohort_df["first_open"] >= start) & (cohort_df["first_open"] <= end)
        ]

    if countries_list and countries_list != ["All"]:
        cohort_df = cohort_df[cohort_df["country"].isin(countries_list)]
        
    if languages and languages != ["All"]:
        lang_col = "app_language" if "app_language" in cohort_df.columns else "language"
        cohort_df = cohort_df[cohort_df[lang_col].isin(languages)]
        
    if app and app != ["All"] and "app" in cohort_df.columns:
        apps = [app] if isinstance(app, str) else app
        cohort_df = cohort_df[cohort_df["app"].isin(apps)]
        

    return cohort_df



@st.cache_data(ttl="1d", show_spinner=False)
def calculate_average_metric_per_user(user_cohort_df, column_name):
    """
    Calculate average for column_name for users in the already-filtered cohort_df.
    Applies max_user_level >= 1 as baseline.
    Returns 0 if cohort is empty or column is missing.
    """
    if user_cohort_df.empty or column_name not in user_cohort_df.columns:
        return 0

    # Optionally, filter to max_user_level >= 1 if that's your baseline (as before)
    df_filtered = user_cohort_df[user_cohort_df["max_user_level"] >= 1]

    # For "days_to_ra", skip nulls
    if column_name == "days_to_ra":
        df_filtered = df_filtered[df_filtered["days_to_ra"].notnull()]

    if df_filtered.empty:
        return 0

    average = df_filtered[column_name].mean()
    return average


@st.cache_data(ttl="1d", show_spinner="Calculating metrics")
def get_metrics_for_cohort(user_cohort_df):

    return {
        "Avg Level Reached": calculate_average_metric_per_user(user_cohort_df=user_cohort_df,column_name="max_user_level"),
        "Avg # Sessions / User": calculate_average_metric_per_user(user_cohort_df=user_cohort_df,column_name="engagement_event_count"),
        "Avg Total Play Time / User": calculate_average_metric_per_user(user_cohort_df=user_cohort_df,column_name="total_time_minutes"),
        "Avg Session Length / User": calculate_average_metric_per_user(user_cohort_df=user_cohort_df,column_name="avg_session_length_minutes"),
        "Active Span / User": calculate_average_metric_per_user(user_cohort_df=user_cohort_df,column_name="active_span"),
        "Avg Days to RA":     calculate_average_metric_per_user(user_cohort_df=user_cohort_df,column_name="days_to_ra")
    }


def get_all_apps_combined_session_and_cohort_df(stat=None):
    session_dfs = []
    
    from ui_widgets import get_apps
    all_apps = get_apps()
    
    for app in all_apps:
        session_df = select_user_dataframe_new(app=app, stat=stat)
        session_dfs.append(session_df)

    # Combine all the session dataframes
    combined_session_df = pd.concat(session_dfs, ignore_index=True)

    return combined_session_df


def get_filtered_cohort(app, daterange, language, countries_list):
    """Returns (user_cohort_df, user_cohort_df_LR) for app selection."""
    is_cr = (app == ["CR"] or app == "CR")
    user_cohort_df_LR = None
    session_df = select_user_dataframe_new(app=app)
    user_cohort_df = get_user_cohort_df(
        session_df=session_df,
        daterange=daterange,
        languages=language,
        countries_list=countries_list,
        app=app
    )
    if is_cr:
        session_df_LR = select_user_dataframe_new(app=app, stat="LR")
        user_cohort_df_LR = get_user_cohort_df(
            session_df=session_df_LR,
            daterange=daterange,
            languages=language,
            countries_list=countries_list,
            app=app
        )
    return user_cohort_df, user_cohort_df_LR


def get_cumulative_funnel_counts(df, funnel_order):
    """
    For each stage, return the number of users whose furthest_event is this stage or any later stage.
    Returns: dict {stage: count}
    """
    counts = {}
    for i, stage in enumerate(funnel_order):
        later_stages = funnel_order[i:]
        counts[stage] = df[df["furthest_event"].isin(later_stages)].shape[0]
    return counts


def funnel_percent_by_group(
    cohort_df,
    cohort_df_LR=None,
    groupby_col="app_language",
    app=None,
    min_funnel=False
):
    """
    Returns a single DataFrame with raw counts and percent-normalized columns (suffix '_pct') by group.
    Handles CR (two dfs for LR), all other apps (one df for all steps).
    """
    import pandas as pd

    app_name = app[0] if isinstance(app, list) and len(app) > 0 else app
    app_name = str(app_name) if app_name is not None else ""

    user_key = "cr_user_id"
    funnel_steps = ["LR", "PC", "LA", "RA", "GC"]
    if app_name == "CR" and min_funnel == False:
        funnel_steps = ["LR", "DC", "TS", "SL", "PC", "LA", "RA", "GC"]
    elif app_name == "Unity":
        user_key = "user_pseudo_id"


    group_vals = set(cohort_df[groupby_col].dropna().unique())
    if cohort_df_LR is not None:
        group_vals = group_vals | set(cohort_df_LR[groupby_col].dropna().unique())

    records = []
    for group in sorted(group_vals):
        if app_name == "CR" and cohort_df_LR is not None:
            group_LR = cohort_df_LR[cohort_df_LR[groupby_col] == group]
            count_LR = group_LR[user_key].nunique() if user_key in group_LR else len(group_LR)
        else:
            group_LR = cohort_df[cohort_df[groupby_col] == group]
            count_LR = group_LR[user_key].nunique() if user_key in group_LR else len(group_LR)

        row = {groupby_col: group, "LR": count_LR}
        group_df = cohort_df[cohort_df[groupby_col] == group]
        for step in funnel_steps[1:]:
            row[step] = get_cohort_totals_by_metric(group_df, stat=step)
        records.append(row)

    df = pd.DataFrame(records)
    # Add percent-normalized columns with _pct suffix
    norm_steps = [s for s in funnel_steps if s != "LR"]
    for step in funnel_steps:
        if step == "LR":
            df[f"{step}_pct"] = 100.0  # 100% at baseline
        else:
            df[f"{step}_pct"] = df[step] / df["LR"] * 100

    # Drop rows where all post-LR steps are zero (optional)
    all_zero = (df[norm_steps].fillna(0).astype(float) == 0).all(axis=1)
    df = df[~all_zero].reset_index(drop=True)
    return df, funnel_steps  # Or just return df if you don't need funnel_steps

