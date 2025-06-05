import sqlite3
import pandas as pd
import requests
import json
import time
from codecarbon import EmissionsTracker  # type: ignore # ✅ NEW: Import CodeCarbon tracker

# Connect to DB
conn = sqlite3.connect('financial_news.db')
cursor = conn.cursor()

# Add 'summary' column if missing
cursor.execute("PRAGMA table_info(news);")
columns = [col[1] for col in cursor.fetchall()]
if 'summary' not in columns:
    print("[INFO] Adding 'summary' column...")
    cursor.execute("ALTER TABLE news ADD COLUMN summary TEXT;")
    conn.commit()

# Create KPI table if not exists
cursor.execute("""
    CREATE TABLE IF NOT EXISTS summary_metrics (
        news_id INTEGER,
        summary_length INTEGER,
        response_time REAL,
        model TEXT,
        FOREIGN KEY(news_id) REFERENCES news(id)
    )
""")
conn.commit()

# Load content only for rows without summary
df = pd.read_sql_query("SELECT id, content FROM news WHERE summary IS NULL", conn)
df = df.dropna(subset=['content'])
df = df[df['content'].str.len() > 200]

# Start the CodeCarbon tracker before inference begins
tracker = EmissionsTracker(
    project_name="financial_news_summary",  # Tag this run
    measure_power_secs=1                   # Frequency of power measurement
)
tracker.start()  # ✅ Starts monitoring CPU/GPU usage and energy intensity

# Ollama summarizer
def summarize_with_ollama(text, model='llama2'):
    headers = {"Content-Type": "application/json"}
    data = {
        "model": model,
        "prompt": f"Summarize this financial news article in 3-4 lines:\n\n{text}",
        "stream": False
    }

    try:
        start = time.time()
        response = requests.post("http://localhost:11434/api/generate", headers=headers, data=json.dumps(data))
        response.raise_for_status()
        elapsed = round(time.time() - start, 2)

        summary = response.json()['response'].strip()
        return summary, elapsed
    except Exception as e:
        print(f"[ERROR] {e}")
        return None, None

# Summarize and track KPIs
for _, row in df.iterrows():
    summary, latency = summarize_with_ollama(row['content'])

    if summary:
        summary_len = len(summary.split())
        print(f"[INFO] Writing summary + KPIs for ID {row['id']}")

        cursor.execute("UPDATE news SET summary = ? WHERE id = ?", (summary, row['id']))
        cursor.execute("INSERT INTO summary_metrics (news_id, summary_length, response_time, model) VALUES (?, ?, ?, ?)", 
                       (row['id'], summary_len, latency, 'llama2'))
        conn.commit()

# Stop tracking and print the carbon emission for this run
emissions = tracker.stop()
print(f"[INFO] Total CO₂ emissions: {emissions:.6f} kg")  # ✅ Reports emissions in kilograms

conn.close()
print("[DONE] Summaries, KPIs, and emissions tracking complete.")
