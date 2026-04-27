import google.generativeai as genai
import os
from config import Config

def find_embedding_model():
    genai.configure(api_key=Config.GEMINI_API_KEY)
    print("--- Searching for available embedding models ---")
    try:
        models = genai.list_models()
        for m in models:
            if 'embedContent' in m.supported_generation_methods:
                print(f"FOUND: {m.name}")
                return m.name
    except Exception as e:
        print(f"Error listing models: {e}")
    return None

if __name__ == "__main__":
    m = find_embedding_model()
    if m:
        print(f"\nFinal Choice: {m}")
    else:
        print("\nNo embedding model found!")
