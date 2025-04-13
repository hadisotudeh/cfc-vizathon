import streamlit as st
from PIL import Image
from streamlit.components.v1 import html
import time

# Set page configuration
st.set_page_config(
    page_title="Performance Dashboard",
    page_icon="static/logo.jpg",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Display banner with logo and title
_,col1, col2,_ = st.columns([0.5,4,0.5,0.5])
with col1:
    st.title("Welcome to the Performance Dashboard")
with col2:
    image = Image.open("static/logo.jpg")
    st.image(image, width=100)
# Custom card function with D3DEEF background

# Custom card function
def create_card(icon, title, content, page):
    # Use markdown to create a clickable card
    card_html = f"""
    <a href="{page}" target="_self" style="text-decoration: none; color: inherit;">
        <div style="
            background: white;
            border: 0.5px solid black;
            border-radius: 10px;
            padding: 15px;
            height: 240px;
            margin-bottom: 20px;
            text-align: left;
        ">
            <h3>{icon} {title}</h3>
            <p>{content}</p>
            <p style="color: #3498db">Explore</p>
        </div>
    </a>
    """
    st.markdown(card_html, unsafe_allow_html=True)
# Create 3 columns with equal spacing
col1, col2, col3 = st.columns(3)

# First column cards
with col1:
    create_card("🏃‍♂️", "Load Demand", 
               "Games & matches played, season availability, training sessions and load.",
               "Load_Demand")
    st.write("")
    create_card("👤", "Biography", 
               "Players details such as photo, nationality, position, age, team, league.",
               "Biography")
    st.write("")
    create_card("📋", "Individual Priority", 
               "Individual priority areas are identified and reviewed by the player and the support team.",
               "Individual_Priority")


# Second column cards
with col2:
    create_card("🏥", "Injury History", 
               "Current injury status, injury risk category, most recent injury.",
               "Injury_History")
    st.write("")
    create_card("🛌", "Recovery", 
               "Nutrition, performance behaviour adherence, sleep, wellness.",
               "Recovery")
    st.write("")
    create_card("🔎", "Case Explorer", 
                "Player data case exploration from multiple sources with filtering and color-coded visualization.",
                "Case_Explorer")

# Third column cards
with col3:
    create_card("💪", "Physical Development", 
               "Physical test capabilities, development plans, strength & conditioning logs.",
               "Physical_Development")
    st.write("")
    create_card("🌍", "External Factors", 
               "Outside influences that may impact an individual's performance.",
               "External_Factors")
    st.write("")
    create_card("📕", "Help", 
               "Platform features, navigation, and data documentation.",
               "Help")

# Add footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center;">
        Developed by <a href="https://www.linkedin.com/in/hadisotudeh" target="_blank">Hadi Sotudeh</a>
    </div>
    """,
    unsafe_allow_html=True
)