import streamlit as st
from config import newsapi
from utils import get_chelsea_players
import warnings
from datetime import datetime, timedelta
warnings.filterwarnings("ignore")

st.set_page_config(page_title="External Factors", page_icon="🌍", layout="wide")

@st.cache_data(ttl=300)  # Cache for 300 seconds (5 minutes)
def get_news_results(selected_player):
    # Calculate dates (today and 30 days ago)
    today = datetime.now()
    past_week = today - timedelta(days=7)

    # Format dates as YYYY-MM-DD strings
    date_format = "%Y-%m-%d"
    today_str = today.strftime(date_format)
    past_week_str = past_week.strftime(date_format)

    results = newsapi.get_everything(
        q=selected_player,
        from_param=past_week_str,
        to=today_str,
        language='en',
        sort_by='publishedAt'
    )
    return results

with st.sidebar:
    st.header("🎯 Select a Player")
    players, _ = get_chelsea_players()
    selected_player = st.selectbox("Choose a Chelsea player:", players, index=players.index("Cole Palmer"))

results = get_news_results(selected_player)

st.header(f"{selected_player}: Latest News & Updates (Past 7 Days)")
st.markdown("Live news data from [NewsAPI](https://newsapi.org)")


# results = newsapi.get_top_headlines(q='chelsea', language='en', country='gb', page_size=10, category='sports')
n_articles = results["totalResults"]
st.subheader(f"Found {n_articles} articles")

for article in results['articles']:
    source = article['source']['name']
    title = article['title']    
    description = article['description']
    url = article['url']
    urlToImage = article["urlToImage"]
    published_at = article['publishedAt']
    content = article['content']
    
    # Format the published date
    try:
        date_obj = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
        formatted_date = date_obj.strftime("%B %d, %Y %H:%M")
    except:
        formatted_date = published_at
    
    # Create a card-like layout for each article
    with st.container():
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if urlToImage:
                st.image(urlToImage, width=200)
            else:
                st.warning("No image available")
        
        with col2:
            st.markdown(f"### [{title}]({url})")
            st.caption(f"**Source:** {source} | **Published:** {formatted_date}")
            
            if description:
                with st.expander("Read more"):
                    st.write(description)
    
        st.markdown("---")  # Divider between articles