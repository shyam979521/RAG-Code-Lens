from flask import Blueprint, render_template, request, redirect, url_for
from app.models.models import File
from app.services.file_service import FileService
import os

main_bp = Blueprint('main', __name__)
file_service = FileService()

@main_bp.route('/')
def dashboard():
    files = File.query.all()
    return render_template('dashboard.html', files=files)

@main_bp.route('/upload')
def upload_page():
    return render_template('upload.html')

@main_bp.route('/process', methods=['POST'])
def process_upload():
    file = request.files['file']
    if not os.path.exists('workspace'):
        os.makedirs('workspace')
    path = os.path.join('workspace', 'upload.zip')
    file.save(path)
    
    extract_path = os.path.join('workspace', 'extracted')
    if not os.path.exists(extract_path):
        os.makedirs(extract_path)
    
    file_service.process_zip(path, extract_path)
    return redirect(url_for('main.dashboard'))