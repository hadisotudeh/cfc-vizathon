import streamlit as st
from config import newsapi
from utils import get_chelsea_players, get_ai_analysis
import warnings
from datetime import datetime, timedelta
from newspaper import Article
from textblob import TextBlob
import nltk
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import re
from nltk.corpus import stopwords
from collections import defaultdict
import numpy as np

# Download NLTK data
nltk.download('stopwords')
nltk.download('punkt')

warnings.filterwarnings("ignore")

st.set_page_config(page_title="External Factors", page_icon="🌍", layout="wide")

@st.cache_data(ttl=300)
def get_news_results(selected_player):
    today = datetime.now()
    past_week = today - timedelta(days=7)
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

def extract_article_content(url, fallback_content=""):
    try:
        article = Article(url, fetch_images=False)
        article.download()
        article.parse()
        if len(article.text) > 100:  # Only use if substantial content
            return article.text
        return fallback_content
    except:
        return fallback_content

def analyze_sentiment(text):
    if not text or len(text.split()) < 3:
        return "neutral", 0.0
    try:
        analysis = TextBlob(text)
        polarity = analysis.sentiment.polarity
        if polarity > 0.1:
            return "positive", polarity
        elif polarity < -0.1:
            return "negative", polarity
        return "neutral", polarity
    except:
        return "neutral", 0.0

def get_sentiment_badge(sentiment, score):
    color = {
        "positive": "🟢",
        "negative": "🔴",
        "neutral": "⚪"
    }.get(sentiment, "⚪")
    return f"{color}"

def generate_wordcloud(text):
    st.subheader("🔠 Larger words appear more often in the news coverage")
    
    # Enhanced stopwords set
    base_stopwords = set(stopwords.words('english'))
    custom_stopwords = {
        'getting', 'many', 'one', 'two', 'three', 'four', 'five', 'six',
        'seven', 'eight', 'nine', 'ten', 'also', 'us', 'would', 'could',
        'said', 'says', 'say', 'like', 'even', 'still', 'yet', 'may',
        'might', 'often', 'every', 'however', 'since', 'without', 'within',
        'made', 'held', 'next', 'take', 'getty'
    }
    stop_words = base_stopwords.union(custom_stopwords)

    wordcloud = WordCloud(
        width=1600,
        height=800,
        background_color='white',
        stopwords=stop_words,
        scale=2,
        collocations=False,
        colormap='tab10',
        max_words=70,
        margin=20,
        prefer_horizontal=0.85,
        min_word_length=4,
        relative_scaling=0.5,
        regexp=r'\w{4,}',
        repeat=False  # Important to prevent color reuse
    ).generate(text)

    # High quality display
    plt.figure(figsize=(12, 6), dpi=300)
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.tight_layout(pad=0)
    st.pyplot(plt, clear_figure=True)

with st.sidebar:
    st.header("🎯 Select a Player")
    players, _ = get_chelsea_players()
    selected_player = st.selectbox("Choose a Chelsea player:", players, index=players.index("Christopher Nkunku"))

try:
    results = get_news_results(selected_player)

    st.header(f"{selected_player}: Latest News (Past 7 Days)")
    n_articles = results["totalResults"]
    st.markdown(f"Found {n_articles} articles - Live news data from [NewsAPI](https://newsapi.org)")

    # Generate word cloud from all content
    all_text = " ".join([art.get('content', '') or art.get('description', '') for art in results['articles']])
    # Remove technical terms/artifacts
    all_text = re.sub(r'\b(chars?|encoding|xml|html)\b', '', all_text, flags=re.IGNORECASE)
    # Remove special characters (optional)
    all_text = re.sub(r'[^\w\s-]', ' ', all_text) 

    generate_wordcloud(all_text)

    st.subheader("AI Sports Journalist's Findings: 💻")

    st.write(get_ai_analysis(df_json=None, mode="external_factors", selected_player=selected_player, news=all_text))

    st.subheader("📰 Article List: Color-coded by Sentiment Analysis")

    for article in results['articles']:
        source = article['source']['name']
        title = article['title']    
        description = article['description']
        url = article['url']
        urlToImage = article["urlToImage"]
        published_at = article['publishedAt']
        content = article.get('content', '')
        
        # Enhanced content extraction
        full_content = extract_article_content(url, content or description)
        sentiment, score = analyze_sentiment(full_content)
        
        # Format date
        try:
            date_obj = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
            formatted_date = date_obj.strftime("%B %d, %Y %H:%M")
        except:
            formatted_date = published_at
        
        # Article display
        with st.container():
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if urlToImage:
                    st.image(urlToImage, width=200)
                else:
                    st.warning("No image available")
            
            with col2:
                st.markdown(f"### [{title}]({url}) {get_sentiment_badge(sentiment, score)}")
                st.caption(f"**Source:** {source} | **Published:** {formatted_date}")
                
                if full_content:
                    with st.expander("Read more"):
                        st.write(full_content)
        
            st.markdown("---")
except:
    st.error(f"Error fetching data for {selected_player}")