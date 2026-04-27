import google.generativeai as genai
import os
from dotenv import load_dotenv

# Try to load from .env if it exists
load_dotenv()

# Use the hardcoded key from config if env is empty
api_key = os.environ.get('GEMINI_API_KEY') or 'AIzaSyBODSa1R8T7s_1dPyL9gxeiI7lAGDT2Nb0'

print(f"Testing API Key: {api_key[:10]}...")

genai.configure(api_key=api_key)

print("\n--- Listing Models ---")
try:
    for m in genai.list_models():
        if 'embedContent' in m.supported_generation_methods:
            print(f"- {m.name} (Methods: {m.supported_embedding_generate_methods if hasattr(m, 'supported_embedding_generate_methods') else 'embedContent'})")
except Exception as e:
    print(f"FAILED TO LIST MODELS: {e}")

print("\n--- Testing Single Embedding (text-embedding-004) ---")
try:
    res = genai.embed_content(model="models/text-embedding-004", content="Hello world", task_type="retrieval_document")
    print(f"SUCCESS! Dimension: {len(res['embedding'])}")
except Exception as e:
    print(f"text-embedding-004 FAILED: {e}")

print("\n--- Testing Single Embedding (embedding-001) ---")
try:
    res = genai.embed_content(model="models/embedding-001", content="Hello world", task_type="retrieval_document")
    print(f"SUCCESS! Dimension: {len(res['embedding'])}")
except Exception as e:
    print(f"embedding-001 FAILED: {e}")
