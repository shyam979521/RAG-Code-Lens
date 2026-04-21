import os
import zipfile
from app import db
from app.models.models import File, Chunk
from app.services.chunk_service import ChunkService
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService

class FileService:
    def __init__(self):
        self.chunk_service = ChunkService()
        self.embedding_service = EmbeddingService()
        self.vector_service = VectorService()

    def process_zip(self, zip_path, extract_to):
        """
        Extracts ZIP, reads supported files, saves to DB, chunks, and embeds.
        """
        if not os.path.exists(extract_to):
            os.makedirs(extract_to)
            
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
        except zipfile.BadZipFile:
            return False, "Invalid ZIP file"

        supported_exts = ['.py', '.js', '.html', '.css', '.ts', '.java', '.md', '.txt']
        files_processed = 0
        
        # We will collect all file objects first
        files_to_embed = []
        
        # Directories to skip
        skip_dirs = {'.git', 'node_modules', 'venv', 'env', '__pycache__', '.idea', '.vscode', 'dist', 'build', 'coverage'}
        
        print(f"Starting file scan in: {extract_to}")
        
        for root, dirs, files in os.walk(extract_to):
            # Modify dirs in-place to skip traversals
            dirs[:] = [d for d in dirs if d not in skip_dirs]
                
            for file in files:
                # Optional: Skip minified files
                if file.endswith('.min.js') or file.endswith('.min.css'):
                    continue
                    
                ext = os.path.splitext(file)[1].lower()
                if ext in supported_exts:
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, extract_to)
                    
                    try:
                        # Skip large files (> 1MB) to prevent lockups
                        if os.path.getsize(filepath) > 1 * 1024 * 1024:
                            print(f"Skipping large file: {rel_path}")
                            continue

                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        # Check if file already exists
                        existing = File.query.filter_by(filepath=rel_path).first()
                        if not existing:
                            file_obj = File(
                                filename=file,
                                filepath=rel_path,
                                filetype=ext,
                                content=content
                            )
                            db.session.add(file_obj)
                            files_to_embed.append(file_obj)
                            files_processed += 1
                            
                    except Exception as e:
                        print(f"Error reading {filepath}: {e}")
        
        print(f"Files found: {len(files_to_embed)}")
        db.session.commit()
        
        # Process embeddings for new files
        if files_to_embed:
            self.process_embeddings(files_to_embed)
            
        return True, f"Processed {files_processed} files."

    def process_embeddings(self, files):
        import sys
        
        total_files = len(files)
        print(f"--- Starting Bulk Embedding for {total_files} files...")
        sys.stdout.flush()
        
        for idx, file in enumerate(files):
            try:
                print(f"    [{idx+1}/{total_files}] Processing: {file.filename}")
                sys.stdout.flush()
                
                chunks_text = self.chunk_service.chunk_text(file.content)
                if not chunks_text:
                    continue
                
                # Create chunk objects in DB first
                chunk_objs = []
                for i, text in enumerate(chunks_text):
                    chunk = Chunk(file_id=file.id, chunk_text=text, chunk_index=i)
                    db.session.add(chunk)
                    chunk_objs.append(chunk)
                
                db.session.flush() # Sync so chunk IDs are available
                
                # Get embeddings in ONE batch for the whole file
                # Note: Gemini batch limit is usually 100 per request. 
                # Our files are usually < 100 chunks.
                embeddings = self.embedding_service.get_embeddings_batch(chunks_text)
                
                if embeddings and len(embeddings) == len(chunk_objs):
                    ids = [c.id for c in chunk_objs]
                    self.vector_service.add_vectors(embeddings, ids)
                    print(f"      ✓ Successfully embedded {len(embeddings)} chunks.")
                else:
                    print(f"      ! Batch embedding failed/mismatched for {file.filename}. Falling back to single mode.")
                    # Single mode backup logic
                    vectors, ids = [], []
                    for c in chunk_objs:
                        emb = self.embedding_service.get_embedding(c.chunk_text)
                        if emb:
                            vectors.append(emb)
                            ids.append(c.id)
                    if vectors:
                        self.vector_service.add_vectors(vectors, ids)

                db.session.commit()
                
            except Exception as e:
                print(f"    ! Error in {file.filename}: {e}")
                db.session.rollback()
                continue
        
        print("--- Bulk Processing Complete.")
        sys.stdout.flush()
            
    def get_file_content(self, file_id):
        file = File.query.get(file_id)
        return file.content if file else None
        
    def get_all_files(self):
        return File.query.all()
