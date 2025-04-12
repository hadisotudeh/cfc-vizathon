#wikipedia retrival of info
import streamlit as st
import wikipediaapi
import requests
from bs4 import BeautifulSoup
import re
from collections import OrderedDict
from utils import get_chelsea_players, get_wikidata_metadata, get_wikidata_entity

@st.cache_data(ttl=300)
def get_biography_and_image(player_name, player2URL):
    """Scrapes detailed player information from Wikipedia."""
    url = player2URL[player_name]
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        infobox = soup.find('table', {'class': 'infobox'})
        infobox_img = infobox.find('img')

        if infobox_img and infobox_img.get('src'):
            photo_section = "https:" + infobox_img['src']
        else:
            photo_section = None
        
        data = {}
        if infobox:
            for row in infobox.find_all('tr'):
                if row.find('th'):
                    key = row.find('th').get_text(strip=True)
                    value = row.find('td').get_text(" ", strip=True) if row.find('td') else None
                    data[key] = value
        
        
        return photo_section, data
        
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

@st.cache_data(ttl=300)
def get_career_sections(player_name, player2URL):
    """Extracts career sections from Wikipedia with Cole Palmer's page structure in mind."""
    try:
        url = player2URL[player_name]
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        career_data = {
            "Youth career": [],
            "Senior career": [],
            "International career": []
        }

        # Find all section headers
        for header in soup.find_all(['h2', 'h3']):
            span = header.find('span', {'class': 'mw-headline'})
            if not span:
                continue
                
            header_text = span.get_text(strip=True)
            
            # Youth career (often in bullets)
            if "Youth career" in header_text:
                ul = header.find_next('ul')
                if ul:
                    career_data["Youth career"] = [
                        li.get_text(' ', strip=True).replace('\xa0', ' ') 
                        for li in ul.find_all('li')
                    ]
            
            # Senior career (table format)
            elif "Senior career" in header_text:
                table = header.find_next('table', {'class': 'wikitable'})
                if table:
                    career_data["Senior career"] = parse_career_table(table)
            
            # International career (table format)
            elif "International career" in header_text:
                table = header.find_next('table', {'class': 'wikitable'})
                if table:
                    career_data["International career"] = parse_career_table(table)
        
        return career_data

    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return None

def parse_career_table(table):
    """Parses Wikipedia career tables with proper headers."""
    rows = table.find_all('tr')
    if not rows:
        return []
    
    # Get headers
    headers = [th.get_text(' ', strip=True) for th in rows[0].find_all(['th', 'td'])]
    
    data = []
    for row in rows[1:]:
        cols = [col.get_text(' ', strip=True).replace('\xa0', ' ') for col in row.find_all(['th', 'td'])]
        if cols:
            if len(headers) == len(cols):
                data.append(dict(zip(headers, cols)))
            else:
                data.append(cols)
    return data

def display_career_info(career_info):
    """Displays career info in Wikipedia-style format in Streamlit."""
    st.markdown("""
    <style>
    .section-title {
        font-size: 1.3em;
        font-weight: bold;
        border-bottom: 1px solid #a2a9b1;
        margin: 1em 0 0.5em 0;
    }
    .career-list {
        margin-left: 1.5em;
    }
    table.wikitable {
        width: 100%;
        border-collapse: collapse;
        margin: 1em 0;
    }
    table.wikitable th {
        background-color: #f8f9fa;
        text-align: left;
        padding: 0.4em;
        border: 1px solid #a2a9b1;
    }
    table.wikitable td {
        padding: 0.4em;
        border: 1px solid #a2a9b1;
    }
    </style>
    """, unsafe_allow_html=True)

    for section, data in career_info.items():
        if not data:
            continue
            
        st.markdown(f'<div class="section-title">{section}</div>', unsafe_allow_html=True)
        
        if section == "Youth career":
            st.markdown('<ul class="career-list">' + 
                       ''.join(f'<li>{item}</li>' for item in data) + 
                       '</ul>', unsafe_allow_html=True)
        else:
            if isinstance(data[0], dict):  # Table with headers
                headers = list(data[0].keys())
                rows = [list(item.values()) for item in data]
            else:  # Simple table
                headers = ["Year", "Team", "Apps", "Goals"] if len(data[0]) >= 4 else ["Year", "Team"]
                rows = data
            
            # Create markdown table
            table = "| " + " | ".join(headers) + " |\n"
            table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
            for row in rows:
                table += "| " + " | ".join(row) + " |\n"
            
            st.markdown(table)

def display_sections(sections, level=0):
    for section in sections:
        if section.title.lower() in ["references", "external links"]:
            continue

        # Skip empty sections
        if not section.text.strip():
            continue
        
        header = "#" * (level + 2)  # H2, H3, ...
        st.markdown(f"{header} {section.title}:")
        st.markdown(section.text.replace('\n', '  \n\n'))

        # Recursively display subsections
        if section.sections:
            display_sections(section.sections, level + 1)

st.set_page_config(page_title="Player Bio", page_icon="👤", layout="wide")

with st.sidebar:
    st.header("🎯 Select a Player")
    players, player2URL = get_chelsea_players()
    selected_player = st.selectbox("Choose a Chelsea player:", players, index=players.index("Cole Palmer"))

st.title(f"Player Bio Live from [Wikipedia]({player2URL[selected_player]})")

if selected_player:
    st.subheader(selected_player)
    photo_section, player_data = get_biography_and_image(selected_player, player2URL)
    wikipedia_title = player2URL[selected_player].split("/")[-1]

    wikidata_id = get_wikidata_entity(wikipedia_title)
    wikidata_dict = get_wikidata_metadata(wikidata_id)

    col1, col2, col3 = st.columns([1, 2, 1.8])
    with col1:
        if photo_section:
            st.image(photo_section, width=180)
        else:
            st.warning("No image available.")
    with col3:
        # Create Wikipedia-style layout
        st.markdown("""
        <style>
        .info-title {
            background-color: #D3DEEF;
            text-align: center;
            font-weight: bold;
            padding: 5px;
        }
        .info-row {
            display: flex;
            margin-bottom: 5px;
        }
        .info-label {
            font-weight: bold;
            min-width: 120px;
        }
        .section-title {
            border-bottom: 1px solid #a2a9b1;
            font-size: 18px;
            font-weight: bold;
            margin: 15px 0 10px 0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Personal Information Section
        st.markdown('<div class="info-box"><div class="info-title">Playing Career</div>', unsafe_allow_html=True)
        for row in wikidata_dict["sports_teams_played_for"]:        
            st.markdown(f"""
            <div class="info-row">
                <div>{row.replace("?","now").replace("national","").replace(".","").replace("under-","U").replace("association football team","national team").replace("-"," - ")}</div>
            </div>
            """, unsafe_allow_html=True)
    with col2:
        # Remove None values and empty keys
        clean_data = {k: v for k, v in player_data.items() if v is not None and k != ''}
        text = re.sub(r"\s*\[\s*\d+\s*\]\s*", "", clean_data['Date of birth'])
        clean_data['Date of birth'] = re.sub(r"\([^()]*\)", "", text, count=1).strip()
        text = ", ".join([x.strip() for x in clean_data['Place of birth'].split(",")])
        clean_data['Place of birth'] = re.sub(r"\[\s*\d+\s*\]", "", text).strip()
        if "Height" in clean_data:
            matched = re.search(r"(\d\.\d+)\s?m", clean_data['Height'])
            clean_data['Height'] = f"{matched.group(1)}m" if matched else None

        clean_data['Position(s)'] = ", ".join(x.strip() for x in clean_data['Position(s)'].split("[")[0].split(" , "))

        # Create Wikipedia-style layout
        st.markdown("""
        <style>
        .info-title {
            background-color: #D3DEEF;
            text-align: center;
            font-weight: bold;
            padding: 5px;
        }
        .info-row {
            display: flex;
            margin-bottom: 5px;
        }
        .info-label {
            font-weight: bold;
            min-width: 120px;
        }
        .section-title {
            border-bottom: 1px solid #a2a9b1;
            font-size: 18px;
            font-weight: bold;
            margin: 15px 0 10px 0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Personal Information Section
        st.markdown('<div class="info-box"><div class="info-title">Personal information</div>', unsafe_allow_html=True)
        
        personal_info_fields = ['Date of birth', 'Place of birth']
        for field in personal_info_fields:
            if field in clean_data:
                st.markdown(f"""
                <div class="info-row">
                    <div class="info-label">{field}</div>
                    <div>{clean_data[field]}</div>
                </div>
                """, unsafe_allow_html=True)
        
        related_wikidata_field = ['country_of_citizenship', 'native_language']
        for key in ["native_language","languages_spoken"]:
            if isinstance(wikidata_dict[key], str):
                wikidata_dict[key] = [wikidata_dict[key]]

        langs = list(OrderedDict.fromkeys(wikidata_dict["native_language"] + wikidata_dict["languages_spoken"]))
        if len(langs) > 1:
            wikidata_dict["native_language"] = ", ".join(langs)
        else:
            wikidata_dict["native_language"] = langs[0]

        wikidata_mapping = {"country_of_citizenship": "Country", 'native_language': "Language"}
        for field in related_wikidata_field:
            value = wikidata_dict[field]
            if value:
                st.markdown(f"""
                <div class="info-row">
                    <div class="info-label">{wikidata_mapping[field]}</div>
                    <div>{value}</div>
                </div>
                """, unsafe_allow_html=True)
        
        personal_info_fields = ['Height', 'Position(s)']
        for field in personal_info_fields:
            if field in clean_data:
                st.markdown(f"""
                <div class="info-row">
                    <div class="info-label">{field}</div>
                    <div>{clean_data[field]}</div>
                </div>
                """, unsafe_allow_html=True)


        st.markdown('</div>', unsafe_allow_html=True)
        
        # Team Information Section
        st.markdown('<div class="info-box"><div class="info-title">Team information</div>', unsafe_allow_html=True)
        
        team_info_fields = ['Current team', 'Number']
        for field in team_info_fields:
            if field in clean_data:
                st.markdown(f"""
                <div class="info-row">
                    <div class="info-label">{field}</div>
                    <div>{clean_data[field]}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)        

    # Wikipedia API setup
    wiki_wiki = wikipediaapi.Wikipedia(
        language='en',
        user_agent='ChelseaFCBioViewer/1.0 (contact: "your_email@example.com)'
    )
    page = wiki_wiki.page(wikipedia_title)
    formatted_summary = page.summary.replace('\n', '  \n\n')
    if formatted_summary:
        st.markdown("## Summary:")
        st.markdown(formatted_summary)
    display_sections(page.sections)