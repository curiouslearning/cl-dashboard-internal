import streamlit as st
import pandas as pd
import datetime as dt
from rich import print
import plotly.express as px
import plotly.graph_objects as go
import metrics
from millify import prettify
import plost
import users
import campaigns
from datetime import timedelta
import numpy as np
from sklearn.linear_model import LinearRegression

default_daterange = [dt.datetime(2021, 1, 1).date(), dt.date.today()]

@st.cache_data(ttl="1d", show_spinner=False)
def stats_by_country_map(daterange, countries_list, app=["CR"], language="All", option="LR"):

    df = metrics.get_counts(type="country",
    daterange=daterange, countries_list=countries_list, app=app, language=language
    )
    country_fig = px.choropleth(
        df,
        locations="country",
        color=str(option),
        color_continuous_scale=[
            "#F9FAFA",
            "#7ef7f7",
            "#a9b6b5",
            "#d0a272",
            "#e48f35",
            "#a18292",
            "#85526c",
            "#48636e",
        ],
        height=600,
        projection="natural earth",
        locationmode="country names",
        hover_data={
            "LR": ":,",
            "PC": ":,",
            "LA": ":,",
            "GPP": ":,",
            "GCA": ":,",
        },
    )

    country_fig.update_layout(
        height=500,
        margin=dict(l=10, r=1, b=0, t=10, pad=4),
        geo=dict(bgcolor="rgba(0,0,0,0)"),
        #       paper_bgcolor="LightSteelBlue",
    )

    country_fig.update_geos(fitbounds="locations")
    st.plotly_chart(country_fig)
    
    return df


@st.cache_data(ttl="1d", show_spinner=False)
def campaign_gantt_chart():
    
    df1 = campaigns.get_name_compliant_campaigns()

    df1["campaign_start_date"] = pd.to_datetime(df1["campaign_start_date"]).dt.date

    # Query the DataFrame
    df1 = df1.query("campaign_start_date > @chart_start")

    # Converting columns to datetime format
    df1["start_date"] = pd.to_datetime(df1["campaign_start_date"])

    # Remove rows where 'end_date' is greater than one year from today (likely invalid campaign)
    today = dt.datetime.now()
    one_year_from_today = today + dt.timedelta(days=365)
    df1 = df1[df1["end_date"] <= one_year_from_today]

    df1["campaign_name_short"] = df1["campaign_name"].str[
        :30
    ]  # cut the title to fit the chart

    df1 = df1[
        (df1["end_date"] - df1["start_date"]).dt.days > 1
    ]  # eliminate campaigns that didn't run longer than a day
    rows = len(df1.index)

    fontsize = 8
    if rows > 80:
        height = rows * 10
    elif rows > 40 and rows <= 80:
        height = rows * 20
    elif  rows > 10 and rows <= 40:
        height = rows * 30
        fontsize = 12
    else:
        height = 500
        fontsize = 18


    fig = px.timeline(
        df1,
        x_start="start_date",
        x_end="end_date",
        y="campaign_name_short",
        height=height,
        color_continuous_scale=[
            [0, "rgb(166,206,227, 0.5)"],
            [0.05, "rgb(31,120,180,0.5)"],
            [0.1, "rgb(178,223,138,0.5)"],
            [0.3, "rgb(51,160,44,0.5)"],
            [0.6, "rgb(251,154,153,0.5)"],
            [1, "rgb(227,26,28,0.5)"],
        ],
        color_discrete_sequence=px.colors.qualitative.Vivid,
        color="cost",
        custom_data=[df1["campaign_name"], df1["cost"], df1["start_date"], df1["end_date"]],
    )
    
    fig.update_yaxes(autorange="reversed")

    fig.update_layout(
        title="",
        hoverlabel_bgcolor="#DAEEED",
        bargap=0.2,
        xaxis_title="",
        yaxis_title="",
        yaxis=dict(tickfont_size=fontsize),
        title_x=0.5,  # Make title centered
        xaxis=dict(
            tickfont_size=10,
            tickangle=270,
            rangeslider_visible=False,
            side="top",  # Place the tick labels on the top of the chart
            showgrid=True,
            zeroline=True,
            showline=True,
            showticklabels=True,
            tickformat="%x\n",
        ),
    )

    hovertemp = "<b>Start Date: </b> %{customdata[2]|%m-%d-%Y } <br>"
    hovertemp += "<b>End Date: </b> %{customdata[3]|%m-%d-%Y} <br>"
    hovertemp += "<b>Campaign: </b> %{customdata[0]} <br>"
    hovertemp += "<b>Cost: </b> %{customdata[1]:$,.2f}<br>"
    fig.update_traces(hoverinfo="text", hovertemplate=hovertemp)
    fig.update_xaxes(
        tickangle=0, tickfont=dict(family="Rockwell", color="#A9A9A9", size=12)
    )
    
    st.plotly_chart(
        fig, use_container_width=True
    )  # Display the plotly chart in Streamlit

@st.cache_data(ttl="1d", show_spinner=False)
def top_gpp_bar_chart(daterange, countries_list, app=["CR"], language="All",display_category="Country",user_list=None):

    # Group by date and display_type, then count the users
    if display_category == "Country":
        display_group = "country"
    elif display_category == "Language":
        display_group = "app_language"     

    df = metrics.get_counts(type=display_group,
    daterange=daterange, countries_list=countries_list, app=app, language=language,user_list=user_list
    )
    
    df = df[[display_group, "GPP"]].sort_values(by="GPP", ascending=False).head(10)

    fig = px.bar(
        df, x=display_group, y="GPP", color=display_group, title="Top 10 Countries by GPP %"
    )
    st.plotly_chart(fig, use_container_width=True)
    return df

@st.cache_data(ttl="1d", show_spinner=False)
def top_gca_bar_chart(daterange, countries_list, app=["CR"], language="All",display_category="Country",user_list=None):

    # Group by date and display_type, then count the users
    if display_category == "Country":
        display_group = "country"
    elif display_category == "Language":
        display_group = "app_language"     
    
    df = metrics.get_counts(type=display_group,
        daterange=daterange, countries_list=countries_list, app=app, language=language,user_list=user_list
    )

    df = df[[display_group, "GCA"]].sort_values(by="GCA", ascending=False).head(10)

    fig = px.bar(
        df,
        x=display_group,
        y="GCA",
        color=display_group,
        title="Top 10  by GCA %",
    )
    st.plotly_chart(fig, use_container_width=True)
    return df

@st.cache_data(ttl="1d", show_spinner=False)
def top_LR_LC_bar_chart(daterange, countries_list, option, app=["CR"], language="All",display_category="Country",user_list=None):
    # Group by date and display_type, then count the users
    if display_category == "Country":
        display_group = "country"
    elif display_category == "Language":
        display_group = "app_language"      

    df = metrics.get_counts(type=display_group,
        daterange=daterange, countries_list=countries_list, app=app, language=language,user_list=user_list
    )


    df = (
        df[[display_group, "LR", "LA" , "RA"]]
        .sort_values(by=option, ascending=False)
        .head(10)
        .round(2)
    )

    title = "Top 10 by " + str(option)
    fig = go.Figure(
        data=[
            go.Bar(
                name="LR",
                x=df[display_group],
                y=df["LR"],
                hovertemplate=" %{x}<br>LR: %{y:,.0f}<extra></extra>",
            ),
            go.Bar(
                name="LA",
                x=df[display_group],
                y=df["LA"],
                hovertemplate=" %{x}<br>LA: %{y:,.0f}<extra></extra>",
            ),
            go.Bar(
                name="RA",
                x=df[display_group],
                y=df["RA"],
                hovertemplate=" %{x}<br>RA: %{y:,.0f}<extra></extra>",
            ),
        ],
    )
    fig.update_layout(title_text=title)
    st.plotly_chart(fig, use_container_width=True)
    return df

@st.cache_data(ttl="1d", show_spinner=False)
def LR_LA_line_chart_over_time(
    daterange, countries_list, option, app=["CR"], language="All", display_category="Country", aggregate=True
):
    df_user_list = metrics.filter_user_data(
        daterange=daterange, countries_list=countries_list, stat=option, app=app, language=language
    )

    if option == "LA":
        groupby = "LA Date"
        title = "Daily Learners Acquired"
        df_user_list.rename({"la_date": "LA Date"}, axis=1, inplace=True)
    else:
        groupby = "LR Date"
        title = "Daily Learners Reached"
        df_user_list.rename({"first_open": "LR Date"}, axis=1, inplace=True)

    # Group by date and display_type, then count the users
    if display_category == "Country":
        display_group = "country"
    elif display_category == "Language":
        display_group = "app_language"
        
    color = display_group

    if aggregate:
        grouped_df = df_user_list.groupby(groupby).size().reset_index(name=option)
        grouped_df[option] = grouped_df[option].cumsum()
        grouped_df["7 Day Rolling Mean"] = grouped_df[option].rolling(14).mean()
        color = None
    else:
        grouped_df = df_user_list.groupby([groupby, display_group]).size().reset_index(name=option)
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

def campaign_funnel_chart():
    df_campaigns = st.session_state.df_campaigns
    impressions = df_campaigns["impressions"].sum()

    clicks = df_campaigns["clicks"].sum()

    funnel_data = {
        "Title": [
            "Impressions",
            "Clicks",
        ],
        "Count": [impressions, clicks],
    }

    fig = create_engagement_figure(funnel_data=funnel_data)
    fig.update_layout(
        height=200,
    )

    st.plotly_chart(fig, use_container_width=True)


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

import plotly.graph_objs as go
import streamlit as st
import pandas as pd

def levels_reached_chart(
    app_names=None,
    stat="LA",
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
    stat : str
        Stat to pass into metrics.filter_user_data (default "LA").
    max_plot_level : int
        Maximum level to include on the x-axis (default 35).
    title : str
        Chart title.
    """
    if not app_names:
        app_names = ["CR", "Unity"]

    traces = []

    for app_name in app_names:
        # Fetch user list for this app (note: app must be passed as a list)
        df_user_list = metrics.filter_user_data(
            stat=stat,
            app=[app_name]
        )

        if df_user_list is None or df_user_list.empty:
            continue

        # Count users by max_user_level up to the chosen max
        df = (
            df_user_list[df_user_list["max_user_level"].notnull()]
            .query("max_user_level <= @max_plot_level")
            .groupby("max_user_level", as_index=False)
            .size()
            .rename(columns={"size": "count"})
            .sort_values("max_user_level", ascending=True)
            .reset_index(drop=True)
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
                "Change from previous: %{customdata:.2f}%%<extra></extra>"
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

@st.cache_data(ttl="1d", show_spinner=False)
def funnel_change_line_chart(df, graph_type='sum'):
    # Convert the column to date only (remove timestamp)
    df['date'] = df['date'].dt.date

    grouped = df.groupby('date').sum().reset_index()
    fig = go.Figure()

    # Define the columns for sum and percent
    sum_columns = ['LR', 'DC', 'TS', 'SL', 'PC', 'LA', 'RA', 'GC']

    # Calculate percent of previous level for the hover data
    grouped['DC over LR'] = (grouped['DC'] / grouped['LR'] * 100).round(2)
    grouped['TS over DC'] = (grouped['TS'] / grouped['DC'] * 100).round(2)
    grouped['SL over TS'] = (grouped['SL'] / grouped['TS'] * 100).round(2)
    grouped['PC over SL'] = (grouped['PC'] / grouped['SL'] * 100).round(2)
    grouped['LA over PC'] = (grouped['LA'] / grouped['PC'] * 100).round(2)
    grouped['RA over LA'] = (grouped['RA'] / grouped['LA'] * 100).round(2)
    grouped['GC over RA'] = (grouped['GC'] / grouped['RA'] * 100).round(2)
    
    # Adding nominator and denominator for hover display
    grouped['DC_LR_nom_den'] = grouped[['DC', 'LR']].values.tolist()
    grouped['TS_DC_nom_den'] = grouped[['TS', 'DC']].values.tolist()
    grouped['SL_TS_nom_den'] = grouped[['SL', 'TS']].values.tolist()
    grouped['PC_SL_nom_den'] = grouped[['PC', 'SL']].values.tolist()
    grouped['LA_PC_nom_den'] = grouped[['LA', 'PC']].values.tolist()
    grouped['RA_LA_nom_den'] = grouped[['RA', 'LA']].values.tolist()
    grouped['GC_RA_nom_den'] = grouped[['GC', 'RA']].values.tolist()

    percent_columns = ['DC over LR', 'TS over DC', 'SL over TS', 'PC over SL', 'LA over PC', 'RA over LA', 'GC over RA']
    nom_den_columns = ['DC_LR_nom_den', 'TS_DC_nom_den', 'SL_TS_nom_den', 'PC_SL_nom_den', 'LA_PC_nom_den', 'RA_LA_nom_den', 'GC_RA_nom_den']
    
    # Column names for the hover labels (nominator/denominator)
    hover_labels = [('DC', 'LR'), ('TS', 'DC'), ('SL', 'TS'), ('PC', 'SL'), ('LA', 'PC'), ('RA', 'LA'), ('GC', 'RA')]

    # Select the columns to plot based on the graph_type parameter
    if graph_type == 'Percent remaining':
        columns_to_plot = percent_columns
        y_axis_title = 'Percent remaining'
    else:
        columns_to_plot = sum_columns
        y_axis_title = 'Totals'

    for i, col in enumerate(columns_to_plot):
        if graph_type == 'Percent remaining':
            # Only assign percent_col and nom_den_col if graph_type is 'Percent remaining'
            nom_den_col = nom_den_columns[i] 
            nom_label, den_label = hover_labels[i] 
        else:
            # If graph_type is not 'Percent remaining', don't reference percent_columns and related lists
            nom_den_col = None
            nom_label, den_label = None, None

        # Select y values based on graph_type
        y_values = grouped[columns_to_plot[i]]

        # Conditional hovertemplate based on graph_type
        if graph_type == 'Percent remaining': 
            fig.add_trace(go.Scatter(
                x=grouped['date'],
                y=y_values,
                mode='lines+markers',
                name=col,
                hovertemplate=(
                    f'<b>Date:</b> %{{x}}<br><b>{col}:</b> %{{y:,}}%' +
                    f'<br><b>{nom_label}:</b> %{{customdata[0]:,}}<br><b>{den_label}:</b> %{{customdata[1]:,}}<extra></extra>'
                ),

                customdata=grouped[nom_den_col]
            ))
        else:
            # For sum or the first trace, use a simpler hovertemplate
            fig.add_trace(go.Scatter(
                x=grouped['date'],
                y=y_values,
                mode='lines+markers',
                name=col,
                hovertemplate=(
                    f'<b>Date:</b> %{{x}}<br><b>{col}:</b> %{{y:,}}<extra></extra>'
                )
            ))

    # Customize the layout to display only the date
    fig.update_layout(
        title=f'{y_axis_title} of Each Column for Each Date',
        xaxis_title='Date',
        yaxis_title=y_axis_title,
        xaxis_tickangle=-45,
        xaxis=dict(
            type='category',  # Change the axis type to 'category' to remove intermediate time markers
            tickformat='%m-%d-%Y'  # Specify the date format
        ),
        template='plotly',
        legend_title_text='Columns'
    )

    # Plotly chart and data display
    st.plotly_chart(fig, use_container_width=True)


def top_campaigns_by_downloads_barchart(n):
    df_campaigns = st.session_state.df_campaigns
    df = df_campaigns.filter(["campaign_name", "mobile_app_install"], axis=1)
    pivot_df = pd.pivot_table(
        df, index=["campaign_name"], aggfunc={"mobile_app_install": "sum"}
    )

    df = pivot_df.sort_values(by=["mobile_app_install"], ascending=False)
    df.reset_index(inplace=True)
    df = df.rename(
        columns={"campaign_name": "Campaign", "mobile_app_install": "Installs"}
    )
    df = df.head(n)
    plost.bar_chart(
        data=df,
        bar="Installs",
        value="Campaign",
        direction="vertical",
        use_container_width=True,
        legend="bottom",
    )

def funnel_change_by_language_chart(
    languages, countries_list, daterange, upper_level, bottom_level, user_list=[]
):
    start_date, end_date = daterange
    total_days = (end_date - start_date).days
    weeks = metrics.weeks_since(daterange)
    
    show_actual = st.checkbox("Show Actual Data Lines", value=True)
    show_trend = st.checkbox("Show Trend Lines", value=True)

    if weeks <= 4:
        date_ranges = [
            (start_date + timedelta(days=i), start_date + timedelta(days=i + 1))
            for i in range(total_days)
        ]
        x_axis_label = "Day"
    else:
        date_ranges = [
            (end_date - timedelta(weeks=i), end_date - timedelta(weeks=i - 1))
            for i in range(1, weeks + 1)
        ]
        x_axis_label = "Week"

    df = pd.DataFrame(columns=["start_date"] + languages)
    customdata_map = {lang: [] for lang in languages}

    for start_date, period_end in date_ranges:
        row_data = {"start_date": start_date}
        local_daterange = [start_date, period_end]

        for language in languages:
            language_list = [language]

            bottom_val = metrics.get_totals_by_metric(
                daterange=local_daterange,
                stat=bottom_level,
                language=language_list,
                countries_list=countries_list,
                app=["CR"],
                user_list=user_list,
            )

            upper_val = metrics.get_totals_by_metric(
                daterange=local_daterange,
                stat=upper_level,
                language=language_list,
                countries_list=countries_list,
                app=["CR"],
                user_list=user_list,
            )

            if upper_val in [0, None] or bottom_val is None:
                percentage = 0
            else:
                percentage = round((bottom_val / upper_val) * 100, 2)

            row_data[language] = percentage
            customdata_map[language].append((bottom_val, upper_val))

        df.loc[len(df)] = row_data

    df["start_date"] = pd.to_datetime(df["start_date"])
    df["start_date_numeric"] = (df["start_date"] - df["start_date"].min()).dt.days

    traces = []

    for lang in languages:
        x_vals = df["start_date_numeric"].values.reshape(-1, 1)
        y_vals = df[lang].values
        custom_vals = customdata_map[lang]

        if show_actual:
            traces.append(
                go.Scatter(
                    x=df["start_date"],
                    y=y_vals,
                    mode="lines+markers",
                    name=lang,
                    customdata=custom_vals,
                    hovertemplate=(
                        f"<b>{lang}</b><br>Date: %{{x}}<br>"
                        "Percentage: %{y}%<br>"
                        f"{bottom_level}: %{{customdata[0]:,}}<br>"
                        f"{upper_level}: %{{customdata[1]:,}}<extra></extra>"
                    ),
                )
            )

        if show_trend and np.isfinite(y_vals).sum() > 1:
            model = LinearRegression()
            model.fit(x_vals, y_vals)
            trendline_y = model.predict(x_vals)

            traces.append(
                go.Scatter(
                    x=df["start_date"],
                    y=trendline_y,
                    mode="lines",
                    name=f"{lang} Trend",
                    line=dict(dash="dot"),
                    showlegend=True,
                )
            )

    fig = go.Figure(
        data=traces,
        layout=go.Layout(
            xaxis=dict(title=x_axis_label),
            yaxis=dict(title="Percent of upper level"),
            legend={"traceorder": "normal"},
            margin=dict(l=10, r=1, b=0, t=10, pad=4),
            geo=dict(bgcolor="rgba(0,0,0,0)"),
        ),
    )
    fig.update_layout(
        xaxis=dict(
            title=x_axis_label,
            tickformat="%Y-%m-%d"
        )
    )

    st.plotly_chart(fig, use_container_width=True)
    return df


@st.cache_data(ttl="1d", show_spinner=False)
def funnel_bar_chart(languages, countries_list, daterange,user_cohort_list):

    df = metrics.build_funnel_dataframe(
        index_col="language",
        daterange=daterange,
        languages=languages,
        countries_list=countries_list,
        user_list=user_cohort_list,
    )

    # Bar chart
    fig = go.Figure()
    # Adding each metric as a bar
    levels = ["LR", "DC", "TS" ,"SL","PC", "LA", "RA","GC"]
    
    # Adding each metric as a bar
    for level in levels:
        fig.add_trace(go.Bar(x=df["language"], y=df[level], name=level))

    title = ""
    fig.update_layout(
        barmode="group",
        title="Language Metrics",
        xaxis_title="Language",
        yaxis_title="Total",
        legend_title="Levels",
        template="plotly_white",
        yaxis=dict(tickformat=",d"),  # Format Y-axis for better readability

        title_text=title,
        #    margin=dict(l=10, r=1, b=0, t=10, pad=4),
        geo=dict(bgcolor="rgba(0,0,0,0)"),
    )
    
    st.plotly_chart(fig, use_container_width=True)
    return df
    

@st.cache_data(ttl="1d", show_spinner=False)
def funnel_line_chart_percent(languages, countries_list, daterange, user_cohort_list, app=["CR"]):
    # Determine levels first, BEFORE using in logic below
      
    if app[0] == "Unity":
        levels = ["LR", "PC", "LA", "RA", "GC"]
    else:
        levels = ["LR", "DC", "TS", "SL", "PC", "LA", "RA", "GC"]
        
    # Build funnel dataframe
    df = metrics.build_funnel_dataframe(
        index_col="language",
        daterange=daterange,
        languages=languages,
        app=app,
        countries_list=countries_list,
        user_list=user_cohort_list
    )

    df_percent = df.copy()

    # Normalize only the specified levels against LR
    columns_to_normalize = levels.copy()
    columns_to_normalize.remove("LR")
    df_percent[columns_to_normalize] = df_percent[columns_to_normalize].div(df["LR"], axis=0) * 100
    df_percent["LR"] = 100  # Set LR as 100% baseline

    cols_after_lr = ['DC', 'TS', 'SL', 'PC', 'LA', 'RA', 'GC']
    # Keep only rows where at least one column after LR is nonzero and not blank/NaN
    df_percent = df_percent[df_percent[cols_after_lr].fillna(0).astype(float).any(axis=1)].reset_index(drop=True)

    # Plotting
    fig = go.Figure()

    for idx, row in df_percent.iterrows():
        language = row["language"]
        denominator_value = df.loc[idx, "LR"]

        percent_values = row[levels]
        numerator_values = df.loc[idx, levels]

        # Prepare custom hover data
        custom_data = [
            [level, num, denominator_value, language]
            for level, num in zip(levels, numerator_values)
        ]

        fig.add_trace(go.Scatter(
            x=levels,
            y=percent_values,
            mode='lines+markers',
            name=language,
            customdata=custom_data,
            hovertemplate=(
                "Language: %{customdata[3]}<br>"
                "Level: %{x}<br>"
                "Percentage: %{y:.2f}%<br>"
                "%{customdata[0]}: %{customdata[1]}<br>"
                "LR: %{customdata[2]}<extra></extra>"
            )
        ))

    fig.update_layout(
        title="Percentage of LR by Language",
        xaxis_title="Levels",
        yaxis_title="Percentage of LR (%)",
        yaxis=dict(tickformat=".2f"),
        template="plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)
    return df_percent

@st.cache_data(ttl="1d", show_spinner=False)
def top_and_bottom_languages_per_level(selection, min_LR):
    if selection == "Top performing":
        ascending = False
    else:
        ascending = True
    
    languages = users.get_language_list()
    user_cohort_list_cr = metrics.get_user_cohort_list(
        languages=languages,
        app=["CR"]
    )
    
    df = metrics.build_funnel_dataframe(index_col="language", languages=languages,app=["CR"],user_list=user_cohort_list_cr)

    # Remove anything where Learners Reached is less than 5000 (arbitrary to have a decent sample size)
    df = df[df["LR"] > min_LR]

    df = metrics.add_level_percents(df)

    dfDCLR = (
        df.sort_values(by="DC over LR", ascending=ascending)
        .head(10)
        .loc[:, ["DC over LR", "language"]]
    ).reset_index(drop=True)

    dfTSDC = (
        df.sort_values(by="TS over DC", ascending=ascending)
        .head(10)
        .loc[:, ["TS over DC", "language"]]
    ).reset_index(drop=True)
    dfSLTS = (
        df.sort_values(by="SL over TS", ascending=ascending)
        .head(10)
        .loc[:, ["SL over TS", "language"]]
    ).reset_index(drop=True)
    dfPCSL = (
        df.sort_values(by="PC over SL", ascending=ascending)
        .head(10)
        .loc[:, ["PC over SL", "language"]]
    ).reset_index(drop=True)
    dfLAPC = (
        df.sort_values(by="LA over PC", ascending=ascending)
        .head(10)
        .loc[:, ["LA over PC", "language"]]
    ).reset_index(drop=True)
    dfRALA = (
        df.sort_values(by="RA over LA", ascending=ascending)
        .head(10)
        .loc[:, ["RA over LA", "language"]]
    ).reset_index(drop=True)
    dfGCRA = (
        df.sort_values(by="GC over RA", ascending=ascending)
        .head(10)
        .loc[:, ["GC over RA", "language"]]
    ).reset_index(drop=True)

    
    df_table = pd.DataFrame(columns=["Event", "First", "Second", "Third", "Fourth", "Fifth"])

    # List of dataframes and corresponding row labels
    dataframes = [
        ("Download Completed", dfDCLR, "DC over LR"),
        ("Tapped Start", dfTSDC, "TS over DC"),
        ("Selected Level", dfSLTS, "SL over TS"),
        ("Puzzle Completed", dfPCSL, "PC over SL"),
        ("Learner Acquired", dfLAPC, "LA over PC"),
        ("Reader Acquired", dfRALA, "RA over LA"),
        ("Game Completed", dfGCRA, "GC over RA"),
    ]

    # Generate rows dynamically
    for label, df, column in dataframes:
        row = [label] + [
            f"{df['language'].loc[i]}, {df[column].loc[i]:.2f}%" for i in range(5)
        ]
        df_row = pd.DataFrame([row], columns=df_table.columns)  # Ensure columns match
        df_table = pd.concat([df_table, df_row], ignore_index=True)  # Ignore index to prevent conflicts

    # Display the dataframe in Streamlit without index
    st.dataframe(df_table)


#Added user_list which is a list of cr_user_id to filter with

def create_funnels(
    countries_list=["All"],
    daterange=None,
    languages=["All"],
    app_versions="All",
    key_prefix="abc",
    app=["CR"],
    funnel_size="large",  # "compact", "medium", or "large"
    user_list=[]
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

    # Default fallback
    if funnel_size not in funnel_variants:
        funnel_size = "large"

    stats = funnel_variants[funnel_size]["stats"]
    titles = funnel_variants[funnel_size]["titles"]

    # Override stats/titles for Unity app — always use "compact"
    if  "Unity" in app:
        stats = funnel_variants["compact"]["stats"]
        titles = funnel_variants["compact"]["titles"]
        funnel_size = "compact"

    if daterange is None:
        from datetime import datetime, timedelta
        daterange = [datetime.today() - timedelta(days=30), datetime.today()]

    if len(daterange) == 2:
        start = daterange[0].strftime("%b %d, %Y")
        end = daterange[1].strftime("%b %d, %Y")
        st.caption(f"{start} to {end}")

        metrics_data = {
            stat: metrics.get_totals_by_metric(
                daterange,
                stat=stat,
                cr_app_versions=app_versions,
                language=languages,
                countries_list=countries_list,
                app=app,
                user_list=user_list
            )
            for stat in stats
        }

        # Convert counts to a list for consistent indexing
        counts = [metrics_data[stat] for stat in stats]

        # Only calculate percent_of_second if funnel_size == "large"
        percent_of_second = None
        if funnel_size == "large" and len(counts) > 1 and counts[1]:
            second_val = counts[1]
            percent_of_second = [
                (100 * c / second_val) if second_val != 0 else None for c in counts
            ]

        funnel_data = {
            "Title": titles,
            "Count": counts,
        }
        if percent_of_second is not None:
            funnel_data["PercentOfSecond"] = percent_of_second

        fig = create_engagement_figure(
            funnel_data, key=f"{key_prefix}-5", funnel_size=funnel_size
        )
        st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}-6")

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
            "user_count": ("cr_user_id", "nunique")
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
        xaxis=dict(rangeslider=dict(visible=True))
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