import streamlit as st
from rich import print as rprint
from millify import prettify

import settings


settings.initialize()
settings.init_user_list()

def info_row(label, value, color="green"):
    st.markdown(f"<div style='margin-bottom: -10px'><span style='color:{color}; font-weight:500'>{label}</span> {value}</div>", unsafe_allow_html=True)


col1, col2 = st.columns([2,4])
with col1:
    cr_user_id = st.text_input(label="Enter cr_user_id",type="default")
st.write(cr_user_id)


df_cr_users = st.session_state.df_cr_users
df_cr_app_launch = st.session_state.df_cr_app_launch
user = df_cr_app_launch.loc[df_cr_app_launch['cr_user_id'] == cr_user_id]

info_row("Country:", user["country"].iloc[0])
info_row("Language:", user["app_language"].iloc[0])
info_row("First Open:", user["first_open"].iloc[0])

    