# pages/00_global.py
import streamlit as st

# Apply to all pages
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            min-width: 0px !important;
            max-width: 0px !important;
        }
    </style>
""", unsafe_allow_html=True)