import sqlite3
import os

db_path = 'app.db'
index_path = 'faiss_index.bin'

print(f"--- Database Check ({db_path}) ---")
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM file")
    f_count = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM chunk")
    c_count = cursor.fetchone()[0]
    print(f"Files: {f_count}")
    print(f"Chunks: {c_count}")
    conn.close()
else:
    print("Database file MISSING")

print(f"\n--- Index Check ({index_path}) ---")
if os.path.exists(index_path):
    print("Index file EXISTS")
    import faiss
    idx = faiss.read_index(index_path)
    print(f"Index Dimensions: {idx.d}")
    print(f"Total Vectors: {idx.ntotal}")
else:
    print("Index file MISSING")
