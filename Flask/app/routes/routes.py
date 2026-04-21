from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app
from app.services.file_service import FileService
from app.services.rag_service import RagService
from app.services.explain_service import ExplainService
from app.services.docs_service import DocsService
from app.services.dependency_service import DependencyService
from app.models.models import File
import os
from datetime import datetime 
from functools import wraps 
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, session, url_for  
from flask_sqlalchemy import SQLAlchemy  
from werkzeug.security import check_password_hash, generate_password_hash  
from werkzeug.utils import secure_filename 

main_bp = Blueprint('main', __name__)

# Initialize services (lazy init might be better but this is fine for Flask)
# Note: In production, we might use dependency injection or current_app context
file_service = FileService()
rag_service = RagService()
explain_service = ExplainService()
docs_service = DocsService()
dep_service = DependencyService()

BASE_DIR = Path(__file__).resolve().parent    
UPLOAD_FOLDER = BASE_DIR / 'uploads'                                                                                                                                                        
ALLOWED_EXTENSIONS = {'zip'}                                                                                               
MAX_UPLOAD_SIZE = 100 * 1024 * 1024                                                                                                         

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{BASE_DIR / 'users.db'}"                                                                       
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False                                                      
app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)                                                         
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_SIZE                                                                                                                                                   
app.secret_key = 'secret_key'                                                                   

UPLOAD_FOLDER.mkdir(exist_ok=True)                                                                                                                                                                   

db = SQLAlchemy(app)                                                                                                                                                                                 


class User(db.Model):                                                                                          
    id = db.Column(db.Integer, primary_key=True)                                                             
    name = db.Column(db.String(100), nullable=False)                                                                       
    email = db.Column(db.String(50), unique=True, nullable=False)                                                                                                
    password = db.Column(db.String(200), nullable=False)                                                                           


with app.app_context():                                                                                                                                                                             
    db.create_all()                                                                                                                                                           


def normalize_email(email):                                                                                                     
    return (email or '').strip().lower()                                                                                                     


def validate_email(email):                                                                                               
    email = normalize_email(email)                                                                                                                                                                                                                                            
    if not email or '@' not in email:                                                                                                                                                                              
        return False

    local_part, _, domain = email.partition('@')                                                                                                                                                                                                                                                                        
    return bool(local_part and domain and '.' in domain)                                                                                                                                                                                                                                                                  


def validate_password(password):                                                                                             
    return (
        bool(password)                                                                                                  
        and len(password) >= 8                                                                                                                                                                                  
        and any(char.isalpha() for char in password)                                                                                                                                                                                                       
        and any(char.isdigit() for char in password)                                                                                                                                                                                
        and any(not char.isalnum() for char in password)                                                                                                                                                                                                  
    )


def allowed_file(filename):                                                                                   
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS                                                                                                                                                                                                                                                                                                  
                                                                                                                                                                                                                                                                                             


def save_uploaded_zip(file_storage):                                                                                                                    
    filename = secure_filename(file_storage.filename)                                                                                                                                                                                                                  
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')                                                                                                                                                                                                                                                                            
    destination = UPLOAD_FOLDER / f'{timestamp}_{filename}'                                                                                                                                                                                                                                                                                                                                                                           
    file_storage.save(destination)                                                                                                                                                                          
    return destination.name                                                                                                                                                                            


def login_required(f):                                                                                                                                       
    @wraps(f)                                                                                                                                                                                                                                                                                    
    def decorated(*args, **kwargs):                                                                                                                                                                                                                                                                             
        if 'user_id' not in session:                                                                                                                                                                                                                                                                                                                        
            flash('Please login to access this page.', 'error')                                                                                                                                                                                                         
            return redirect(url_for('signin'))  
        return f(*args, **kwargs)                                                                                                                                                                                                                                         
    return decorated                                                                                                                                                                      


@app.errorhandler(413)                                                                                                                                                                         
def file_too_large(_error):                                                                                                                                                                                                                                                                                      
    flash('File size must be less than 100MB.', 'error')                                                                                                                                                                                                                                                                               
    return redirect(url_for('home'))                                                                                                                                                                                                   


@main_bp.route('/upload', methods=['GET'])
def upload_page():
    return render_template('upload.html')

@main_bp.route('/')
def index():
    return render_template('index.html')


@app.route('/signin', methods=['GET', 'POST'])                                                                                                                                                                                                                             
def signin():
    if request.method == 'POST':                                                                                                                                                                                                                                                                                                           
        email = normalize_email(request.form.get('email'))                                                                                                                                                                                                                                                                                                                          
        password = request.form.get('password', '')                                                                                                                                                                                                                                                                                                    

        user = User.query.filter_by(email=email).first()                                                                                                                                                                                                                                                                                                                            

        if user and check_password_hash(user.password, password):                                                                                                                                                                                                                                                                                                                                                                                 
            session['user_id'] = user.id                                                                                                                                                                                                                                                 
            session['user_name'] = user.name                                                                                                                                                                                                                                                  
            flash(f'Welcome back, {user.name}!', 'success')                                                                                                                                                                                                                                                      
            return redirect(url_for('home'))                                                                                                                                                                                        

        flash('Invalid email or password.', 'error')                                                                                                                                                                                                                                                                                                                          
        return redirect(url_for('signin'))                                                                                                                                                                                                                             

    return render_template('login.html')                                                                                                                                                                                                                                     


@app.route('/signup', methods=['GET', 'POST'])                                                                                                                                                                                                                                    
def signup():
    if request.method == 'POST':                                                                                                                                                                                                                                                                                                                                                          
        name = request.form.get('name', '').strip()                                                                                                                                                                                                                                                                                                                                                                                                                
        email = normalize_email(request.form.get('email'))                                                                                                                                                                                                                                                                                                                                    
        password = request.form.get('password', '')                                                                                                                                                                                                                                                                                                                  
        confirm_password = request.form.get('confirm_password', '')                                                                                                                                                                                                                                                                                                                                                  

        if len(name) < 2:                                       
            flash('Name must be at least 2 characters long.', 'error')                           
            return redirect(url_for('signup'))                                                                                  

        if not validate_email(email):                                          
            flash('Please enter a valid email address.', 'error')                                                                                                                           
            return redirect(url_for('signup'))                                                                                          

        if not validate_password(password):                                             
            flash('Password must be at least 8 characters long and contain letters, numbers, and a special character.', 'error')                                                                                                                                                                                                                                                           
            return redirect(url_for('signup'))                                                                                     

        if confirm_password != password:                                                                         
            flash('Confirm password should match password.', 'error')                                                                                                                                                                          
            return redirect(url_for('signup'))                                                                                             

        existing_user = User.query.filter_by(email=email).first()                                                               
        if existing_user:                    
            flash('Email already exists. Please login.', 'error')                                                                                                      
            return redirect(url_for('signup'))                                                                                

        new_user = User(name=name, email=email, password=generate_password_hash(password))                                                                                                                                                                                                                              

        try:                                                     
            db.session.add(new_user)                                                                                                                                                                            
            db.session.commit()                                                                                                                                                                                         
            flash('Registration successful. Please sign in.', 'success')                                                                                                                                                                                                                                                                             
            return redirect(url_for('signin'))                                                                                                                                                                                                           
        except Exception:                                                                                                                                                                                                                                    
            db.session.rollback()                                                                                                                                                                                                                                            
            flash('Some error occurred while registering.', 'error')                                                                                                                                                                                                                                              
            return redirect(url_for('signup'))                                                                                                                                                                                                                                        

    return render_template('register.html')                                                                                                                                                                                                                                                  


@app.route('/forgot-password', methods=['GET', 'POST'])                                                                                                                                                                                                                                                              
def forgot_password():
    if request.method == 'POST':                                                                                                                                                                                                                                                                                                                                                                                 
        email = normalize_email(request.form.get('email'))                                                                                                                                                                                                                                                                                                                                          
        password = request.form.get('password', '')                                                                                                                                                                                                                                                                                                                            
        confirm_password = request.form.get('confirm_password', '')                                                                                                                                                                                                                                                                                                                                                        

        if not validate_email(email):                                                                                                                                                                                                                                      
            flash('Please enter a valid email address.', 'error')                                                                                                                                                                                  
            return redirect(url_for('forgot_password'))                                                                                                                                                                                                                                      

        user = User.query.filter_by(email=email).first()                                                                                                                                                                                                                                                                                                                      
        if not user:                                                                                                                                                                                                                                                                                             
            flash('No account found for that email.', 'error')                                                                                                                                                                                              
            return redirect(url_for('forgot_password'))                                                                                                                                                                                                                                                             

        if not validate_password(password):                                                                                                                                                                                                                     
            flash('New password must be at least 8 characters long and contain letters, numbers, and a special character.', 'error')                                                                                                                                                                                                                                                                             
            return redirect(url_for('forgot_password'))                                                                                                                                                                                                                            

        if password != confirm_password:                                                                                                                                                                                                                                   
            flash('Confirm password should match the new password.', 'error')                                                                                                                                                                                                                                   
            return redirect(url_for('forgot_password'))                                                                                                                                                                                                                                                                           

        user.password = generate_password_hash(password)                                                                
        db.session.commit()                                                                                 
        flash('Password updated successfully. Please sign in.', 'success')                                                                                                                                                                                                                                                                                                
        return redirect(url_for('signin'))                                                                                                                                                                                                                      

    return render_template('forgot_password.html')                                                                                                                                                                                                                                                                             


@app.route('/ask', methods=['POST'])                                                                                                                                                                                                          
@login_required                                                                                                                                                                                                                                                                                                                                                                        
def ask(): 
    question = request.form.get('questionInput', '').strip()                                                                                                                                                                                                                                                                                                                                                                                                                        

    if not question:                                 
        flash('Please enter a question.', 'error')                                                                                                                                                                                                                                                                                                     
        return redirect(url_for('home'))                                                                                                                                                                                                                                                  

    flash(f'Your question was: {question}', 'success')                                                        
    return redirect(url_for('home'))                               


@app.route('/upload', methods=['POST'])                                                                                                                                                                                                                     
@login_required                                                                                                                                                                                                                                                                                                                                                                          
def upload_file():
    file = request.files.get('fileInput')                                                                                                                                                                                                                           

    if not file or file.filename == '':                                                                                                                                                                                                                                                                
        flash('Please select a ZIP file.', 'error')                                                                                                                                                                                                                                                                                                                             
        return redirect(url_for('home'))                                                                                                                                                                                                          

    if not allowed_file(file.filename):                                                                                                                                                                                                                                                                                                        
        flash('Only ZIP files are allowed.', 'error')                                                                                                                                                                                                                                                                                      
        return redirect(url_for('home'))                                                                                                                                                                                                                          

    saved_name = save_uploaded_zip(file)                                                                                                                                                                                                                                                                                                                                  
    session['last_uploaded_file'] = saved_name                                                                                                                                                                                                                                                                                                              
    flash(f'File "{saved_name}" uploaded successfully.', 'success')                                                                                                                                                                                                                                                                                                      
    return redirect(url_for('home'))                                                                                                                                                                                                                                                    


@app.route('/logout')                                                                                                                                                                                                                            
def logout():
    user_name = session.get('user_name')                                                                                                                                                                                                                                                                                                    
    last_uploaded_file = session.get('last_uploaded_file')                                                                                                                                                                                                                                                                                                                                                                     
    session.clear()                                                                                                                                                                                                                                                                      

    if last_uploaded_file:                                                                                                                                                                                                                                                                                                                                                                                                               
        session['last_uploaded_file'] = last_uploaded_file                                                                                                                                                                                                                                                                                                                                                                               

    if user_name:                                   
        flash(f'{user_name}, you have been logged out.', 'success')                                                                                                                                                                                                                                                
    else:                                                                                                
        flash('Logged out successfully.', 'success')                                                                                                                                                                                                                                       
    return redirect(url_for('home')) 

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
