# from flask import Blueprint, render_template, request, redirect, url_for
# from app.models.models import File

# main_bp = Blueprint('main', __name__)

# @main_bp.route('/')
# def dashboard():
#     files = File.query.all()
#     return render_template('dashboard.html', files=files)

# @main_bp.route('/upload')
# def upload_page():
#     return render_template('upload.html')


from flask import Blueprint, render_template, request, redirect, url_for
from app.models.models import File

@main_bp.route('/process', methods=['POST'])
def process_upload():
    file = request.files['file']
    path = os.path.join('workspace', 'upload.zip')
    file.save(path)
    file_service.process_zip(path, 'workspace/extracted')
    return redirect(url_for('main.dashboard'))