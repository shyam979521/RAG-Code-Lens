from groq import Groq
from app.config import Config

class LLMService:
    def __init__(self):
        try:
            self.client = Groq(api_key=Config.GROQ_API_KEY)
            # Use a simpler, more reliable model
            self.model = Config.LLM_MODEL
            print("✅ LLM Service initialized with Groq")
            print(f"   Using model: {self.model}")
        except Exception as e:
            print(f"❌ Error initializing Groq: {e}")
            self.client = None
    
    def generate_text(self, prompt):
        """Generate text response using Groq's Llama model"""
        if not self.client:
            return "Error: AI service not available. Please check your Groq API key."
        
        if not prompt or len(prompt.strip()) == 0:
            return "Please provide a valid prompt."
        
        try:
            # Add system instruction to prevent documentation output
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful code assistant. Answer questions directly and concisely. Do NOT output documentation, API references, or restructured text. Just give plain English answers."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,  # Lower temperature for more focused answers
                max_tokens=1024
            )
            
            return response.choices[0].message.content
                
        except Exception as e:
            print(f"❌ Error generating text: {e}")
            return f"Error: {str(e)}"
    
    def generate_chat_response(self, prompt, context=""):
        """Generate response with context"""
        full_prompt = f"""Question: {prompt}

Context: {context[:2000] if context else 'No additional context'}

Answer the question directly and clearly. Do not output documentation or technical specifications. Just provide a helpful answer."""
        
        return self.generate_text(full_prompt)
    
    def test_connection(self):
        """Test if the API is working"""
        try:
            test_response = self.generate_text("Say 'OK'")
            if test_response and "OK" in test_response:
                print("✅ Groq API connection test passed!")
                return True
            else:
                print("⚠️ Groq API test returned unexpected response")
                return True
        except Exception as e:
            print(f"❌ API test error: {e}")
            return False
