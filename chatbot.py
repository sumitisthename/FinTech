import faiss
import pickle
import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer
import requests
import os
import logging
from codecarbon import EmissionsTracker  # ✅ Import emissions tracker

# Set up basic logging config
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

GROQ_API_KEY = "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"  # consider storing securely

# Load model and FAISS index
logging.info("Loading sentence transformer model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

logging.info("Reading FAISS index...")
index = faiss.read_index("faiss_index.index")

logging.info("Loading ID mapping from pickle...")
with open("id_mapping.pkl", "rb") as f:
    id_map = pickle.load(f)

def query_bot(user_query):
    # ✅ Start emissions tracker
    tracker = EmissionsTracker(
        project_name="financial_news_summary",
        measure_power_secs=1,
        output_file="emissions.csv",   
        log_level="info"
    )
    tracker.start()
    logging.info("Started carbon emissions tracking.")

    logging.info(f"Encoding query: {user_query}")
    query_emb = model.encode([user_query])

    logging.info("Performing FAISS search...")
    D, I = index.search(np.array(query_emb), k=5)
    logging.debug(f"Search distances: {D}")
    logging.debug(f"Search indices: {I}")

    logging.info("Connecting to SQLite database...")
    conn = sqlite3.connect("financial_news.db")
    cursor = conn.cursor()

    docs = []
    for idx in I[0]:
        news_id = id_map[idx] if idx in id_map else None
        logging.debug(f"Mapping index {idx} to news ID: {news_id}")
        if news_id is None:
            logging.warning(f"No mapping found for index: {idx}")
            continue

        logging.info(f"Fetching news for ID: {news_id}")
        cursor.execute("SELECT title, summary FROM news WHERE id = ?", (news_id,))
        result = cursor.fetchone()
        if result:
            logging.info(f"Retrieved article: {result[0]}")
            docs.append(f"{result[0]}: {result[1]}")
        else:
            logging.warning(f"No article found for ID: {news_id}")

    conn.close()
    logging.info("Closed SQLite connection.")

    context = "\n\n".join(docs)
    prompt = f"""
You are a financial advisor AI. Based on the following news, answer the question: "{user_query}"
Use the articles below to justify your answer.

Articles:
{context}
"""

    logging.info("Preparing request to Groq API...")
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {
                "role": "system",
                "content": "You are an expert financial advisor AI. "
                           "Provide concise, accurate, and well-reasoned financial advice based on the provided news articles only. "
                           "Do not make assumptions or provide personal opinions. Cite the articles used in your response."
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1024
    }

    logging.info("Sending request to Groq API...")
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        logging.error(f"Groq API returned error: {response.status_code} - {response.text}")
        tracker.stop()  # ✅ Stop emissions tracking on error
        return "Error from Groq API"

    logging.info("Response received from Groq API.")
    result_text = response.json()['choices'][0]['message']['content'].strip()
    logging.debug(f"Generated response: {result_text}")

    # ✅ Stop and report emissions
    emissions = tracker.stop()
    logging.info(f"Total CO₂ emissions: {emissions:.6f} kg")

    return result_text

if __name__ == "__main__":
    test_query = "How will interest rate hikes affect the stock market?"
    print(query_bot(test_query))
