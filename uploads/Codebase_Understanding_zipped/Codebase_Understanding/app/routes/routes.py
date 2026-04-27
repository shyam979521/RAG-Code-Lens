from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app
from app.services.file_service import FileService
from app.services.rag_service import RagService
from app.services.explain_service import ExplainService
from app.services.docs_service import DocsService
from app.services.dependency_service import DependencyService
from app.models.models import File
import os

main_bp = Blueprint('main', __name__)

# Initialize services (lazy init might be better but this is fine for Flask)
# Note: In production, we might use dependency injection or current_app context
file_service = FileService()
rag_service = RagService()
explain_service = ExplainService()
docs_service = DocsService()
dep_service = DependencyService()

@main_bp.route('/')
def dashboard():
    files = file_service.get_all_files()
    return render_template('dashboard.html', files=files)

@main_bp.route('/upload', methods=['GET'])
def upload_page():
    return render_template('upload.html')

@main_bp.route('/process', methods=['POST'])
def process_upload():
    import sys
    import traceback
    
    print("\n" + "="*50)
    print(">>> UPLOAD REQUEST RECEIVED")
    sys.stdout.flush()
    
    try:
        if 'file' not in request.files:
            print("!!! No file part in request")
            return "No file part", 400
            
        file = request.files['file']
        if file.filename == '':
            print("!!! No selected file")
            return "No selected file", 400
            
        if file:
            # File size sanity check (50MB) 
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)
            print(f"--- File name: {file.filename}, Size: {size / (1024*1024):.2f} MB")
            sys.stdout.flush()

            if size > 50 * 1024 * 1024:
                return "Error: ZIP file too large (>50MB).", 400

            upload_dir = current_app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
                print(f"Created upload dir: {upload_dir}")

            filepath = os.path.join(upload_dir, 'upload.zip')
            
            print(f"--- Saving file to disc...")
            file.save(filepath)
            print(f"--- File saved successfully.")
            sys.stdout.flush()

            extract_to = os.path.join(upload_dir, 'extracted')
            if os.path.exists(extract_to):
                import shutil
                print(f"--- Cleaning old extraction folder: {extract_to}")
                shutil.rmtree(extract_to)
            
            print(f"--- Starting extraction (zipfile module)...")
            sys.stdout.flush()
            success, msg = file_service.process_zip(filepath, extract_to)
            
            if success:
                print(f"--- Extraction completed: {msg}")
                print(f"--- Building dependency graph...")
                sys.stdout.flush()
                try:
                    dep_service.build_dependency_graph()
                    print(f"--- Dependency graph built.")
                except Exception as de:
                    print(f"!!! Dependency Error (Non-Fatal): {de}")
                
                print(">>> SUCCESS: Redirecting to Dashboard")
                print("="*50 + "\n")
                sys.stdout.flush()
                return redirect(url_for('main.dashboard'))
            else:
                print(f"!!! Process ZIP failed: {msg}")
                return f"Error: {msg}", 500
                
    except Exception as e:
        print("\n" + "!"*50)
        print(f"!!! CRITICAL SERVER CRASH DETECTED")
        print(f"!!! Error type: {type(e).__name__}")
        print(f"!!! Error message: {str(e)}")
        traceback.print_exc()
        print("!"*50 + "\n")
        sys.stdout.flush()
        return f"CRITICAL ERROR: {str(e)}", 500

@main_bp.route('/search')
def search_page():
    return render_template('search.html')

@main_bp.route('/api/query', methods=['POST'])
def api_query():
    data = request.json
    query = data.get('query')
    if not query:
        return jsonify({"answer": "Please provide a query.", "citations": []})
    result = rag_service.answer_query(query)
    return jsonify(result)

@main_bp.route('/file')
def view_file():
    file_id = request.args.get('id')
    file = File.query.get(file_id)
    if not file:
        return "File not found", 404
    return render_template('file_view.html', file=file)

@main_bp.route('/explain-file')
def explain_file_route():
    file_id = request.args.get('id')
    file = File.query.get(file_id)
    if not file:
        return "File not found", 404
        
    explanation = explain_service.explain_file(file.filename, file.content)
    # Convert markdown to html if needed, or just let template handle it (if using a markdown lib or just raw)
    # We'll pass raw and let frontend handle or just display as pre-wrap
    return render_template('explanation.html', file=file, explanation=explanation)

@main_bp.route('/docs')
def docs_page():
    return render_template('docs.html')

@main_bp.route('/generate-docs-action', methods=['POST'])
def generate_docs_action():
    files = file_service.get_all_files()
    # Create a summary context - naive approach
    context = ""
    for f in files:
        # Include filename and first 200 chars to give an overview without blowing up context
        context += f"File: {f.filename}\nFirst 200 chars: {f.content[:200]}\n...\n\n"
        
    docs = docs_service.generate_docs(context)
    return jsonify({"docs": docs})

@main_bp.route('/dependencies')
def dependencies_page():
    deps = dep_service.get_dependencies()
    return render_template('dependencies.html', deps=deps)
