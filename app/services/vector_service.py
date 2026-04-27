import faiss
import numpy as np
import os

class VectorService:
    def __init__(self):
        self.path = 'faiss_index.bin'
        self.dimension = 768
        self.index = None
        
        # Load existing index if available
        if os.path.exists(self.path):
            try:
                self.index = faiss.read_index(self.path)
                print(f"✅ Loaded existing index with {self.index.ntotal} vectors")
            except Exception as e:
                print(f"⚠️ Could not load index: {e}")
                self.index = None
        else:
            print("📁 No existing index found, will create new one when adding vectors")
    
    def _create_index(self, dimension):
        """Create a new FAISS index"""
        try:
            flat_index = faiss.IndexFlatL2(dimension)
            self.index = faiss.IndexIDMap(flat_index)
            print(f"✅ Created new index with dimension {dimension}")
            return True
        except Exception as e:
            print(f"❌ Error creating index: {e}")
            return False
    
    def add_vectors(self, vectors, ids):
        """Add vectors to the index"""
        if not vectors:
            print("⚠️ No vectors to add")
            return 0
        
        try:
            vectors_np = np.array(vectors).astype('float32')
            ids_np = np.array(ids).astype('int64')
            
            # Create index if it doesn't exist
            if self.index is None:
                if not self._create_index(vectors_np.shape[1]):
                    return 0
            
            # Add vectors
            self.index.add_with_ids(vectors_np, ids_np)
            
            # Save index
            faiss.write_index(self.index, self.path)
            print(f"✅ Added {len(vectors)} vectors to index (total: {self.index.ntotal})")
            
            return len(vectors)
        except Exception as e:
            print(f"❌ Error adding vectors: {e}")
            return 0
    
    def search(self, query_vector, k=10):
        """Search for similar vectors"""
        if self.index is None or self.index.ntotal == 0:
            print("⚠️ Index is empty or not initialized")
            return [], []
        
        try:
            query_np = np.array([query_vector]).astype('float32')
            distances, indices = self.index.search(query_np, min(k, self.index.ntotal))
            valid_results = [(distances[0][i], indices[0][i]) for i in range(len(indices[0])) if indices[0][i] >= 0]
            
            if valid_results:
                print(f"✅ Search found {len(valid_results)} relevant results")
                return [d for d, i in valid_results], [i for d, i in valid_results]
            else:
                print("⚠️ Search found no results")
                return [], []
        except Exception as e:
            print(f"❌ Error searching: {e}")
            return [], []
    
    def get_total_vectors(self):
        """Get total number of vectors in index"""
        return self.index.ntotal if self.index else 0
    
    def clear_index(self):
        """Clear the index"""
        self.index = None
        if os.path.exists(self.path):
            os.remove(self.path)
            print("✅ Index cleared")
            