import streamlit as st
from PIL import Image

from utils import adjust_sidebar_width

# Set page configuration
st.set_page_config(
    page_title="CFC Performance Dashboard",
    page_icon="static/logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)
adjust_sidebar_width()

# Display banner with logo and title
_,col1, col2,_ = st.columns([1.5,3,1,1.5])
with col1:
    st.title("Welcome to the CFC Performance Dashboard")
with col2:
    image = Image.open("static/logo.jpg")
    st.image(image, width=100)
# Custom card function with D3DEEF background
def create_card(icon, title, content, page):
    with st.container(border=False):
        container = st.container()
        with container:
            st.markdown(
                f"""
                <a href="{page}" style="text-decoration: none; color: inherit;">
                <div style="border: 0.5px solid black; border-radius: 10px; padding: 15px; height: 240px;">
                    <h3>{icon} {title}</h3>
                    <p>{content}</p>
                    <p style="color: #3498db"> Explore </p>
                </div>
                </a>
                """,
                unsafe_allow_html=True
            )

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
               "Individual priority areas are identified and reviewed by the player and Performance Support Team.",
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
               "Case Explorer",
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
               "Help",
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