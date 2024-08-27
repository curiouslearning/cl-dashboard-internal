import streamlit as st
import ui_components as uic

st.title("Multi Language  Funnel (hardcoded) ")


funnel_data = {
    "Title": [
        "CR First Open, distinct",
        "Tapped on FTM, distinct",
        "Distinct users download complete or better",
        "Distinct users choosing multiple languages",
        "Distinct users completing levels in multiple languages"],

    "Count": [476929,369732,285744,32688,7891],
}


fig = uic.create_engagement_figure(funnel_data, "acq-5")
st.plotly_chart(fig, use_container_width=True)

funnel_data = {
    "Title": [

        "Tapped on FTM, distinct",
        "Distinct users download complete or better",
        "Distinct users choosing multiple languages",
        "Distinct users completing levels in multiple languages"],

    "Count": [369732,285744,32688,7891],
}


fig = uic.create_engagement_figure(funnel_data, "acq-5")
st.plotly_chart(fig, use_container_width=True)