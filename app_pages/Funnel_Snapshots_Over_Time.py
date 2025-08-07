import streamlit as st
import settings
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import users
import datetime as dt


settings.initialize()
from users import ensure_user_data_initialized
ensure_user_data_initialized()

ui.display_definitions_table("Definitions",ui.level_percent_definitions)


countries_list = users.get_country_list()


st.write("Select date")    
selected_date, option = ui.calendar_selector(placement="middle", key="fa-3", index=4)
daterange = ui.convert_date_to_range(selected_date, option)

df = users.get_language_list()

selected_languages = ui.multi_select_all(
    df, placement="middle", title="Select languages", key="fa-1"
)

toggle = st.radio(
            options=[
                "Funnel totals",
                "Percent remaining",
            ],
            label="Graph option",
            horizontal=True,
            index=1,
            key="fsot",
            
        )

if len(selected_languages) > 0 and len(daterange) == 2:
    # Funnel snapshots started 9/11/2024
    daterange[0] = max(daterange[0], dt.date(2025, 3, 22))
    
    start = daterange[0].strftime("%b %d, %Y")
    end = daterange[1].strftime("%b %d, %Y")
    st.write("Timerange: " + start + " to " + end)
    df = users.get_funnel_snapshots(daterange=daterange,languages=selected_languages)
    with st.spinner("Calculating..."):
        uic.funnel_change_line_chart(df,toggle)
        csv = ui.convert_for_download(df)
        st.download_button(label="Download CSV",data=csv,file_name="funnel_snapshots.csv",key="fs-10",icon=":material/download:",mime="text/csv")

else:
    st.write("Please select at least one language and a valid date range")

