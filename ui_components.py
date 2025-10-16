import streamlit as st
import pandas as pd
import datetime as dt
from rich import print
import plotly.express as px
import plotly.graph_objects as go
import metrics
from millify import prettify
import users
import numpy as np


default_daterange = [dt.datetime(2021, 1, 1).date(), dt.date.today()]

@st.cache_data(ttl="1d", show_spinner=False)
def LR_LA_line_chart_over_time(
    user_cohort_df,option="LR",  display_category="Country", aggregate=True
):
    option = "LR"
    groupby = "LR Date"
    title = "Daily Learners Reached"
    user_cohort_df.rename({"first_open": "LR Date"}, axis=1, inplace=True)

    # Group by date and display_type, then count the users
    if display_category == "Country":
        display_group = "country"
    elif display_category == "Language":
        display_group = "app_language"
        
    color = display_group

    if aggregate:
        grouped_df = user_cohort_df.groupby(groupby).size().reset_index(name=option)
        grouped_df[option] = grouped_df[option].cumsum()
        grouped_df["7 Day Rolling Mean"] = grouped_df[option].rolling(14).mean()
        color = None
    else:
        grouped_df = user_cohort_df.groupby([groupby, display_group]).size().reset_index(name=option)
        grouped_df["7 Day Rolling Mean"] = grouped_df[option].rolling(14).mean()

    # Plotly line graph
    fig = px.line(
        grouped_df,
        x=groupby,
        y=option,
#        height=300,
        color=color,
        markers=False,
        title=title,
    )

    st.plotly_chart(fig, use_container_width=True)
    return grouped_df


@st.cache_data(ttl="1d", show_spinner=True)
def lrc_scatter_chart(option, display_category, df_campaigns, daterange, session_df, languages, countries_list):
    """
    option: "LRC" or "LAC"
    display_category: "Country" or "Language"
    df_campaigns: campaign spend data (filtered for date range, countries/languages)
    daterange, session_df,  languages, countries_list: for user cohort filtering
    """
    import plotly.express as px

    # Determine grouping
    if display_category == "Country":
        group_col = "country"
        groups = df_campaigns[group_col].unique()
    else:
        group_col = "app_language"
        groups = df_campaigns[group_col].unique()

    # Get user-level metrics for all groups (use your cohort model)
    group_counts = []
    for group in groups:
        if group_col == "country":
            filtered_countries = [group]
            filtered_languages = languages
        else:
            filtered_countries = countries_list
            filtered_languages = [group]

        cohort_df = metrics.get_user_cohort_df(
            session_df=session_df,
            daterange=daterange,
            languages=filtered_languages,
            countries_list=filtered_countries,
            app=None
        )
        LR = metrics.get_cohort_totals_by_metric(cohort_df=cohort_df, stat="LR")
        LA = metrics.get_cohort_totals_by_metric(cohort_df=cohort_df, stat="LA")
        group_counts.append({"group": group, "LR": LR, "LA": LA})

    df_counts = pd.DataFrame(group_counts)
    df_counts.rename(columns={"group": group_col}, inplace=True)

    # Sum cost by group
    df_campaigns_grouped = df_campaigns.groupby(group_col)["cost"].sum().reset_index()

    # Merge user metrics with campaign cost
    merged_df = pd.merge(df_campaigns_grouped, df_counts, on=group_col, how="outer")

    x = "LR" if option == "LRC" else "LA"

    min_value = 200
    merged_df = merged_df[(merged_df["LR"] > min_value) | (merged_df["LA"] > min_value)]

    merged_df[option] = (merged_df["cost"] / merged_df[x]).round(2)
    merged_df[option] = merged_df[option].fillna(0)

    # Formatting for display
    scatter_df = merged_df[[group_col, "cost", option, x]].copy()
    if not scatter_df.empty:
        scatter_df["cost"] = "$" + scatter_df["cost"].apply(lambda x: "{:,.2f}".format(x))
        scatter_df[option] = "$" + scatter_df[option].apply(lambda x: "{:,.2f}".format(x))
        scatter_df[x] = scatter_df[x].apply(lambda x: "{:,}".format(x))

        fig = px.scatter(
            scatter_df,
            x=x,
            y=option,
            color=group_col,
            title="Reach to Cost",
            hover_data={
                "cost": True,
                option: True,
                x: True,
            },
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No data for selected period")
        
    return scatter_df


@st.cache_data(ttl="1d", show_spinner=False)
def spend_by_country_map(df_campaigns,source):

    if source == 'Both':
        df_campaigns = df_campaigns.groupby("country", as_index=False)["cost"].sum().round(2)
    else:
        df_campaigns = df_campaigns[df_campaigns["source"] == source]
        df_campaigns = df_campaigns.groupby("country", as_index=False)["cost"].sum().round(2)


    total_cost = df_campaigns["cost"].sum().round(2)
    value = "$" + prettify(total_cost)
    st.metric(label="Total Spend", value=value)

    country_fig = px.choropleth(
        df_campaigns,
        locations="country",
        color="cost",
        color_continuous_scale=[
            [0, "rgb(166,206,227, 0.5)"],
            [0.05, "rgb(31,120,180,0.5)"],
            [0.1, "rgb(178,223,138,0.5)"],
            [0.3, "rgb(51,160,44,0.5)"],
            [0.6, "rgb(251,154,153,0.5)"],
            [1, "rgb(227,26,28,0.5)"],
        ],
        height=600,
        projection="natural earth",
        locationmode="country names",
        hover_data={
            "cost": ":$,.2f",
        },
    )

    country_fig.update_geos(fitbounds="locations")
    country_fig.update_layout(
        height=600,
        margin=dict(l=10, r=1, b=10, t=10, pad=4),
        geo=dict(bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(country_fig)
    return df_campaigns


def create_engagement_figure(funnel_data, key="", funnel_size="large"):
    percent_2nd = funnel_data.get("PercentOfSecond", [None] * len(funnel_data["Count"]))

    hovertemplate = []
    for i, (title, count, pct2) in enumerate(zip(funnel_data["Title"], funnel_data["Count"], percent_2nd)):
        pct2_txt = (
            f"<br>% of DC: {pct2:.1f}%"
            if funnel_size == "large" and pct2 is not None else ""
        )
        # Use Plotly's built-in variables for percent of previous and initial
        hovertemplate.append(
            f"<b>{title}</b><br>"
            f"Count: {count:,d}"
            "<br>% of previous: %{percentPrevious:.1%}"
            "<br>% of first: %{percentInitial:.1%}"
            f"{pct2_txt}<extra></extra>"
        )

    fig = go.Figure(
        go.Funnel(
            y=funnel_data["Title"],
            x=funnel_data["Count"],
            textposition="auto",
            marker={
                "color": [
                    "#4F420A", "#73600F", "#947C13", "#E0BD1D",
                    "#B59818", "#D9B61C", "#6C5212", "#8B7121"
                ],
                "line": {
                    "width": [4, 3, 2, 2, 2, 1, 1, 1],
                    "color": ["wheat"] * 8,
                },
            },
            connector={"line": {"color": "#4F3809", "dash": "dot", "width": 3}},
            hovertemplate=hovertemplate,
        )
    )
    fig.update_traces(texttemplate="%{value:,d}")
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
    )
    return fig


def levels_reached_chart(
    app_names=None,
    max_plot_level=35,
    title="Levels Reached by App"
):
    """
    Plot percent of original cohort reaching each level for multiple apps.

    Parameters
    ----------
    app_names : list[str]
        List of app names, e.g. ["CR", "Unity", "StandAloneHindi"].
        Defaults to ["CR", "Unity"] if not provided.

    max_plot_level : int
        Maximum level to include on the x-axis (default 35).
    title : str
        Chart title.
    """
    if not app_names:
        app_names = ["CR", "Unity"]

    traces = []

    for app_name in app_names:
        user_cohort_df, _ = metrics.get_filtered_cohort(app=app_name, language=["All"], countries_list=["All"],daterange=default_daterange)

        if user_cohort_df is None or user_cohort_df.empty:
            continue

        # Keep only rows with max_user_level >= 1 and not null
        filtered = user_cohort_df.loc[
            user_cohort_df["max_user_level"].notnull() 
            & (user_cohort_df["max_user_level"] >= 1)
        ]

        # Count users by max_user_level up to the chosen max
        df = (
            filtered.query("max_user_level <= @max_plot_level")
            .groupby("max_user_level", as_index=False)
            .size()
            .rename(columns={"size": "count"})
            .sort_values("max_user_level", ascending=True, ignore_index=True)
        )

        if df.empty:
            continue

        first_level_count = df["count"].iloc[0]
        if first_level_count == 0:
            continue

        df["percent_reached"] = df["count"] / first_level_count * 100.0
        df["percent_drop"] = df["percent_reached"].diff().fillna(0.0)

        trace = go.Scatter(
            x=df["max_user_level"],
            y=df["percent_reached"],
            mode="lines+markers",
            name=app_name,
            customdata=df["percent_drop"],
            text=[app_name] * len(df),
            hovertemplate=(
                "App: %{text}<br>"
                "Max Level: %{x}<br>"
                "Percent reached: %{y:.2f}%<br>"
                "Change from previous: %{customdata:.2f}%%<extra></extra><br>"
            ),
        )
        traces.append(trace)

    layout = go.Layout(
        title=title,
        xaxis=dict(title="Levels"),
        yaxis=dict(title="Percent of Original Group Reaching Level"),
        height=500,
        hovermode="x unified"
    )

    fig = go.Figure(data=traces, layout=layout)
    st.plotly_chart(fig, use_container_width=True)
    return fig


def create_funnels_by_cohort(
    cohort_df,
    key_prefix="",
    funnel_size="medium",
    cohort_df_LR=None,
    app=None,
):

    funnel_variants = {
        "compact": {
            "stats": ["LR", "PC", "LA", "RA", "GC"],
            "titles": [
                "Learner Reached", "Puzzle Completed", "Learners Acquired", "Readers Acquired", "Game Completed"
            ]
        },
        "large": {
            "stats": ["LR", "DC", "TS", "SL", "PC", "LA", "RA", "GC"],
            "titles": [
                "Learner Reached", "Download Completed", "Tapped Start",
                "Selected Level", "Puzzle Completed", "Learners Acquired", "Readers Acquired", "Game Completed"
            ]
        },
        "medium": {
            "stats": ["DC", "TS", "SL", "PC", "LA", "RA", "GC"],
            "titles": [
                "Download Completed", "Tapped Start", "Selected Level",
                "Puzzle Completed", "Learners Acquired", "Readers Acquired", "Game Completed"
            ]
        }
    }

    variant = funnel_variants.get(funnel_size, funnel_variants["medium"])
    stats = variant["stats"]
    titles = variant["titles"]

    # Determine user key for LR (top)
    if app == "Unity" or (isinstance(app, list) and "Unity" in app):
        user_key = "user_pseudo_id"
    else:
        user_key = "cr_user_id"

    funnel_step_counts = []
    for stat in stats:
        if stat == "LR":
            count = (
                cohort_df_LR[user_key].nunique()
                if cohort_df_LR is not None and user_key in cohort_df_LR.columns
                else cohort_df[user_key].nunique()
            )
        else:
            count = metrics.get_cohort_totals_by_metric(cohort_df, stat=stat)
        funnel_step_counts.append(count)

    # --- Percentages ---
    percent_of_previous = [None]
    for i in range(1, len(funnel_step_counts)):
        prev = funnel_step_counts[i-1]
        curr = funnel_step_counts[i]
        percent = round(100 * curr / prev, 1) if prev and prev > 0 else None
        percent_of_previous.append(percent)

    percent_of_second = [None, None]
    if len(funnel_step_counts) >= 2 and funnel_step_counts[1]:
        for i in range(2, len(funnel_step_counts)):
            second = funnel_step_counts[1]
            curr = funnel_step_counts[i]
            percent = round(100 * curr / second, 1) if second and second > 0 else None
            percent_of_second.append(percent)
    else:
        percent_of_second += [None] * (len(funnel_step_counts) - 2)

    funnel_data = {
        "Title": titles,
        "Count": funnel_step_counts,
        "PercentOfPrevious": percent_of_previous,
        "PercentOfSecond": percent_of_second,
    }

    # Render with your existing function
    fig = create_engagement_figure(
        funnel_data,
        key=f"{key_prefix}-5",
        funnel_size=funnel_size,
    )

    st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}-6")


@st.cache_data(ttl="1d", show_spinner="Computing chart")    
def lr_lrc_bar_chart(df_totals_per_month):

    # Create bar chart for Total Learners Reached
    bar_chart = go.Bar(
        x=df_totals_per_month["month"],
        y=df_totals_per_month["total"],
        name='Total Learners Reached',
        marker_color='indianred',
        text=df_totals_per_month["total"],  # Show learners reached value on hover
        textposition='auto',
        hovertemplate='%{x}:<br>%{y:,}<br>Learners Reached<extra></extra>',  # Hover template formatting

)
    # Create line chart for Average LRC
    line_chart = go.Scatter(
        x=df_totals_per_month["month"],
        y=df_totals_per_month["LRC"],
        name='Average LRC',
        mode='lines+markers+text',
        yaxis='y2',  # Assign to second y-axis
        text=[f'${val:.2f}' for val in df_totals_per_month["LRC"]],  # Show cost on hover
        textposition='top center',
        textfont=dict(
        color='black'  # Change text color to blue
                     ),
        hovertemplate='<span style="color:green;">%{x}%{x}:<br>$%{y:,}<br>Avg Learners Reached Cost<extra></extra></span>',  # Hover template formatting

        line=dict(color='green', width=2)
    )

    # Combine the two charts into a figure
    fig = go.Figure()

    # Add bar chart and line chart
    fig.add_trace(bar_chart)
    fig.add_trace(line_chart)

# Set up layout
    fig.update_layout(
        title='Total LRs and Average LRC',
        xaxis=dict(title='Month'),
        yaxis=dict(title='Total Learners Reached', showgrid=False),
        yaxis2=dict(
            title='Average LRC',
            overlaying='y',
            side='right',
            showgrid=False,
            tickprefix='$',  # Add dollar sign for LRC axis
         #   range=[0, 1]  # Adjust as needed based on LRC values
        ),
        legend=dict(x=0.1, y=1.1, orientation='h'),
        barmode='group'
    )

    # Show the figure
    st.plotly_chart(fig, use_container_width=True)

@st.cache_data(ttl="1d", show_spinner="Computing chart")    
def engagement_over_time_chart(df_list_with_labels, metric="Avg Total Time (minutes)"):
    all_data = []

    for label, df in df_list_with_labels:
        df = df.copy()
        df["first_open"] = pd.to_datetime(df["first_open"])
        df["cohort_week"] = df["first_open"].dt.to_period("W").apply(lambda r: r.start_time)

        agg = {
            "user_count": ("user_pseudo_id", "nunique")
        }

        if metric == "Avg Session Count":
            agg["avg_value"] = ("engagement_event_count", "mean")
        else:
            agg["avg_value"] = ("total_time_minutes", "mean")

        cohort_summary = (
            df.groupby("cohort_week")
            .agg(**agg)
            .reset_index()
        )

        cohort_summary = cohort_summary[cohort_summary["user_count"] >= 5]
        cohort_summary["cohort_label"] = label
        all_data.append(cohort_summary)

    if not all_data:
        st.warning("No cohorts had enough users (≥5) to plot.")
        return

    combined_df = pd.concat(all_data, ignore_index=True)

    y_label = "Average Session Count" if metric == "Avg Session Count" else "Average Total Time (minutes)"

    fig = px.line(
        combined_df,
        x="cohort_week",
        y="avg_value",
        color="cohort_label",
        markers=True,
        hover_data={"user_count": True},
        labels={
            "cohort_week": "Week (First Open)",
            "avg_value": y_label,
            "user_count": "Users in Cohort",
            "cohort_label": "Cohort"
        },
        title=f"{y_label} by Weekly Cohort (≥5 users)"
    )

    fig.update_layout(
        xaxis_title="Cohort Week",
        yaxis_title=y_label,
        yaxis_tickformat=",",
 
    )

    st.plotly_chart(fig, use_container_width=True)

    
def days_to_ra_chart(df_ra,by_months):

    df_ra['months_to_ra'] = df_ra['days_to_ra'] / 30.44

    top_langs = df_ra['app_language'].value_counts().nlargest(20).index.tolist()
    df_ra['lang_grouped'] = df_ra['app_language'].where(df_ra['app_language'].isin(top_langs), 'Other')



    if by_months:
        x_col = 'months_to_ra'
        x_label = 'Months to RA'
        hovertemplate = (
            'Months to RA: %{x:.2f}<br>' +
            'Days to RA: %{customdata[0]:.0f}<br>' +
            'User: %{customdata[1]}<br>' +
            'Language: %{customdata[2]}<br>' +
            'Group: %{y}'
        )
    else:
        x_col = 'days_to_ra'
        x_label = 'Days to RA'
        hovertemplate = (
            'Days to RA: %{x:.0f}<br>' +
            'Months to RA: %{customdata[0]:.2f}<br>' +
            'User: %{customdata[1]}<br>' +
            'Language: %{customdata[2]}<br>' +
            'Group: %{y}'
        )

    # Custom data for both days and months always in hover
    fig = px.scatter(
        df_ra,
        x=x_col,
        y='lang_grouped',
        color='lang_grouped',
        opacity=0.25,
        category_orders={'lang_grouped': top_langs + ['Other']},
        hover_data={
            'days_to_ra': True,
            'months_to_ra': ':.2f',
            'app_language': True,
            'lang_grouped': False,
        },
        title=f"{x_label} to Reader Acquired (RA)",
        height=600,
    )

    # Set custom hovertemplate for ALL traces
    for trace in fig.data:
        trace.hovertemplate = hovertemplate

    fig.update_traces(marker=dict(size=4), selector=dict(mode='markers'))
    fig.update_layout(
        showlegend=True,
        yaxis_title='App Language',
        xaxis_title=x_label,
    )
    st.plotly_chart(fig, use_container_width=True)

def ra_ecdf_curve(df_ra,by_months):

    x_col = 'months_to_ra' if by_months else 'days_to_ra'
    x_label = 'Months to RA' if by_months else 'Days to RA'

    # For hover, always provide both
    xvals = np.sort(df_ra[x_col].values)
    days_sorted = np.sort(df_ra['days_to_ra'].values)
    months_sorted = np.sort(df_ra['months_to_ra'].values)
    user_counts = np.arange(1, len(xvals) + 1)
    percent_users = user_counts / len(xvals) * 100

    ecdf_df = pd.DataFrame({
        x_label: xvals,
        "Days to RA": days_sorted,
        "Months to RA": months_sorted,
        "Cumulative Users": user_counts,
        "Percent of Users": percent_users
    })

    fig = px.line(
        ecdf_df,
        x=x_label,
        y="Cumulative Users",
        title=f"Total Users vs {x_label} to Reader Acquired (RA)",
        labels={x_label: x_label, "Cumulative Users": "Total Users"}
    )

    # Custom hover to always display both days & months, plus users and percent
    fig.update_traces(
        customdata=ecdf_df[["Days to RA", "Months to RA", "Percent of Users"]],
        hovertemplate=
            f"{x_label}: %{{x:.2f}}<br>" +
            "Days to RA: %{customdata[0]:.0f}<br>" +
            "Months to RA: %{customdata[1]:.2f}<br>" +
            "Total Users: %{y:,}<br>" +
            "Percent of Users: %{customdata[2]:.1f}%"
    )

    fig.update_layout(
        yaxis_title="Total Users",
        xaxis_title=x_label
    )
    st.plotly_chart(fig, use_container_width=True)
    
def avg_days_to_ra_by_dim_chart(df_ra,app=["CR"]):

    group_dim = st.radio("Grouping", ["Language", "Country"], key="123", index=0,horizontal=True)
    group_col = 'app_language' if group_dim == "Language" else 'country'
    group_label = 'App Language' if group_dim == "Language" else 'Country'

    index_col = "cr_user_id"
    if app[0] == "Unity":
        index_col = "user_pseudo_id"

    stats = (
        df_ra.groupby(group_col)
        .agg(
            avg_days_to_ra=('days_to_ra', 'mean'),
            avg_months_to_ra=('days_to_ra', lambda x: x.mean() / 30.44),
            user_count=(index_col, 'nunique'),
        )
        .reset_index()
        .sort_values('avg_days_to_ra')
    )

    fig = px.scatter(
        stats,
        x=group_col,
        y='avg_days_to_ra',
        size='user_count',
        hover_data={
            group_col: True,
            'avg_days_to_ra': ':.1f',
            'avg_months_to_ra': ':.2f',
            'user_count': True
        },
        title=f'Average to Reader Acquired by {group_label}',
        labels={
            group_col: group_label,
            'avg_days_to_ra': 'Average Days to RA',
            'avg_months_to_ra': 'Average Months to RA',
            'user_count': 'User Count'
        },
        height=500
    )
    fig.update_traces(marker=dict(opacity=0.7, line=dict(width=1, color='DarkSlateGrey')))
    fig.update_layout(
        xaxis_title=group_label,
        yaxis_title='Average Days to RA',
        xaxis={'categoryorder':'total ascending'},
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)
    


def ra_histogram_curve(df_ra, by_months):

    x_col = 'months_to_ra' if by_months else 'days_to_ra'
    x_label = 'Months to RA' if by_months else 'Days to RA'

    # Set your bin size
    bin_size = 5 if not by_months else 0.5
    x_start = 0
    x_end = df_ra[x_col].max()

    fig = px.histogram(
        df_ra,
        x=x_col,
        title=f"Distribution of Users by {x_label} to Reader Acquired (RA)",
        labels={x_col: x_label, 'count': 'Number of Users'},
        opacity=0.8,
        color_discrete_sequence=['royalblue'],
        nbins=int((x_end - x_start) // bin_size)
    )

    # Explicitly set bin edges
    fig.update_traces(
        xbins=dict(
            start=x_start,
            end=x_end,
            size=bin_size
        )
    )

    fig.update_layout(
        yaxis_title="Number of Users",
        xaxis_title=x_label
    )

    st.plotly_chart(fig, use_container_width=True)

def show_dual_metric_table(title, home_metrics):

    df = pd.DataFrame({
        "Metric": list(home_metrics.keys()),
        "App Calculated": [f"{v:.2f}" for v in home_metrics.values()],

    })
    st.markdown(f"### {title}")
    st.table(df)
    

@st.cache_data(ttl="1d", show_spinner="Calculating")
def funnel_chart(
    cohort_df,
    cohort_df_LR=None,
    groupby_col="app_language",
    app=None,
    chart_title=None,
    use_top_ten=True,
    min_funnel=True,
    ascending=False,
    stat="LA",
    chart_type="line",
    sort_by="Total",
):
    """
    Plots a funnel line chart (percent dropoff) or grouped bar chart (raw count or percent-of-LR)
    by group (default: app_language). Sorts and visualizes according to selected stat and method.
    """
    # 1. Compute funnel summary and step order
    df, funnel_steps = metrics.funnel_percent_by_group(
        cohort_df=cohort_df,
        cohort_df_LR=cohort_df_LR,
        groupby_col=groupby_col,
        app=app,
        min_funnel=min_funnel
    )

    # 2. Determine sort column, handling LR edge case for percent
    if sort_by == "Percent":
        # LR_pct is always 100%, so sort by total in this case
        sort_col = stat if stat == "LR" else f"{stat}_pct"
    else:
        sort_col = stat

    df = df.sort_values(by=sort_col, ascending=ascending)
    if use_top_ten:
        df = df.head(10)

    fig = go.Figure()

    if chart_type == "line":
        # Plot line chart: percent dropoff by group
        for idx, row in df.iterrows():
            group_label = row[groupby_col]
            percent_values = [row.get(f"{step}_pct", 0) for step in funnel_steps]
            numerator_values = [row.get(step, 0) for step in funnel_steps]
            denominator_value = row.get("LR", 0)
            custom_data = [
                [step, int(num), row.get(f"{step}_pct", 0), int(denominator_value), group_label]
                for step, num in zip(funnel_steps, numerator_values)
            ]
            fig.add_trace(go.Scatter(
                x=funnel_steps,
                y=percent_values,
                mode='lines+markers',
                name=str(group_label),
                customdata=custom_data,
                hovertemplate=(
                    f"{groupby_col.title()}: %{{customdata[4]}}<br>"
                    "Step: %{customdata[0]}<br>"
                    "Count: %{customdata[1]:,}<br>"
                    "Percent: %{customdata[2]:.2f}%<br>"
                    "LR: %{customdata[3]:,}<extra></extra>"
                ),
            ))
        yaxis_title = "Percentage of LR (%)"
        yaxis = dict(tickformat=".2f")
        if not chart_title:
            chart_title = f"Percentage of LR by {groupby_col.title()}"
        fig.update_layout(
            xaxis_title="Funnel Steps",
            legend_title=groupby_col.title(),
        )

    elif chart_type == "bar":
        if sort_by == "Percent":
            # REMOVE LR step, only show funnel steps after LR
            funnel_steps_no_lr = [step for step in funnel_steps if step != "LR"]
            for step in funnel_steps_no_lr:
                pct_col = f"{step}_pct"
                if step in df.columns and pct_col in df.columns:
                    bar_customdata = [
                        [row[step], row[pct_col], step, row[groupby_col]]
                        for _, row in df.iterrows()
                    ]
                    fig.add_trace(go.Bar(
                        x=df[groupby_col],
                        y=df[pct_col],  # Bar height = percent
                        name=step,
                        text=[f"{row[pct_col]:.2f}%" for _, row in df.iterrows()],
                        customdata=bar_customdata,
                        textposition="auto",
                        hovertemplate=(
                            f"{groupby_col.title()}: %{{customdata[3]}}<br>"
                            "Step: %{customdata[2]}<br>"
                            "Count: %{customdata[0]:,}<br>"
                            "Percent: %{customdata[1]:.2f}%<extra></extra>"
                        ),
                    ))
            yaxis_title = "Percent of LR (%)"
            yaxis = dict(tickformat=".2f", range=[0, 100])  # lock axis to 100
        else:
            # Bar heights are raw counts (including LR)
            for step in funnel_steps:
                pct_col = f"{step}_pct"
                if step in df.columns and pct_col in df.columns:
                    bar_customdata = [
                        [row[step], row[pct_col], step, row[groupby_col]]
                        for _, row in df.iterrows()
                    ]
                    fig.add_trace(go.Bar(
                        x=df[groupby_col],
                        y=df[step],
                        name=step,
                        text=df[step],
                        customdata=bar_customdata,
                        textposition="auto",
                        hovertemplate=(
                            f"{groupby_col.title()}: %{{customdata[3]}}<br>"
                            "Step: %{customdata[2]}<br>"
                            "Count: %{customdata[0]:,}<br>"
                            "Percent: %{customdata[1]:.2f}%<extra></extra>"
                        ),
                    ))
            yaxis_title = "Users"
            yaxis = dict(tickformat=",d")
        if not chart_title:
            chart_title = f"{groupby_col.replace('_',' ').title()} Funnel Metrics"

        fig.update_layout(
            barmode="group",
            xaxis_title=groupby_col.replace('_', ' ').title(),
            legend_title="Funnel Step",
        )

    else:
        raise ValueError(f"Unknown chart_type: {chart_type}. Must be 'line' or 'bar'.")

    # Shared chart settings
    fig.update_layout(
        title=chart_title,
        yaxis_title=yaxis_title,
        template="plotly_white",
        yaxis=yaxis,
        margin=dict(t=60, b=40, l=0, r=0),
        font=dict(size=14),
    )

    st.plotly_chart(fig, use_container_width=True)
    return df

@st.cache_data(ttl="1d", show_spinner="Calculating")
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
    Used by funnel_chart() and any other visualizations needing sorted funnel data.
    """
    # Compute funnel summary and steps
    df, funnel_steps = metrics.funnel_percent_by_group(
        cohort_df=cohort_df,
        cohort_df_LR=cohort_df_LR,
        groupby_col=groupby_col,
        app=app,
        min_funnel=min_funnel
    )

    # Determine sort column
    if sort_by == "Percent":
        sort_col = stat if stat == "LR" else f"{stat}_pct"
    else:
        sort_col = stat

    # Sort and truncate
    df = df.sort_values(by=sort_col, ascending=ascending)
    if use_top_ten:
        df = df.head(10)

    return df, funnel_steps

@st.cache_data(ttl="1d", show_spinner="Calculating")
def funnel_chart(
    cohort_df,
    cohort_df_LR=None,
    groupby_col="app_language",
    app=None,
    chart_title=None,
    use_top_ten=True,
    min_funnel=True,
    ascending=False,
    stat="LA",
    chart_type="line",
    sort_by="Total",
):
    """
    Plots a funnel line chart (percent dropoff) or grouped bar chart (raw count or percent-of-LR)
    by group (default: app_language). Sorts and visualizes according to selected stat and method.

    Uses get_sorted_funnel_df() for consistent sorting and decoupling from UI logic.
    """

    # ✅ Get sorted data and funnel step order
    df, funnel_steps = get_sorted_funnel_df(
        cohort_df=cohort_df,
        cohort_df_LR=cohort_df_LR,
        groupby_col=groupby_col,
        app=app,
        min_funnel=min_funnel,
        stat=stat,
        sort_by=sort_by,
        ascending=ascending,
        use_top_ten=use_top_ten,
    )

    fig = go.Figure()

    # --- CHART TYPE: LINE ---
    if chart_type == "line":
        for _, row in df.iterrows():
            group_label = row[groupby_col]
            percent_values = [row.get(f"{step}_pct", 0) for step in funnel_steps]
            numerator_values = [row.get(step, 0) for step in funnel_steps]
            denominator_value = row.get("LR", 0)
            custom_data = [
                [step, int(num), row.get(f"{step}_pct", 0), int(denominator_value), group_label]
                for step, num in zip(funnel_steps, numerator_values)
            ]
            fig.add_trace(go.Scatter(
                x=funnel_steps,
                y=percent_values,
                mode="lines+markers",
                name=str(group_label),
                customdata=custom_data,
                hovertemplate=(
                    f"{groupby_col.title()}: %{{customdata[4]}}<br>"
                    "Step: %{customdata[0]}<br>"
                    "Count: %{customdata[1]:,}<br>"
                    "Percent: %{customdata[2]:.2f}%<br>"
                    "LR: %{customdata[3]:,}<extra></extra>"
                ),
            ))

        yaxis_title = "Percentage of LR (%)"
        yaxis = dict(tickformat=".2f")
        if not chart_title:
            chart_title = f"Percentage of LR by {groupby_col.title()}"

        fig.update_layout(
            xaxis_title="Funnel Steps",
            legend_title=groupby_col.title(),
        )

    # --- CHART TYPE: BAR ---
    elif chart_type == "bar":
        if sort_by.lower() == "percent":
            # Remove LR step (always 100%)
            funnel_steps_no_lr = [step for step in funnel_steps if step != "LR"]
            for step in funnel_steps_no_lr:
                pct_col = f"{step}_pct"
                if step in df.columns and pct_col in df.columns:
                    bar_customdata = [
                        [row[step], row[pct_col], step, row[groupby_col]]
                        for _, row in df.iterrows()
                    ]
                    fig.add_trace(go.Bar(
                        x=df[groupby_col],
                        y=df[pct_col],
                        name=step,
                        text=[f"{row[pct_col]:.2f}%" for _, row in df.iterrows()],
                        customdata=bar_customdata,
                        textposition="auto",
                        hovertemplate=(
                            f"{groupby_col.title()}: %{{customdata[3]}}<br>"
                            "Step: %{customdata[2]}<br>"
                            "Count: %{customdata[0]:,}<br>"
                            "Percent: %{customdata[1]:.2f}%<extra></extra>"
                        ),
                    ))
            yaxis_title = "Percent of LR (%)"
            yaxis = dict(tickformat=".2f", range=[0, 100])  # lock axis to 100
        else:
            # Bar heights are raw counts (including LR)
            for step in funnel_steps:
                pct_col = f"{step}_pct"
                if step in df.columns and pct_col in df.columns:
                    bar_customdata = [
                        [row[step], row[pct_col], step, row[groupby_col]]
                        for _, row in df.iterrows()
                    ]
                    fig.add_trace(go.Bar(
                        x=df[groupby_col],
                        y=df[step],
                        name=step,
                        text=df[step],
                        customdata=bar_customdata,
                        textposition="auto",
                        hovertemplate=(
                            f"{groupby_col.title()}: %{{customdata[3]}}<br>"
                            "Step: %{customdata[2]}<br>"
                            "Count: %{customdata[0]:,}<br>"
                            "Percent: %{customdata[1]:.2f}%<extra></extra>"
                        ),
                    ))
            yaxis_title = "Users"
            yaxis = dict(tickformat=",d")

        if not chart_title:
            chart_title = f"{groupby_col.replace('_',' ').title()} Funnel Metrics"

        fig.update_layout(
            barmode="group",
            xaxis_title=groupby_col.replace('_', ' ').title(),
            legend_title="Funnel Step",
        )

    else:
        raise ValueError(f"Unknown chart_type: {chart_type}. Must be 'line' or 'bar'.")

    # --- SHARED CHART SETTINGS ---
    fig.update_layout(
        title=chart_title,
        yaxis_title=yaxis_title,
        template="plotly_white",
        yaxis=yaxis,
        margin=dict(t=60, b=40, l=0, r=0),
        font=dict(size=14),
    )

    st.plotly_chart(fig, use_container_width=True)
    return df
