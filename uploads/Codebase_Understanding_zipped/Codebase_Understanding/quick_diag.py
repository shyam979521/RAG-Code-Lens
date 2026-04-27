import sqlite3
import os

def run_diag():
    db_path = 'app.db'
    output_file = 'diag_output.txt'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("--- RAG DIAGNOSTIC ---\n")
        if not os.path.exists(db_path):
            f.write("DB file not found!\n")
            return
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Count files
        cursor.execute("SELECT count(*) FROM file")
        f.write(f"Total files: {cursor.fetchone()[0]}\n")
        
        # List files
        f.write("\nFiles List:\n")
        cursor.execute("SELECT filepath FROM file")
        for row in cursor.fetchall():
            f.write(f"- {row[0]}\n")
            
        # Search for 'login' in content
        f.write("\nFiles containing 'login':\n")
        cursor.execute("SELECT filepath FROM file WHERE content LIKE '%login%'")
        for row in cursor.fetchall():
            f.write(f"- {row[0]}\n")
            
        # Count chunks
        cursor.execute("SELECT count(*) FROM chunk")
        f.write(f"\nTotal chunks: {cursor.fetchone()[0]}\n")
        
        # Check index
        if os.path.exists('faiss_index.bin'):
            f.write("\nFAISS Index: EXISTS\n")
            import faiss
            idx = faiss.read_index('faiss_index.bin')
            f.write(f"Index Dimension: {idx.d}\n")
            f.write(f"Total Vectors: {idx.ntotal}\n")
        else:
            f.write("\nFAISS Index: MISSING\n")
            
        conn.close()

if __name__ == '__main__':
    run_diag()
    print("Diagnostic complete.")
