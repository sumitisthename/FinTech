# Step 2: Fetch News from NewsAPI
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
    print(f"[DEBUG] API URL: {response.url}")
    print(f"[DEBUG] Response Text: {response.text[:300]}...")  
    return response.json().get('articles', [])

# Step 3: Save Articles to SQLite
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