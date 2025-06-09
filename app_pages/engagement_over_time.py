import streamlit as st
import users
import settings
import metrics
import ui_widgets as ui
import ui_components as uic

settings.initialize()
settings.init_user_list()
settings.init_cr_app_version_list()

# Get options
languages = users.get_language_list()
countries_list = users.get_country_list()

# Choose number of cohorts to compare
num_cohorts = st.number_input(
    "How many cohorts to compare?", min_value=1, max_value=10, value=2, step=1
)

cohort_inputs = []

# Loop over each cohort configuration
for i in range(num_cohorts):
    st.markdown(f"### Cohort {i + 1}")
    col1, col2 = st.columns(2)

    with col1:
        language = ui.single_selector(
            languages, placement="col", title="Language", key=f"lang_{i}"
        )
        cr_app_versions = ui.app_version_selector(placement="col", key=f"ver_{i}")

    with col2:
        countries = ui.single_selector(
            countries_list, placement="col", title="Country", key=f"country_{i}"
        )

    cohort_label = f"{language} / {countries[0]} / {cr_app_versions}"

    df_user_list = metrics.filter_user_data(
        countries_list=countries,
        stat="LR",
        app="CR",
        cr_app_versions=cr_app_versions,
        language=language,
    )

    if df_user_list.empty:
        st.warning(f"⚠️ Cohort '{cohort_label}' has no users and will be skipped.")
        continue

    cohort_inputs.append((cohort_label, df_user_list))

# Metric selector
metric_choice = st.radio(
    "Select metric to plot:",
    options=["Avg Total Time (minutes)", "Avg Session Count"],
    index=0,
    horizontal=True
)

# Build chart only on button click
if st.button("Build Chart"):
    if cohort_inputs:
        uic.engagement_over_time_chart(
            df_list_with_labels=cohort_inputs,
            metric=metric_choice
        )
    else:
        st.info("No valid cohorts selected to plot.")

