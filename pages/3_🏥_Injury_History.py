import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
from datetime import datetime
import warnings
from utils import get_chelsea_players, get_wikidata_metadata, get_wikidata_entity, adjust_sidebar_width

# Configuration
warnings.filterwarnings("ignore")
st.set_page_config(page_title="Injury History", page_icon="🏥", layout="wide")
adjust_sidebar_width()

# Set headers to mimic a browser visit
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_injury_history(player_id):
    url = f"https://www.transfermarkt.com/player/verletzungen/spieler/{player_id}"
    
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the injuries table
        table = soup.find('table', {'class': 'items'})
        if not table:
            return None
            
        # Extract rows
        rows = table.find_all('tr')[1:]  # skip header row
        injuries = []
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 5:
                injury = {
                    'season': cols[0].get_text(strip=True),
                    'injury': cols[1].get_text(strip=True),
                    'from_date': cols[2].get_text(strip=True),
                    'until_date': cols[3].get_text(strip=True),
                    'days': cols[4].get_text(strip=True),
                    'games_missed': cols[5].get_text(strip=True) if len(cols) > 5 else 'N/A'
                }
                injuries.append(injury)
                
        return injuries, url
        
    except Exception as e:
        st.error(f"Error fetching data for player ID {player_id}: {str(e)}")
        return None

def process_injuries(injuries):
    """Process raw injury data into organized DataFrames by injury type"""
    if not injuries:
        return {}
    
    # Create a DataFrame from all injuries
    df = pd.DataFrame(injuries)
    
    # Convert dates to datetime objects for sorting
    try:
        df['from_date'] = pd.to_datetime(df['from_date'], format='%b %d, %Y', errors='coerce')
        df['until_date'] = pd.to_datetime(df['until_date'], format='%b %d, %Y', errors='coerce')
    except:
        pass
    
    # Group by injury type and count occurrences
    injury_counts = df['injury'].value_counts().to_dict()
    
    # Group by injury type and sort by count (descending)
    injury_types = sorted(df['injury'].unique(), key=lambda x: -injury_counts.get(x, 0))
    injury_dfs = {}
    
    for injury_type in injury_types:
        injury_df = df[df['injury'] == injury_type].copy()
        injury_df = injury_df.sort_values('from_date', ascending=False)
        injury_dfs[injury_type] = injury_df
        
    return injury_dfs

def display_injury_tables(injury_dfs, player_name=""):
    """Display injury DataFrames in Streamlit in a 3-column grid"""
    if not injury_dfs:
        st.warning("No injury data available for this player.")
        return
    
    # Convert the dictionary to a list of tuples (injury_type, df)
    injury_items = list(injury_dfs.items())
    
    # Calculate how many rows we need (2 tables per row)
    num_rows = (len(injury_items) + 2) // 2  # Round up division
    
    for row in range(num_rows):
        # Create columns for this row
        cols = st.columns(2)
        
        # Get up to 2 injuries for this row
        start_idx = row * 2
        end_idx = start_idx + 2
        current_injuries = injury_items[start_idx:end_idx]
        
        # Display each injury in its own column
        for col_idx, (injury_type, df) in enumerate(current_injuries):
            with cols[col_idx]:
                st.subheader(injury_type.title())
                
                # Format the DataFrame for display
                display_df = df.drop(columns=['injury']).reset_index(drop=True)
                display_df.index = display_df.index + 1  # Start index at 1
                
                display_df.rename(columns={"season":"Season", "days":"Days", "games_missed":"Missed"},inplace=True)

                st.dataframe(
                    display_df,
                    column_config={
                        'from_date': st.column_config.DateColumn("From", format="MMM D, YYYY"),
                        'until_date': st.column_config.DateColumn("Until", format="MMM D, YYYY")
                    },
                    use_container_width=True
                )
players, player2URL = get_chelsea_players()
selected_player = st.sidebar.selectbox("Choose a Chelsea player:", players, index=players.index("Reece James"))

st.header(f"{selected_player.title()}'s Injury History:")

wikipedia_title = player2URL[selected_player].split("/")[-1]

wikidata_id = get_wikidata_entity(wikipedia_title)
wikidata_dict = get_wikidata_metadata(wikidata_id)

player_id = wikidata_dict['transfermarkt_id']

with st.spinner(f"Fetching {selected_player}'s injury history"):
    injuries, url = get_injury_history(player_id)
st.write(f"Live from [Transfermarkt]({url})")
if injuries:
    injury_dfs = process_injuries(injuries)
    display_injury_tables(injury_dfs, selected_player)
else:
    st.warning(f"No injury data found for {selected_player}")
