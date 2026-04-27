import google.generativeai as genai
from config import Config

genai.configure(api_key=Config.GEMINI_API_KEY)

try:
    print("Listing available models...")
    for m in genai.list_models():
        if 'embedContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error: {e}")
