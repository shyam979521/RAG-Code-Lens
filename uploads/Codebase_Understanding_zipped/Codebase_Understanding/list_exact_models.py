import google.generativeai as genai
import os
from config import Config

genai.configure(api_key=Config.GEMINI_API_KEY)

print("--- AVAILABLE EMBEDDING MODELS ---")
try:
    for m in genai.list_models():
        if 'embedContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error: {e}")
