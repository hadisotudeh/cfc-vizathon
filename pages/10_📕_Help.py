from pathlib import Path
from streamlit_pdf_viewer import pdf_viewer
import streamlit as st
from PIL import Image
import warnings

# Configuration
warnings.filterwarnings("ignore")
st.set_page_config(page_title="Help", page_icon="📕", layout="wide")

st.header("Help Page:")

st.markdown(
    """
    This prototype provides **performance coaches** and **players** with an overview of key performance data across the following areas:

    1. **Biography** – Player identity: photo, nationality, position, age, team, and league.  
    2. **Load Demand** – Match and training load based on GPS KPIs.
    3. **Physical Development** – Test results, development plans, strength & conditioning logs, and priority areas.  
    4. **Recovery** – Insights on sleep, wellness, nutrition, and behavioural adherence.  
    5. **Injury History** – Recent injuries.  
    6. **Individual Priority** – Player-specific focus areas and development needs.  
    7. **External Factors** – Contextual influences such as environment, team dynamics, and motivation.  
    8. **Case Explorer** – Browse and compare tabular performance data.  
    9. **Help** – Reference Chelsea FC's physical performance data sources.
    
    For personalized recommendations, the dashboard includes an "AI Sports Scientist" powered by [Mistral](https://en.wikipedia.org/wiki/Mistral_AI)'s **free** [LLM model](https://docs.mistral.ai/getting-started/models/models_overview). 
    
    This aligns with how AI is already used in elite football, see [AAVA for recovery](https://www.youtube.com/watch?v=s55HF_PKuOk) or [Sevilla FC’s scouting with Llama](https://sevillafc.es/en/actual/news/sevilla-fc-chosen-meta-example-use-artificial-intelligence).

    This dashboard in general is mobile-friendly, built with [Python](https://www.python.org), [Streamlit](https://streamlit.io), [Plotly](https://plotly.com), and [Matplotlib](https://matplotlib.org).
    """
)

# PDF path
pdf_file_path = "static/doc.pdf"

# Sidebar with logo
image = Image.open("static/logo.jpg")
st.sidebar.image(image, use_container_width=True)

# Main content
st.title("Documentation Viewer")

# PDF viewer
pdf_viewer(pdf_file_path)
