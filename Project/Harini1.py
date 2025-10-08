from dotenv import load_dotenv
import os

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_KEY")
NEWS_KEY = os.getenv("NEWS_KEY") 

import requests
import pandas as pd
from datetime import datetime, timedelta

def get_news(api_key, query, from_date, to_date):
    """Fetches news articles from NewsAPI."""
    url = "https://newsapi.org/v2/everything" # get API for news
    #NEWS_KEY=5342a45703ea4b178c8e83c7f8927512 

    params = {
        'q': query,
        'from': from_date,
        'to': to_date,
        'language': 'en',
        'sortBy': 'publishedAt',
        'apiKey': api_key,
        'pageSize': 100  # Max is 100
    }
    
    all_articles = []
    page = 1
    while True:
        params['page'] = page
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"Error fetching data: {response.json().get('message', 'Unknown error')}")
            break
            
        data = response.json()
        articles = data.get('articles', [])
        if not articles:
            break
            
        all_articles.extend(articles)
        
        # NewsAPI developer plan has a limit on how deep you can paginate
        if len(all_articles) >= data.get('totalResults', 0) or page > 5:
            break
        page += 1
        
    df = pd.DataFrame(all_articles)
    if not df.empty:
        df['publishedAt'] = pd.to_datetime(df['publishedAt'])
        df = df[['publishedAt', 'title', 'source']]
        df.rename(columns={'publishedAt': 'date'}, inplace=True)
    return df

# --- Example Usage ---

QUERY = "Apple OR AAPL"
TO_DATE = datetime.now().strftime('%Y-%m-%d')
FROM_DATE = (datetime.now() - timedelta(days=29)).strftime('%Y-%m-%d')

news_df = get_news(NEWS_KEY, QUERY, FROM_DATE, TO_DATE)
print(f"Fetched {len(news_df)} articles.")
print(news_df.head())