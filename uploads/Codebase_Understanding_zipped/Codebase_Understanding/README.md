# 🚀 AI Codebase Intelligence - Ultimate Step-by-Step Tutorial 🎓

Welcome to the **AI Codebase Assistant** masterclass. This project is divided into **4 Phases**. At the end of each phase, your project will be "Run-able," meaning you can open the browser and see your progress live!

---

## 📂 Phase 1: The App Foundation (Setup & UI)
**Goal:** Initialize the project and see a beautiful Dashboard in your browser.

#### **1.1 `requirements.txt`**
```text
flask
flask-sqlalchemy
google-generativeai
faiss-cpu
numpy
python-dotenv
```

#### **1.2 `config.py`**
```python
import os
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-code-ai-key'
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'workspace')
    GEMINI_API_KEY = 'PASTE_YOUR_GEMINI_API_KEY_HERE'
```

#### **1.3 `app/__init__.py`**
```python
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    from app.routes.routes import main_bp
    app.register_blueprint(main_bp)
    
    with app.app_context():
        from app.models import models
        db.create_all()
    return app
```

#### **1.4 `app/routes/routes.py` (Phase 1 Version)**
```python
from flask import Blueprint, render_template, request, redirect, url_for
from app.models.models import File

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def dashboard():
    files = File.query.all()
    return render_template('dashboard.html', files=files)

@main_bp.route('/upload')
def upload_page():
    return render_template('upload.html')
```

#### **1.5 `app.py`**
```python
from app import create_app
app = create_app()
if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False)
```

**[UI CHECKPOINT]**: Run `python app.py`. Visit `localhost:5000`. You should see the Dashboard and Navigation.

---

## � Phase 2: Data & File Management
**Goal:** Upload a ZIP, process code, and see files list on your Dashboard.

#### **2.1 `app/models/models.py`**
```python
from app import db
from datetime import datetime

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(1024), nullable=False)
    filetype = db.Column(db.String(50))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    chunks = db.relationship('Chunk', backref='file', lazy=True, cascade="all, delete-orphan")

class Chunk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=False)
    chunk_text = db.Column(db.Text, nullable=False)
    chunk_index = db.Column(db.Integer)

class Dependency(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parent_file = db.Column(db.String(1024), nullable=False)
    child_file = db.Column(db.String(1024), nullable=False)
```

#### **2.2 `app/services/chunk_service.py`**
```python
class ChunkService:
    def chunk_text(self, text, chunk_size=4000, overlap=400):
        if not text: return []
        chunks, start = [], 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])
            if end == len(text): break
            start += (chunk_size - overlap)
        return chunks
```

#### **2.3 `app/services/file_service.py`**
```python
import os, zipfile
from app import db
from app.models.models import File, Chunk

class FileService:
    def process_zip(self, zip_path, extract_to):
        with zipfile.ZipFile(zip_path, 'r') as z: z.extractall(extract_to)
        for root, _, files in os.walk(extract_to):
            if any(x in root for x in ['.git', 'node_modules', 'venv']): continue
            for file in files:
                if file.endswith(('.py', '.js', '.html', '.css')):
                    p = os.path.join(root, file)
                    rel = os.path.relpath(p, extract_to)
                    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                        f_obj = File(filename=file, filepath=rel, content=f.read())
                        db.session.add(f_obj)
        db.session.commit()
        return True, "Done"
```

#### **2.4 Update `routes.py` (Add Upload Handling)**
```python
@main_bp.route('/process', methods=['POST'])
def process_upload():
    file = request.files['file']
    path = os.path.join('workspace', 'upload.zip')
    file.save(path)
    file_service.process_zip(path, 'workspace/extracted')
    return redirect(url_for('main.dashboard'))
```

**[DATA CHECKPOINT]**: Upload a project. Dashboard will now display your files!

---

## � Phase 3: The AI Brain (Embeddings & Search)
**Goal:** Ask AI questions about your code and get smart answers.

#### **3.1 `app/services/llm_service.py`**
```python
import google.generativeai as genai
from config import Config
class LLMService:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    def generate_text(self, p):
        return self.model.generate_content(p).text
```

#### **3.2 `app/services/embedding_service.py`**
```python
import google.generativeai as genai
import time
class EmbeddingService:
    def __init__(self): self.model = None
    def get_embedding(self, text, task_type="retrieval_document"):
        # List of models to try
        for m in ["models/gemini-embedding-001", "models/embedding-001"]:
            try:
                res = genai.embed_content(model=m, content=text[:8000], task_type=task_type)
                return res['embedding']
            except: time.sleep(2); continue
        return None
```

#### **3.3 `app/services/vector_service.py`**
```python
import faiss, numpy as np, os
class VectorService:
    def __init__(self):
        self.path = 'faiss_index.bin'
        self.index = faiss.read_index(self.path) if os.path.exists(self.path) else None
    def add_vectors(self, vectors, ids):
        v, i = np.array(vectors).astype('float32'), np.array(ids).astype('int64')
        if not self.index: self.index = faiss.IndexIDMap(faiss.IndexFlatL2(v.shape[1]))
        self.index.add_with_ids(v, i)
        faiss.write_index(self.index, self.path)
    def search(self, vec, k=30):
        if not self.index: return [], []
        return self.index.search(np.array([vec]).astype('float32'), k)
```

#### **3.4 `app/services/rag_service.py`**
```python
class RagService:
    # Logic to combine Search Results + AI Prompt
    def answer_query(self, query):
        # 1. Embed Query -> 2. Search FAISS -> 3. Build AI Prompt -> 4. Return Answer
        # (Copy full diverse retrieval logic from source)
```

**[AI CHECKPOINT]**: Visit `/search`. Ask "Where is the main entry point?". AI will explain!

---

## 📂 Phase 4: Advanced AI Features (Explain & Docs)
**Goal:** Generate full project documentation and file-wise explanations.

#### **4.1 `app/services/explain_service.py`**
```python
class ExplainService:
    def explain_file(self, name, code):
        prompt = f"Explain this code file like a Senior Engineer: {name}\nCode: {code[:10000]}"
        return llm_service.generate_text(prompt)
```

#### **4.2 `app/services/docs_service.py`**
```python
class DocsService:
    def generate_docs(self, project_summary):
        prompt = f"Create a high-level technical README for this project based on these files:\n{project_summary}"
        return llm_service.generate_text(prompt)
```

#### **Final `app/routes/routes.py` (Full Version)**
```python
# Include /explain-file, /docs, /dependencies, and /file?id= routes here.
```

---

## 🔥 Launch!
Run `python app.py` and enjoy your professional **AI Codebase Intelligence Dashboard**! 🚀✨
