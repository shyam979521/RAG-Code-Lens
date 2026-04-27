import google.generativeai as genai
import os
from config import Config

# Force load the key directly to be sure
key = Config.GEMINI_API_KEY
print(f"Testing with Key: {key[:10]}...")

genai.configure(api_key=key)

try:
    print("Attempting to embed 'test query'...")
    result = genai.embed_content(
        model="models/embedding-001",
        content="test query",
        task_type="retrieval_query"
    )
    print("Success! Vector length:", len(result['embedding']))
except Exception as e:
    print("\nFAILED:")
    print(e)
