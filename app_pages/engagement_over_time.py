import streamlit as st
import users
import ui_widgets as ui
import ui_components as uic
from users import ensure_user_data_initialized
from settings import initialize,init_cr_app_version_list,default_daterange
from metrics import get_filtered_cohort

initialize()
init_cr_app_version_list()
ensure_user_data_initialized()

# Get options
languages = users.get_language_list()
countries_list = users.get_country_list()

# Choose number of cohorts to compare
num_cohorts = st.number_input(
    "How many cohorts to compare?", min_value=1, max_value=10, value=2, step=1
)

cohort_inputs = []
apps = ui.get_apps()

# Loop over each cohort configuration
for i in range(num_cohorts):
    st.markdown(f"### Cohort {i + 1}")
    col1, col2 = st.columns(2)

    with col1:
        language = ui.single_selector(
            languages, title="Language", key=f"lang_{i}"
        )
        app = ui.single_selector(apps,title="Select an App", key=f"app{i}",include_All=False,index=1)

    with col2:
        countries = ui.single_selector(
            countries_list,  title="Country", key=f"country_{i}"
        )
        

    cohort_label = f"{language} / {countries[0]} / {app}"

    user_cohort_df, _ = get_filtered_cohort(app=app, language=language, countries_list=countries_list,daterange=default_daterange)


    if user_cohort_df.empty:
        st.warning(f"⚠️ Cohort '{cohort_label}' has no users and will be skipped.")
        continue

    cohort_inputs.append((cohort_label, user_cohort_df))

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

