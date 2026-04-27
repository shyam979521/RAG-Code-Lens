import faiss
import os
import numpy as np
from app.services.embedding_service import EmbeddingService
from config import Config

index_path = os.path.join(Config.BASE_DIR, 'faiss_index.bin')

if os.path.exists(index_path):
    index = faiss.read_index(index_path)
    print(f"Current Index Dimension: {index.d}")
    print(f"Total Vectors in Index: {index.ntotal}")
else:
    print("No Index file found at faiss_index.bin")

print("\n--- Testing Model Dimensions ---")
emb_service = EmbeddingService()
test_text = "This is a test to check dimensions."

models_to_test = [
    "models/gemini-embedding-001",
    "models/text-embedding-004",
    "models/embedding-001"
]

for m in models_to_test:
    try:
        import google.generativeai as genai
        genai.configure(api_key=Config.GEMINI_API_KEY)
        res = genai.embed_content(model=m, content=test_text, task_type="retrieval_document")
        vec = res['embedding']
        print(f"Model {m}: SUCCESS | Dimension: {len(vec)}")
    except Exception as e:
        print(f"Model {m}: FAILED | {e}")
