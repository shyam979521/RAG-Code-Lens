import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-code-ai-key'
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    
    # IMPORTANT: Replace with your actual Gemini API Key
    # Get it from: https://aistudio.google.com/app/apikey
    GROQ_API_KEY = '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'