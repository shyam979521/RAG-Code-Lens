"""Central application settings.

Environment variables take precedence so deployments can override local defaults
without modifying source code.
"""

import os
from datetime import timedelta


class Config:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-code-ai-key"
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "app.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER") or os.path.join(BASE_DIR, "uploads")
    MAX_UPLOAD_SIZE = 500 * 1024 * 1024
    MAX_CONTENT_LENGTH = MAX_UPLOAD_SIZE
    SEND_FILE_MAX_AGE_DEFAULT = 0
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    SUPPORTED_EXTENSIONS = {"zip"}
    INDEXED_FILE_EXTENSIONS = {".py", ".js", ".html", ".css", ".txt", ".md", ".json"}
    IGNORED_DIRECTORIES = {"__pycache__", ".git", "node_modules", "venv", ".venv"}
    IGNORED_FILE_SUFFIXES = (".pyc", ".pyo")

    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    EMBEDDING_DIMENSION = 768
    VECTOR_INDEX_PATH = os.environ.get("VECTOR_INDEX_PATH", "faiss_index.bin")
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or "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"
    LLM_MODEL = os.environ.get("LLM_MODEL", "llama-3.1-8b-instant")
