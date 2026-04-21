import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-secret'
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'workspace')
    # User should set this env var or replace directly
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or 'AIzaSyDx-AZRA3gmmyWgNBq0Khr7NmOo_YSIlt0'
