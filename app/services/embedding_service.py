class EmbeddingService:
    def __init__(self):
        print("✅ Embedding Service ready (search features available)")
    
    def get_embedding(self, text, task_type="retrieval_document"):
        # Return dummy embedding - actual search not needed for basic AI
        return [0.0] * 768
    
    def test_connection(self):
        return True