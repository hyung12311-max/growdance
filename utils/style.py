import streamlit as st
import os

LOGO_PATH = "assets/grow_logo.png"

def apply_custom_style():
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background-color: #F7F7F7;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0B1220 0%, #111827 100%) !important;
    }

    [data-testid="stSidebar"] * {
        color: white !important;
        font-weight: 700;
    }

    [data-testid="stSidebarNav"] {
        background-color: transparent !important;
    }

    h1 {
        color: #111827 !important;
        font-weight: 900 !important;
    }

    h2, h3 {
        color: #1F2937 !important;
        font-weight: 800 !important;
    }

    .stButton > button {
        border-radius: 14px !important;
        border: 1px solid #FF7A00 !important;
        background-color: #FF7A00 !important;
        color: white !important;
        font-weight: 800 !important;
        height: 44px;
    }

    .stButton > button:hover {
        background-color: #E86D00 !important;
        color: white !important;
        border: 1px solid #E86D00 !important;
    }

    div[data-testid="stMetric"] {
        background-color: white !important;
        padding: 22px !important;
        border-radius: 20px !important;
        border-left: 8px solid #FF7A00 !important;
        box-shadow: 0px 6px 18px rgba(0,0,0,0.08) !important;
    }

    div[data-testid="stDataFrame"] {
        background-color: white !important;
        border-radius: 16px !important;
        padding: 8px !important;
        box-shadow: 0px 4px 14px rgba(0,0,0,0.05);
    }

    .stTextInput input,
    .stSelectbox div,
    .stDateInput input,
    .stTextArea textarea {
        border-radius: 12px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, use_container_width=True)
        st.markdown("---")