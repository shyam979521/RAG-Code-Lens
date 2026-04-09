import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-code-ai-key'
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'workspace')
    GEMINI_API_KEY = 'PASTE_YOUR_GEMINI_API_KEY_HERE'