from config import Config
from groq import Groq

print("Testing Groq API...")

try:
    client = Groq(api_key=Config.GROQ_API_KEY)
    response = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[{"role": "user", "content": "Say 'Hello, I am working!'"}]
    )
    print("✅ SUCCESS! Response:", response.choices[0].message.content)
except Exception as e:
    print("❌ Error:", e)