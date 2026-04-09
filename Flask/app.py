from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)

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


@app.route('/')
def home():
    latest_upload = session.get('last_uploaded_file')
    uploads = sorted(UPLOAD_FOLDER.glob('*.zip'), key=lambda item: item.stat().st_mtime, reverse=True)
    recent_uploads = [item.name for item in uploads[:4]]
    upload_count = len(uploads)
    user_count = User.query.count()
    return render_template(
        'index.html',
        latest_upload=latest_upload,
        recent_uploads=recent_uploads,
        upload_count=upload_count,
        user_count=user_count,
    )


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


if __name__ == '__main__':
    app.run(debug=True)
