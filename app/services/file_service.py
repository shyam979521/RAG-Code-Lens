import os
import zipfile
from app import db
from app.models.models import File

class FileService:
    def process_zip(self, zip_path, extract_to):
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(extract_to)
        
        for root, _, files in os.walk(extract_to):
            if any(x in root for x in ['.git', 'node_modules', 'venv']):
                continue
            for file in files:
                if file.endswith(('.py', '.js', '.html', '.css')):
                    p = os.path.join(root, file)
                    rel = os.path.relpath(p, extract_to)
                    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                        f_obj = File(filename=file, filepath=rel, content=f.read())
                        db.session.add(f_obj)
        
        db.session.commit()
        return True, "Done"