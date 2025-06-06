import requests
import sqlite3
import datetime
from datetime import timedelta

import warnings
warnings.filterwarnings('ignore')

# Step 1: Configure API Key and Parameters
API_KEY = 'f02302ebd27f4944b5cae0dc2284619a'  # 🔐 Replace with your actual key
BASE_URL = 'https://newsapi.org/v2/everything'
KEYWORDS = 'finance OR stock OR market'


TODAY = datetime.date.today()
START_DATE = (TODAY - timedelta(days=5)).isoformat()  # last 5 days
TODAY = TODAY.isoformat()
print(f"[DEBUG] Fetching news from {START_DATE} to {TODAY}")


def fetch_news():
    print("[INFO] Fetching financial news from NewsAPI...")
    params = {
    'q': KEYWORDS,
    'from': START_DATE,
    'to': TODAY,
    'language': 'en',
    'sortBy': 'publishedAt',
    'apiKey': API_KEY,
    'pageSize': 20
}
    response = requests.get(BASE_URL, params=params)
    if response.status_code != 200:
        print(f"[ERROR] Failed to fetch news: {response.status_code} - {response.text}")
        return []
    print("[INFO] News fetched successfully.")
    return response.json().get('articles', [])

def store_articles(articles):
    print(f"[INFO] Connecting to SQLite database 'financial_news.db'...")
    conn = sqlite3.connect('financial_news.db')
    c = conn.cursor()

    print("[INFO] Creating table if not exists...")
    c.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            url TEXT,
            publishedAt TEXT,
            source TEXT
        )
    ''')

    print("[INFO] Inserting articles into the database...")
    count = 0
    for article in articles:
        c.execute('''
            INSERT INTO news (title, content, url, publishedAt, source)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            article.get('title'),
            article.get('content'),
            article.get('url'),
            article.get('publishedAt'),
            article.get('source', {}).get('name')
        ))
        count += 1

    conn.commit()
    conn.close()
    print(f"[INFO] {count} articles stored successfully.")

if __name__ == '__main__':
    print("[START] News ingestion pipeline initiated...")
    articles = fetch_news()
    if articles:
        store_articles(articles)
    else:
        print("[WARN] No articles were returned.")
    print("[END] News ingestion pipeline completed.")
