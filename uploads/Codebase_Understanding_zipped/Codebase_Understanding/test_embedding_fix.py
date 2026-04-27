from app.services.embedding_service import EmbeddingService
import sys

try:
    service = EmbeddingService()
    vector = service.get_embedding("Test query")
    if vector:
        print(f"Vector dimension: {len(vector)}")
    else:
        print("Failed to get vector")
except Exception as e:
    print(f"Error: {e}")
