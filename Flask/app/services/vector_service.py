import faiss
import numpy as np
import os
from config import Config

class VectorService:
    def __init__(self):
        self.index_path = os.path.join(Config.BASE_DIR, 'faiss_index.bin')
        
        if os.path.exists(self.index_path):
            try:
                self.index = faiss.read_index(self.index_path)
                print(f"--- Loaded FAISS index from {self.index_path}, Dimension: {self.index.d}")
            except Exception as e:
                print(f"--- Error loading index: {e}, creating new one.")
                self.index = None
        else:
            self.index = None
            
    def add_vectors(self, vectors, ids):
        if not vectors:
            return
        
        np_vectors = np.array(vectors).astype('float32')
        np_ids = np.array(ids).astype('int64')
        
        # Initialize index if it doesn't exist
        if self.index is None:
            dimension = np_vectors.shape[1]
            print(f"--- Initializing NEW FAISS index with Dimension: {dimension}")
            self.index = faiss.IndexIDMap(faiss.IndexFlatL2(dimension))
        
        self.index.add_with_ids(np_vectors, np_ids)
        self.save_index()
        
    def search(self, query_vector, k=5):
        if query_vector is None or self.index is None:
            if self.index is None:
                print("--- Search failed: Index is not initialized yet (Upload files first).")
            return [], []
            
        np_vector = np.array([query_vector]).astype('float32')
        
        # Dimension Check
        query_dim = np_vector.shape[1]
        if query_dim != self.index.d:
            print(f"!!! DIMENSION MISMATCH: Index expects {self.index.d}, but query is {query_dim}")
            print("!!! Solution: Reset your database and re-upload your project.")
            return [], []
            
        distances, indices = self.index.search(np_vector, k)
        return indices[0], distances[0]
        
    def save_index(self):
        if self.index:
            faiss.write_index(self.index, self.index_path)
        
    def reset_index(self):
        self.index = None
        if os.path.exists(self.index_path):
            os.remove(self.index_path)
            print(f"--- FAISS index file {self.index_path} deleted.")
