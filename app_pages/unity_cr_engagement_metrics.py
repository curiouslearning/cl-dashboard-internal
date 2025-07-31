import streamlit as st
import settings
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import users
import metrics
from settings import get_logger

settings.initialize()
settings.init_user_list()

ui.display_definitions_table("Data Notes",ui.data_notes)
countries_list = users.get_country_list()

ui.colorize_multiselect_options()

logger = settings.get_logger()

# --- Filter Row ---
col_date, col_lang, col_country = st.columns((1, 1, 1), gap="large")

with col_date:
    st.caption("Select a Date")
    selected_date, option = ui.calendar_selector(placement="middle")
    daterange = ui.convert_date_to_range(selected_date, option)

with col_lang:
    languages = users.get_language_list()
    language = ui.single_selector(
        languages, placement="middle", title="Select a language", key="acq-1"
    )

with col_country:
    countries_list = ui.multi_select_all(
        countries_list,
        title="Country Selection",
        key="acq-2",
        placement="middle"
    )

# --- Date Display ---
if len(daterange) == 2:
    start = daterange[0].strftime("%b %d, %Y")
    end = daterange[1].strftime("%b %d, %Y")
    st.write(f"{start} to {end}")

# --- Header Row ---
col_unity_head, col_cr_head = st.columns((1, 1), gap="large")
with col_unity_head:
    st.markdown("<strong><div style='text-align: center;'>Unity</div></strong>", unsafe_allow_html=True)
with col_cr_head:
    st.markdown("<strong><div style='text-align: center;'>Curious Reader</div></strong>", unsafe_allow_html=True)


if len(daterange) == 2 and countries_list:

    # --- Get user cohorts ---
    user_cohort_list_unity = metrics.get_user_cohort_list(
        daterange=daterange,
        languages=language,
        countries_list=countries_list,
        app="Unity"
    )
    user_cohort_list_cr = metrics.get_user_cohort_list(
        daterange=daterange,
        languages=language,
        countries_list=countries_list,
        app="CR"
    )

    # --- Calculate metrics ---
    metrics_unity = {
        "Avg # Sessions / User": metrics.calculate_average_metric_per_user(user_cohort_list_unity, app="Unity", column_name="engagement_event_count"),
        "Avg Total Play Time / User": metrics.calculate_average_metric_per_user(user_cohort_list_unity, app="Unity", column_name="total_time_minutes"),
        "Avg Session Length / User": metrics.calculate_average_metric_per_user(user_cohort_list_unity, app="Unity", column_name="avg_session_length_minutes"),
        "Active Span / User": metrics.calculate_average_metric_per_user(user_cohort_list_unity, app="Unity", column_name="active_span"),
    }

    metrics_cr = {
        "Avg # Sessions / User": metrics.calculate_average_metric_per_user(user_cohort_list_cr, app="CR", column_name="engagement_event_count"),
        "Avg Total Play Time / User": metrics.calculate_average_metric_per_user(user_cohort_list_cr, app="CR", column_name="total_time_minutes"),
        "Avg Session Length / User": metrics.calculate_average_metric_per_user(user_cohort_list_cr, app="CR", column_name="avg_session_length_minutes"),
        "Active Span / User": metrics.calculate_average_metric_per_user(user_cohort_list_cr, app="CR", column_name="active_span"),
    }

    # --- Metric Display Columns ---
    col_unity_metrics, col_cr_metrics = st.columns((1, 1), gap="large")

    with col_unity_metrics:
        for label, value in metrics_unity.items():
            unit = " days" if "Span" in label else " min" if "Time" in label or "Length" in label else ""
            st.metric(label=label, value=f"{value:.2f}{unit}")

    with col_cr_metrics:
        for label, value in metrics_cr.items():
            unit = " days" if "Span" in label else " min" if "Time" in label or "Length" in label else ""
            st.metric(label=label, value=f"{value:.2f}{unit}")

            