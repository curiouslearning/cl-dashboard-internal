import streamlit as st
from rich import print as rprint
from millify import prettify

import settings


settings.initialize()
settings.init_user_list()

col1, col2 = st.columns([2,4])
with col1:
    cr_user_id = st.text_input(label="Enter cr_user_id",type="default")
st.write(cr_user_id)

