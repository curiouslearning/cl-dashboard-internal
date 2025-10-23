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


def select_user_dataframe(app, stat=None):
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

def get_counts(
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


def get_user_cohort_df(
    session_df,
    daterange=None,
    languages=["All"],
    countries_list=["All"],
    app=None,
    cohort=None,
):
    """
    Returns a filtered DataFrame for the cohort matching selected filters.

    Parameters
    ----------
    session_df : pd.DataFrame
        The user-level dataset (from cr_user_progress or cr_app_launch).
    daterange : list-like of 2 dates
        Filters by first_open date range.
    languages : list[str]
        Filters by app_language (default: ["All"]).
    countries_list : list[str]
        Filters by country (default: ["All"]).
    app : str or list[str]
        Filters by app name (e.g. "CR", "Unity", "WBS-standalone").
    cohort : str or list[str]
        Filters by cohort_group (only applied when app == "CR").
    """
    cohort_df = session_df.copy()

    # --- Date range filter ---
    if daterange is not None and len(daterange) == 2:
        start = pd.to_datetime(daterange[0])
        end = pd.to_datetime(daterange[1])
        cohort_df = cohort_df[
            (cohort_df["first_open"] >= start) & (cohort_df["first_open"] <= end)
        ]

    # --- Country filter ---
    if countries_list and countries_list != ["All"]:
        cohort_df = cohort_df[cohort_df["country"].isin(countries_list)]

    # --- Language filter ---
    if languages and languages != ["All"]:
        lang_col = "app_language" if "app_language" in cohort_df.columns else "language"
        cohort_df = cohort_df[cohort_df[lang_col].isin(languages)]

    # --- App filter ---
    if app and app != ["All"] and "app" in cohort_df.columns:
        apps = [app] if isinstance(app, str) else app
        cohort_df = cohort_df[cohort_df["app"].isin(apps)]

    # --- Cohort filter (applies only for CR app) ---
    if (
        cohort
        and cohort != ["All"]
        and "cohort_group" in cohort_df.columns
        and app[0] == "CR"
    ):
        cohorts = [cohort] if isinstance(cohort, str) else cohort
        cohort_df = cohort_df[cohort_df["cohort_group"].isin(cohorts)]

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
def get_engagement_metrics_for_cohort(user_cohort_df):

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
        session_df = select_user_dataframe(app=app, stat=stat)
        session_dfs.append(session_df)

    # Combine all the session dataframes
    combined_session_df = pd.concat(session_dfs, ignore_index=True)

    return combined_session_df


def get_filtered_cohort(app, daterange, language, countries_list, cohort=None):
    """Returns (user_cohort_df, user_cohort_df_LR) for app selection."""
    is_cr = (app == ["CR"] or app == "CR")
    user_cohort_df_LR = None
    session_df = select_user_dataframe(app=app)
    user_cohort_df = get_user_cohort_df(
        session_df=session_df,
        daterange=daterange,
        languages=language,
        countries_list=countries_list,
        app=app,
        cohort=cohort
    )
    if is_cr:
        session_df_LR = select_user_dataframe(app=app, stat="LR")
        user_cohort_df_LR = get_user_cohort_df(
            session_df=session_df_LR,
            daterange=daterange,
            languages=language,
            countries_list=countries_list,
            app=app,
            cohort=cohort
        )
    return user_cohort_df, user_cohort_df_LR


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

@st.cache_data(ttl="1d", show_spinner=False)
def get_sorted_funnel_df(
    cohort_df,
    cohort_df_LR=None,
    groupby_col="app_language",
    app=None,
    min_funnel=True,
    stat="LA",
    sort_by="Total",
    ascending=False,
    use_top_ten=True
):
    """
    Returns a funnel dataframe (with counts and percentages) sorted by the chosen stat.
    Decoupled from Streamlit chart UI so it can be reused for tables, CSVs, or other charts.

    Parameters
    ----------
    cohort_df : pd.DataFrame
        Main cohort dataframe (includes all funnel users)
    cohort_df_LR : pd.DataFrame, optional
        Learners Reached dataframe (for CR app only)
    groupby_col : str, default "app_language"
        Column to group by ("app_language", "country", etc.)
    app : str or list, optional
        App name (e.g., "CR", "Unity", etc.)
    min_funnel : bool, default True
        If True, uses minimal funnel steps for CR
    stat : str, default "LA"
        Funnel metric to sort by ("LR", "LA", "RA", "GC", etc.)
    sort_by : str, default "Total"
        Whether to sort by "Total" (raw counts) or "Percent"
    ascending : bool, default False
        Sort ascending (lowest first) or descending (highest first)
    use_top_ten : bool, default True
        If True, return top 10 rows

    Returns
    -------
    df : pd.DataFrame
        Sorted funnel dataframe
    funnel_steps : list
        List of funnel step names in order
    """

    # Compute funnel summary and funnel step order
    df, funnel_steps = funnel_percent_by_group(
        cohort_df=cohort_df,
        cohort_df_LR=cohort_df_LR,
        groupby_col=groupby_col,
        app=app,
        min_funnel=min_funnel
    )

    # Determine sort column
    if sort_by.lower() == "percent":
        sort_col = stat if stat == "LR" else f"{stat}_pct"
    else:
        sort_col = stat

    # Sort the dataframe
    df = df.sort_values(by=sort_col, ascending=ascending)

    # Limit to top 10 if requested
    if use_top_ten:
        df = df.head(10)

    return df, funnel_steps

@st.cache_data(ttl="1d", show_spinner=False)
def get_top_and_bottom_funnel_groups(
    cohort_df,
    cohort_df_LR=None,
    groupby_col="app_language",
    app=None,
    stat="RA",
    sort_by="Percent",
    min_funnel=True,
):
    """
    Returns two sorted DataFrames: top 10 and bottom 10 groups by the given stat.

    Parameters
    ----------
    cohort_df : pd.DataFrame
        Main cohort dataframe
    cohort_df_LR : pd.DataFrame, optional
        Learners Reached dataframe (for CR app only)
    groupby_col : str, default "app_language"
        Column to group by ("app_language", "country", etc.)
    app : str or list, optional
        App name (e.g., "CR", "Unity", etc.)
    stat : str, default "RA"
        Funnel metric to sort by ("LR", "LA", "RA", "GC", etc.)
    sort_by : str, default "Percent"
        Sort criterion ("Total" or "Percent")
    min_funnel : bool, default True
        Use minimal funnel for CR app

    Returns
    -------
    top10 : pd.DataFrame
        Top 10 groups sorted by descending stat value
    bottom10 : pd.DataFrame
        Bottom 10 groups sorted by ascending stat value
    funnel_steps : list
        Funnel steps returned by funnel_percent_by_group
    """

    top10, funnel_steps = get_sorted_funnel_df(
        cohort_df=cohort_df,
        cohort_df_LR=cohort_df_LR,
        groupby_col=groupby_col,
        app=app,
        min_funnel=min_funnel,
        stat=stat,
        sort_by=sort_by,
        ascending=False,
        use_top_ten=True
    )

    bottom10, _ = get_sorted_funnel_df(
        cohort_df=cohort_df,
        cohort_df_LR=cohort_df_LR,
        groupby_col=groupby_col,
        app=app,
        min_funnel=min_funnel,
        stat=stat,
        sort_by=sort_by,
        ascending=True,
        use_top_ten=True
    )

    return top10, bottom10, funnel_steps

