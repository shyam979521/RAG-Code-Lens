import faiss, numpy as np, os

class VectorService:
    def __init__(self):
        self.path = 'faiss_index.bin'
        self.index = faiss.read_index(self.path) if os.path.exists(self.path) else None
    def add_vectors(self, vectors, ids):
        v, i = np.array(vectors).astype('float32'), np.array(ids).astype('int64')
        if not self.index: self.index = faiss.IndexIDMap(faiss.IndexFlatL2(v.shape[1]))
        self.index.add_with_ids(v, i)
        faiss.write_index(self.index, self.path)
def search(self, vec, k=30):
    if not self.index: return [], []
    return self.index.search(np.array([vec]).astype('float32'), k)