import google.generativeai as genai

from config import Config
class LLMService:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
def generate_text(self, p):
    return self.model.generate_content(p).text
