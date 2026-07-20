from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import os
import zipfile
import shutil
import time
from werkzeug.utils import secure_filename

# Import Config first
from app.config import Config

# Then import AI Services
from app.services.rag_service import RagService
from app.services.explain_service import ExplainService
from app.services.docs_service import DocsService
from app.services.dependency_service import DependencyService

# Database
from app import db
from app.models.models import File, Dependency, User
from app.services.project_service import ProjectService
from app.services.auth_service import AuthService
from app.utils.auth import login_required
from app.utils.filesystem import (
    allowed_file,
    force_delete_file,
    force_delete_folder,
    remove_empty_folders as _remove_empty_folders,
    should_skip_directory,
    should_skip_file,
)

app = Flask(__name__)

# Configuration
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_UPLOAD_SIZE
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = Config.SEND_FILE_MAX_AGE_DEFAULT

# Session secret key for login/logout
app.secret_key = Config.SECRET_KEY

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize AI Services
try:
    rag_service = RagService()
    explain_service = ExplainService()
    docs_service = DocsService()
    dependency_service = DependencyService()
    AI_AVAILABLE = True
    print(" AI Services initialized successfully")
except Exception as e:
    print(f" AI Services initialization failed: {e}")
    AI_AVAILABLE = False

# Initialize Database
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.create_all()

# Allowed extensions
project_service = ProjectService(app.config['UPLOAD_FOLDER'])

# ========== HELPER FUNCTIONS ==========
def remove_empty_folders(folder_path):
    """Backward-compatible wrapper for the shared cleanup helper."""
    return _remove_empty_folders(folder_path, app.config['UPLOAD_FOLDER'])

def index_file_chunks(file_id, file_path, content):
    """Index a file's content into vector database"""
    try:
        # Split content into chunks
        chunk_size = Config.CHUNK_SIZE
        overlap = Config.CHUNK_OVERLAP
        chunks = []
        
        for i in range(0, len(content), chunk_size - overlap):
            chunk = content[i:i + chunk_size]
            if chunk.strip():
                chunks.append(chunk)
        
        # Index each chunk
        indexed = rag_service.index_file_chunks(file_id, chunks)
        print(f"   Indexed {indexed} chunks from {file_path}")
        return indexed
    except Exception as e:
        print(f"   Error indexing {file_path}: {e}")
        return 0

# ========== PAGE ROUTES ==========
@app.route('/')
def home():
    """Landing page"""
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    msg = request.args.get('msg', '')
    error = request.args.get('error', '')
    return render_template('index.html', msg=msg, error=error)

@app.route('/register')
def register():
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    error = request.args.get('error', '')
    return render_template('register.html', error=error)

@app.route('/login')
def login():
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    error = request.args.get('error', '')
    msg = request.args.get('msg', '')
    return render_template('login.html', error=error, msg=msg)

@app.route('/upload')
@login_required
def upload_page():
    """Show the upload page"""
    return render_template('upload.html')

@app.route('/workspace/<project_name>')
@login_required
def workspace(project_name):
    """Read-only project workspace built from the existing uploaded files."""
    workspace_data = project_service.get_workspace(project_name, request.args.get('file'))
    if not workspace_data:
        return redirect(url_for('dashboard', error='Project not found'))
    return render_template('workspace.html', workspace=workspace_data)

@app.route('/dashboard')
@login_required
def dashboard():
    """Show all uploaded projects and their files"""
    remove_empty_folders(app.config['UPLOAD_FOLDER'])
    projects = project_service.list_projects(include_details=True)
    
    msg = request.args.get('msg', '')
    error = request.args.get('error', '')
    
    return render_template('dashboard.html', projects=projects, msg=msg, error=error)

# ========== LOGIN/LOGOUT/REGISTRATION ROUTES ==========
@app.route('/do-login', methods=['POST'])
def do_login():
    """Handle login form submission"""
    email = request.form.get('email', '')
    password = request.form.get('password', '')
    user, error = AuthService.authenticate(email, password)
    if user:
        session['user'] = user.email
        session['fullname'] = user.fullname
        session['logged_in'] = True
        session.permanent = request.form.get('remember_me') == 'on'
        return redirect(url_for('dashboard', msg='Login successful! Welcome back!'))
    return redirect(url_for('login', error=error))

@app.route('/do-register', methods=['POST'])
def do_register():
    """Handle registration form submission"""
    fullname = request.form.get('fullname', '')
    email = request.form.get('email', '')
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    user, error = AuthService.register(fullname, email, password, confirm_password)
    if user:
        session.clear()
        return redirect(url_for('login', msg='Registration successful! Please login to continue.'))
    return redirect(url_for('register', error=error))

@app.route('/logout')
def logout():
    """Log out the user"""
    session.clear()
    return redirect(url_for('home', msg='You have been logged out successfully!'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Password recovery placeholder until delivery infrastructure is configured."""
    msg = ''
    if request.method == 'POST':
        msg = 'If an account exists for that email, recovery instructions will be sent when email delivery is configured.'
    return render_template('forgot_password.html', msg=msg)

@app.route('/reset-password')
def reset_password():
    """Password reset placeholder; no token delivery exists in the current application."""
    return render_template('reset_password.html')

# ========== API UPLOAD ROUTE ==========
@app.route('/api/upload', methods=['POST'])
@login_required
def api_upload():
    """API endpoint for uploading MULTIPLE ZIP files and indexing them"""
    print("=" * 50)
    print("UPLOAD REQUEST RECEIVED")
    
    if 'files' not in request.files:
        return jsonify({'success': False, 'error': 'No files uploaded'}), 400
    
    files = request.files.getlist('files')
    print(f"Number of files received: {len(files)}")
    
    if len(files) == 0 or files[0].filename == '':
        return jsonify({'success': False, 'error': 'No files selected'}), 400
    
    uploaded_projects = []
    errors = []
    file_id_counter = 1
    
    for file in files:
        if file and file.filename.endswith('.zip'):
            print(f"\nProcessing: {file.filename}")
            
            filename = secure_filename(file.filename)
            project_name = filename.replace('.zip', '')
            
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            extract_folder = os.path.join(app.config['UPLOAD_FOLDER'], project_name)

            File.query.filter_by(project_name=project_name).delete()
            Dependency.query.filter_by(project_name=project_name).delete()
            db.session.commit()
            
            if os.path.exists(extract_folder):
                force_delete_folder(extract_folder)
            
            os.makedirs(extract_folder, exist_ok=True)
            
            try:
                with zipfile.ZipFile(filepath, 'r') as zip_ref:
                    zip_ref.extractall(extract_folder)
                print(f"  Extracted successfully")
                
                os.remove(filepath)
                
                # Index all files in the extracted folder
                indexed_count = 0
                for root, dirs, files_in_zip in os.walk(extract_folder):
                    dirs[:] = [d for d in dirs if not should_skip_directory(d)]
                    for f in files_in_zip:
                        if should_skip_file(f):
                            continue
                        if f.endswith(('.py', '.js', '.html', '.css', '.txt', '.md', '.json')):
                            file_path = os.path.join(root, f)
                            try:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as code_file:
                                    content = code_file.read()
                                
                                    # Save to DB for dependency analysis
                                    new_file = File(
                                        filename=f,
                                        filepath=file_path,
                                        filetype='.' + f.split('.')[-1] if '.' in f else '',
                                        content=content,
                                        project_name=project_name
                                    )
                                    db.session.add(new_file)
                                    
                                    if content.strip():
                                        indexed = index_file_chunks(file_id_counter, f, content)
                                        indexed_count += indexed
                                        file_id_counter += 1
                            except Exception as e:
                                print(f"    Error indexing {f}: {e}")
                
                db.session.commit()
                
                # Count total files
                file_count = 0
                for root, dirs, files_in_zip in os.walk(extract_folder):
                    dirs[:] = [d for d in dirs if not should_skip_directory(d)]
                    for f in files_in_zip:
                        if not should_skip_file(f):
                            file_count += 1
                
                uploaded_projects.append({
                    'name': project_name,
                    'file_count': file_count,
                    'indexed_chunks': indexed_count
                })
                print(f"  Added {file_count} files, {indexed_count} chunks indexed")
                
            except Exception as e:
                errors.append(f"Error extracting {filename}: {str(e)}")
                print(f"  Extraction error: {e}")
        else:
            errors.append(f"Invalid file type: {file.filename} (only ZIP files allowed)")
    
    print(f"\nUpload complete: {len(uploaded_projects)} projects uploaded")
    print("=" * 50)
    
    if len(uploaded_projects) > 0:
        return jsonify({
            'success': True,
            'message': f'Successfully uploaded {len(uploaded_projects)} project(s)!',
            'uploaded_projects': uploaded_projects,
            'errors': errors if errors else None
        })
    else:
        return jsonify({
            'success': False,
            'error': 'No valid ZIP files uploaded',
            'errors': errors
        }), 400

# ========== DELETE ROUTES ==========
@app.route('/delete/project/<project_name>')
@login_required
def delete_project(project_name):
    project_path = os.path.join(app.config['UPLOAD_FOLDER'], project_name)
    
    if os.path.exists(project_path):
        force_delete_folder(project_path)
        
        # Delete from database as well
        File.query.filter_by(project_name=project_name).delete()
        Dependency.query.filter_by(project_name=project_name).delete()
        db.session.commit()
        
        remove_empty_folders(app.config['UPLOAD_FOLDER'])
        return redirect(url_for('dashboard', msg=f'Project "{project_name}" deleted successfully!'))
    else:
        return redirect(url_for('dashboard', error='Project not found'))

@app.route('/delete/file/<project_name>/<path:file_path>')
@login_required
def delete_file(project_name, file_path):
    full_path = os.path.join(app.config['UPLOAD_FOLDER'], project_name, file_path)
    
    if os.path.exists(full_path):
        force_delete_file(full_path)
        normalized_path = os.path.normpath(full_path)
        File.query.filter_by(project_name=project_name, filepath=normalized_path).delete()
        Dependency.query.filter(
            (Dependency.project_name == project_name) &
            ((Dependency.parent_file == os.path.basename(file_path)) | (Dependency.child_file == os.path.basename(file_path)))
        ).delete(synchronize_session=False)
        db.session.commit()
        folder_to_clean = os.path.dirname(full_path)
        remove_empty_folders(folder_to_clean)
        return redirect(url_for('dashboard', msg=f'File deleted successfully!'))
    else:
        return redirect(url_for('dashboard', error='File not found'))

# ========== VIEW FILE CONTENTS ==========
@app.route('/view/<project_name>/<path:file_path>')
@login_required
def view_file(project_name, file_path):
    full_path = os.path.join(app.config['UPLOAD_FOLDER'], project_name, file_path)
    
    if os.path.exists(full_path):
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return render_template('view_file.html', 
                                 project_name=project_name, 
                                 file_path=file_path, 
                                 content=content)
        except Exception as e:
            return f"Error reading file: {e}", 500
    else:
        return f"File not found: {full_path}", 404

# ========== AI ROUTES ==========
@app.route('/ask', methods=['GET', 'POST'])
@login_required
def ask_question():
    """Ask AI questions about your code"""
    if not AI_AVAILABLE:
        return render_template('ask.html', 
                             query="", 
                             answer={'answer': '⚠️ AI features are not available. Please check your API key in config.py', 'sources': []})
    
    answer = None
    query = ""
    
    if request.method == 'POST':
        query = request.form.get('query', '')
        if query:
            try:
                result = rag_service.answer_query(query)
                answer = result
            except Exception as e:
                answer = {'answer': f"Error: {str(e)}", 'sources': []}
    
    return render_template('ask.html', query=query, answer=answer)

@app.route('/explain/<project_name>/<path:file_path>')
@login_required
def explain_file_route(project_name, file_path):
    """Get AI explanation of a file"""
    if not AI_AVAILABLE:
        return "⚠️ AI features are not available. Please check your API key in config.py"
    
    full_path = os.path.join(app.config['UPLOAD_FOLDER'], project_name, file_path)
    
    if os.path.exists(full_path):
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            explanation = rag_service.explain_file(file_path, content)
            
            return render_template('explain.html', 
                                 project_name=project_name,
                                 file_path=file_path,
                                 explanation=explanation,
                                 content=content)
        except Exception as e:
            return f"Error: {str(e)}", 500
    
    return "File not found", 404

@app.route('/generate-readme')
@login_required
def generate_readme():
    """Generate README for all projects"""
    if not AI_AVAILABLE:
        return "⚠️ AI features are not available. Please check your API key in config.py"
    
    all_files = project_service.list_all_project_files()
    
    try:
        readme = rag_service.generate_readme(all_files)
    except Exception as e:
        readme = f"Error generating README: {str(e)}"
    
    return render_template('generate_readme.html', readme=readme)

# ========== AI SEARCH ROUTES ==========
@app.route('/ai-search')
@login_required
def ai_search():
    """AI-powered semantic search page"""
    if not AI_AVAILABLE:
        return render_template('ai_search.html', ai_available=False)
    return render_template('ai_search.html', ai_available=True)

@app.route('/api/search', methods=['POST'])
@login_required
def api_search():
    """API endpoint for AI semantic search with project filtering"""
    if not AI_AVAILABLE:
        return jsonify({'success': False, 'error': 'AI features not available'}), 503
    
    data = request.get_json()
    query = data.get('query', '')
    project = data.get('project', '')
    
    if not query:
        return jsonify({'success': False, 'error': 'No query provided'}), 400
    
    try:
        result = rag_service.answer_query(query, project)
        return jsonify({
            'success': True,
            'answer': result.get('answer', ''),
            'sources': result.get('sources', [])
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== API PROJECTS ROUTE ==========
@app.route('/api/projects')
@login_required
def api_projects():
    """API endpoint to get all projects and their files"""
    return jsonify({'success': True, 'projects': project_service.list_projects()})

# ========== DEBUG INDEX ROUTE ==========
@app.route('/debug/index')
@login_required
def debug_index():
    """Force index all uploaded files"""
    results = []
    uploads_path = app.config['UPLOAD_FOLDER']
    file_id = 1
    
    if os.path.exists(uploads_path):
        for project in os.listdir(uploads_path):
            project_path = os.path.join(uploads_path, project)
            if os.path.isdir(project_path):
                for root, dirs, files in os.walk(project_path):
                    dirs[:] = [d for d in dirs if not should_skip_directory(d)]
                    for file in files:
                        if not should_skip_file(file) and file.endswith(('.py', '.js', '.html', '.css', '.txt', '.md', '.json')):
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                
                                if content.strip():
                                    indexed = index_file_chunks(file_id, file, content)
                                    results.append(f"✅ Indexed: {file} ({indexed} chunks)")
                                    file_id += 1
                                else:
                                    results.append(f"⚠️ Empty: {file}")
                            except Exception as e:
                                results.append(f"❌ Error: {file} - {e}")
    
    if not results:
        results.append("No files found to index. Please upload a ZIP file first.")
    
    return "<br>".join(results)

# ========== DEPENDENCY ROUTES ==========
@app.route('/dependencies')
@login_required
def dependencies_page():
    """Show the dependency graph page"""
    project_name = request.args.get('project')
    
    # If a specific project is requested, build/get its dependencies
    if project_name:
        # Build if no dependencies exist for this project
        if not Dependency.query.filter_by(project_name=project_name).first():
            dependency_service.build_dependency_graph(project_name)
        deps = dependency_service.get_dependencies(project_name)
    else:
        # Show all if no project specified
        if not Dependency.query.first():
            dependency_service.build_dependency_graph()
        deps = dependency_service.get_dependencies()
    
    # Get all files for this project
    if project_name:
        all_files = File.query.filter_by(project_name=project_name).all()
    else:
        all_files = File.query.all()
        
    # Initialize graph_data with all files (empty list for children)
    graph_data = {f.filename: [] for f in all_files}
    
    # Fill in dependencies
    for dep in deps:
        if dep.parent_file in graph_data:
            graph_data[dep.parent_file].append(dep.child_file)
        else:
            # Handle cases where parent might not be in all_files (unlikely but safe)
            graph_data[dep.parent_file] = [dep.child_file]
        
    return render_template('dependencies.html', 
                         graph_data=graph_data, 
                         total_deps=len(deps),
                         project_name=project_name)

@app.route('/api/build-graph')
@login_required
def api_build_graph():
    """Force rebuild the dependency graph"""
    project_name = request.args.get('project')
    try:
        dependency_service.build_dependency_graph(project_name)
        return jsonify({'success': True, 'message': 'Dependency graph rebuilt successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False)
