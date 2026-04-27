import sqlite3
import os

db_path = 'app.db'

print(f"--- Searching Database for 'login' keyword ---")
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Search in File contents first
    print("\n[Files containing 'login']:")
    cursor.execute("SELECT filepath FROM file WHERE content LIKE '%login%'")
    files = cursor.fetchall()
    for f in files:
        print(f"- {f[0]}")
        
    # Search in Chunks
    print("\n[Chunks containing 'login']:")
    cursor.execute("""
        SELECT f.filepath, c.chunk_index, substr(c.chunk_text, 1, 100) 
        FROM chunk c 
        JOIN file f ON c.file_id = f.id 
        WHERE c.chunk_text LIKE '%login%'
    """)
    chunks = cursor.fetchall()
    for c in chunks:
        print(f"- File: {c[0]} | Chunk: {c[1]} | Snippet: {c[2]}...")
        
    conn.close()
else:
    print("Database file MISSING")
