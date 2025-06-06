from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import sqlite3
import pickle

print("[START] Building vector store...")

try:
    # Load model
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("[INFO] SentenceTransformer model loaded.")

    # Connect to SQLite
    conn = sqlite3.connect("financial_news.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, summary FROM news WHERE summary IS NOT NULL")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("[WARN] No summarized articles found in the database.")
        exit()

    print(f"[INFO] Fetched {len(rows)} rows from DB.")

    # Prepare data for indexing
    texts = [f"{row[1]}: {row[2]}" for row in rows]
    ids = [row[0] for row in rows]
    embeddings = model.encode(texts)
    print("[INFO] Generated embeddings.")

    # Build and save FAISS index
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings))
    faiss.write_index(index, "faiss_index.index")
    print("[INFO] FAISS index saved to 'faiss_index.index'.")

    with open("id_mapping.pkl", "wb") as f:
        pickle.dump(ids, f)
    print("[INFO] ID mapping saved to 'id_mapping.pkl'.")

    print("[SUCCESS] Vector store built and saved successfully.")

except Exception as e:
    print(f"[ERROR] Failed to build vector store: {e}")
