from datetime import datetime # to add time and date to the uploaded file name
from functools import wraps # to create a decorator for routes that require login
from pathlib import Path # to handle file paths in a platform-independent way

from flask import Flask, flash, redirect, render_template, request, session, url_for  # to handle web requests, sessions, and rendering templates
from flask_sqlalchemy import SQLAlchemy  # to interact with the SQLite database for user management
from werkzeug.security import check_password_hash, generate_password_hash  # to securely hash and verify user passwords
from werkzeug.utils import secure_filename # to safely handle uploaded file names and prevent directory traversal attacks

app = Flask(__name__) # Initialize the Flask application

BASE_DIR = Path(__file__).resolve().parent    # “Meri current file (app.py) ka folder ka path nikaalo”
UPLOAD_FOLDER = BASE_DIR / 'uploads'  # “Ek folder ka path banao jiska naam uploads hai, aur wo current file ke folder ke andar hoga” (yeh uploads folder me hum zip files ko store karenge)
ALLOWED_EXTENSIONS = {'zip'}  # “Ek set banao jisme allowed file extensions hon, is case me sirf zip files hi allowed hain”
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # “Ek variable banao jisme maximum upload size define karo, is case me 100MB (100 * 1024 * 1024 bytes)”

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{BASE_DIR / 'users.db'}" # Database ka address set kar rahe ho, Data users.db file me save hoga
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Database me changes ko track mat karo unnecessarily
app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER) #“Jo bhi file upload hogi → usse is folder me save karo”
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_SIZE # “Jo bhi file upload hogi → uski size isse zyada nahi honi chahiye” (agar user 100MB se badi file upload karne ki koshish karega to error aayega)
app.secret_key = 'secret_key'  #“Login/session data ko secure rakhne ke liye password jaisi key”

UPLOAD_FOLDER.mkdir(exist_ok=True) # “Uploads folder ko create karo agar wo already exist nahi karta hai” (yeh ensure karega ki uploads folder hamesha available ho jab bhi koi file upload karni ho)

db = SQLAlchemy(app) # “SQLAlchemy ko Flask app ke saath integrate karo taaki hum database operations kar sakein” (yeh humein database me users ko add karne, unhe query karne, etc. ki suvidha dega)


class User(db.Model): # Database me table bana rahe ho jiska naam User hai, aur usme columns define kar rahe ho
    id = db.Column(db.Integer, primary_key=True) # “Ek column banao jiska naam id hai, aur wo primary key ho”
    name = db.Column(db.String(100), nullable=False) # “Ek column banao jiska naam name hai, aur wo null nahi hona chahiye”
    email = db.Column(db.String(50), unique=True, nullable=False) # “Ek column banao jiska naam email hai, aur wo unique hona chahiye aur null nahi hona chahiye”
    password = db.Column(db.String(200), nullable=False) # “Ek column banao jiska naam password hai, aur wo null nahi hona chahiye”


with app.app_context(): # “Flask application context ke andar” (yeh ensure karega ki database operations Flask app ke context me ho rahe hain, jisse ki database connection properly manage ho sake)
    db.create_all() # “Database me defined tables ko create karo” (agar tables already exist karte hain to yeh command unhe overwrite nahi karega, balki unhe maintain karega)


def normalize_email(email): # “Ek function banao jiska naam normalize_email hai, jo email ko standard format me convert karega” 
    return (email or '').strip().lower() #(yeh function email ko lowercase me convert karega aur uske aage-peeche ke spaces ko remove karega)


def validate_email(email): # “Ek function banao jiska naam validate_email hai, jo email address ki validity check karega”
    email = normalize_email(email) # “Pehle email ko normalize karo taaki uska format standard ho jaye” (yeh ensure karega ki email validation ke liye hum hamesha normalized email ka use kar rahe hain, jisse ki case sensitivity aur extra spaces ke issues se bach sakein)
    if not email or '@' not in email: # “Agar email empty hai ya usme @ symbol nahi hai, to email invalid hai” (yeh basic check karega ki email address me @ symbol hona chahiye aur email empty nahi hona chahiye)
        return False

    local_part, _, domain = email.partition('@') # “Email ko @ symbol ke basis par do parts me divide karo: local_part (jo @ se pehle wala hissa hai) aur domain (jo @ ke baad wala hissa hai)” (yeh email address ko local part aur domain me split karega, jisse ki hum dono parts ki alag-alag validation kar sakein)
    return bool(local_part and domain and '.' in domain) # “Email valid hai agar local_part aur domain dono non-empty hain, aur domain me at least ek dot (.) symbol hai” (yeh ensure karega ki email address me local part aur domain dono hon, aur domain me dot symbol hona chahiye jisse ki valid domain structure ho)


def validate_password(password): # “Ek function banao jiska naam validate_password hai, jo password ki strength check karega”
    return (
        bool(password) # “Password valid hai agar wo empty nahi hai” (yeh check karega ki password field empty nahi hai)
        and len(password) >= 8 # “Password valid hai agar uski length 8 characters ya usse zyada hai” (yeh ensure karega ki password kam se kam 8 characters ka hona chahiye, jisse ki password thoda strong ho)
        and any(char.isalpha() for char in password) # “Password valid hai agar usme at least ek letter (a-z ya A-Z) hai” (yeh check karega ki password me kam se kam ek alphabetic character hona chahiye, jisse ki password me letters ka combination ho)
        and any(char.isdigit() for char in password) # “Password valid hai agar usme at least ek digit (0-9) hai” (yeh check karega ki password me kam se kam ek digit hona chahiye, jisse ki password me numbers ka combination ho)
        and any(not char.isalnum() for char in password) # “Password valid hai agar usme at least ek special character hai” (yeh check karega ki password me kam se kam ek special character hona chahiye, jisse ki password me symbols ka combination ho)
    )


def allowed_file(filename): #Check karta hai file allowed hai ya nahi (is case me sirf zip files allowed hain)
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS #“Filename me dot (.) hona chahiye, aur uske baad ka extension (jo last dot ke baad wala hissa hai) allowed extensions me se ek hona chahiye” (yeh ensure karega ki user sirf zip files hi upload kar sakta hai, aur koi bhi file jiska extension zip nahi hai, usse upload karne se roka jayega)
# (def allowed_file(filename):-----Check karta hai file allowed hai ya nahi,         '.' in filename---👉 File me extension hai ya nahi,         filename.rsplit('.', 1)[1].lower()-- File ka extension nikaal raha hai,        in ALLOWED_EXTENSIONS---kya ye extension allowed list me hai?)


def save_uploaded_zip(file_storage): # “Ek function banao jiska naam save_uploaded_zip hai, jo uploaded file ko save karega aur uska naam return karega”
    filename = secure_filename(file_storage.filename) # “Uploaded file ka naam secure karo taaki usme koi malicious path ya characters na ho” (yeh function filename ko sanitize karega, jisse ki koi bhi harmful characters ya path traversal attempts se bach sakein)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S') # “Current date and time ko ek string me convert karo jiska format hai YYYYMMDDHHMMSS” (yeh timestamp generate karega, jisse ki hum uploaded files ke naam me unique identifier ke roop me use kar sakte hain, taaki multiple uploads ke case me file name conflicts na ho)
    destination = UPLOAD_FOLDER / f'{timestamp}_{filename}' # “Destination path banao jisme uploads folder ke andar ek file hogi jiska naam hoga timestamp_ followed by the original filename” (yeh ensure karega ki uploaded file ka naam unique ho, kyunki har file ke naam ke aage current timestamp add ho jayega, jisse ki agar do files same naam ki bhi upload hoti hain, to unke naam me timestamp ke wajah se fark aa jayega)
    file_storage.save(destination) # “Uploaded file ko destination path par save karo” (yeh command uploaded file ko specified location par store karega, jisse ki hum us file ko baad me access kar sakein)
    return destination.name # “Saved file ka naam return karo” (yeh function uploaded file ka final name return karega, jisme timestamp bhi included hoga, jisse ki hum us file ko identify kar sakein)


def login_required(f): # “Ek decorator banao jiska naam login_required hai, jo routes ko protect karega taaki sirf logged-in users hi unhe access kar sakein”
    @wraps(f) # “Flask ke wraps decorator ka use karo taaki original function ke metadata (jaise naam, docstring, etc.) ko preserve kiya ja sake” (yeh ensure karega ki jab hum login_required decorator ka use karenge, to original function ke naam aur docstring jaisi information lost na ho)
    def decorated(*args, **kwargs): # “Ek inner function banao jiska naam decorated hai, jo original function ko wrap karega” (yeh inner function original function ke around ek wrapper ka kaam karega, jisme hum login check karenge aur agar user logged in nahi hai to usse login page par redirect karenge)
        if 'user_id' not in session: # “Check karo ki session me user_id key exist karti hai ya nahi, jiska matlab hai ki user logged in hai ya nahi” (yeh check karega ki user login hai ya nahi, kyunki jab user login karta hai to uska user_id session me store ho jata hai, aur agar wo key session me nahi hai to iska matlab user logged in nahi hai)
            flash('Please login to access this page.', 'error') # “Agar user logged in nahi hai, to ek flash message show karo jisme user ko login karne ke liye kaha jaye” (yeh message user ko inform karega ki unhe is page ko access karne ke liye login karna hoga)
            return redirect(url_for('signin')) #
        return f(*args, **kwargs) # “Agar user logged in hai, to original function ko call karo aur uske arguments pass karo” (yeh ensure karega ki agar user login hai, to wo original function ko access kar sakta hai, aur uske arguments bhi properly pass ho jayenge)
    return decorated # “Login_required decorator ko return karo” (yeh decorator function ko return karega, jise hum apne routes par apply kar sakte hain taaki unhe login protection mile)


@app.errorhandler(413) # “Flask me ek error handler define karo jo 413 status code (Request Entity Too Large) ke liye trigger hoga, jab user 100MB se badi file upload karne ki koshish karega”
def file_too_large(_error): # “Error handler function banao jiska naam file_too_large hai, jo error object ko parameter ke roop me lega” (yeh function 413 error ke case me call hoga, aur usme error details pass ki jayengi, jise hum ignore kar sakte hain kyunki hume sirf user ko ek message show karna hai)
    flash('File size must be less than 100MB.', 'error') # “Ek flash message show karo jisme user ko bataya jaye ki file size 100MB se kam honi chahiye” (yeh message user ko inform karega ki unhe 100MB se choti file upload karni hogi, aur agar wo badi file upload karne ki koshish karenge to unhe yeh error message dikhai dega)
    return redirect(url_for('home')) # “User ko home page par redirect karo” (yeh ensure karega ki jab user 413 error encounter kare, to wo home page par wapas chala jaye, jahan se wo apni file upload karne ki koshish kar raha tha)


@app.route('/')  # “Flask me ek route define karo jo root URL (/) ke liye trigger hoga, aur uske corresponding function ka naam home hai” (yeh route application ke home page ko serve karega, jahan se users apni activities start karenge)
def home(): # “Home function banao jo home page ko render karega” (yeh function home page ke liye logic handle karega, jisme hum recent uploads, upload count, user count, etc. ki information prepare karenge aur usse template me pass karenge)
    latest_upload = session.get('last_uploaded_file') # “Session se last_uploaded_file key ki value nikaalo, jisme user ne jo last file upload ki hai uska naam store hoga” (yeh variable latest_upload me user ke last uploaded file ka naam store karega, jise hum home page par display kar sakte hain)
    uploads = sorted(UPLOAD_FOLDER.glob('*.zip'), key=lambda item: item.stat().st_mtime, reverse=True) # “Uploads folder me jitni bhi zip files hain unhe nikaalo, unhe unke modification time ke basis par sort karo (sabse recent upload pehle aayega)” (yeh line uploads folder me se sabhi zip files ko list karega, aur unhe unke last modified time ke basis par descending order me sort karega, jisse ki hum recent uploads ko easily identify kar sakein)
    recent_uploads = [item.name for item in uploads[:4]] # “Sorted uploads me se top 4 items nikaalo, unke names ko ek list me store karo” (yeh line sorted uploads list me se sabse recent 4 uploads ke names ko extract karega aur unhe recent_uploads list me store karega, jise hum home page par display kar sakte hain)
    upload_count = len(uploads) # “Total number of uploads ko calculate karo” (yeh line uploads list ki length calculate karega, jisse ki hume total number of uploaded files ka pata chalega, aur is information ko bhi home page par display kar sakte hain)
    user_count = User.query.count() # “Total number of users ko calculate karo” (yeh line User model se sabhi users ki count calculate karega, jisse ki hume total number of registered users ka pata chalega, aur is information ko bhi home page par display kar sakte hain)
    return render_template( # “Home template ko render karo aur usme variables pass karo” (yeh line home.html template ko render karega, aur upar define kiye gaye variables ko usme pass karega)
        'index.html', # “Home template ka naam index.html hai” (yeh ensure karega ki home page ke liye index.html template use ho)
        latest_upload=latest_upload, # “Template me latest_upload variable ke roop me user ke last uploaded file ka naam pass karo” (yeh ensure karega ki home page par user ke last uploaded file ka naam display ho)
        recent_uploads=recent_uploads, # “Template me recent_uploads variable ke roop me recent uploads ki list pass karo” (yeh ensure karega ki home page par recent uploads ki list display ho)
        upload_count=upload_count, # “Template me upload_count variable ke roop me total number of uploads pass karo” (yeh ensure karega ki home page par total number of uploaded files display ho)
        user_count=user_count, # “Template me user_count variable ke roop me total number of users pass karo” (yeh ensure karega ki home page par total number of registered users display ho)
    )


@app.route('/signin', methods=['GET', 'POST']) # “Flask me ek route define karo jo /signin URL ke liye trigger hoga, aur usme GET aur POST dono methods allow karo” (yeh route sign-in page ko serve karega, jahan users apne credentials enter karke login kar sakte hain)
def signin():
    if request.method == 'POST': # “Agar request method POST hai, to iska matlab user login form submit kar raha hai, to login logic ko handle karo” (yeh check karega ki user login form submit kar raha hai ya nahi, aur agar wo submit kar raha hai to hum uske credentials ko validate karenge aur usse login karne ki koshish karenge)
        email = normalize_email(request.form.get('email')) # “Login form se email field ki value nikaalo, usse normalize karo taaki wo standard format me ho jaye” (yeh line login form se email address ko extract karega, aur usse normalize_email function ke through standard format me convert karega, jisse ki case sensitivity aur extra spaces ke issues se bach sakein)    
        password = request.form.get('password', '') # “Login form se password field ki value nikaalo, agar wo field exist nahi karti hai to empty string return karo” (yeh line login form se password ko extract karega, aur agar password field form me nahi hai to usse empty string set karega, jisse ki hum password validation me use kar sakein)

        user = User.query.filter_by(email=email).first() # “Database me User model ke through query karo taaki email ke basis par user ko find karo, aur pehla matching user return karo” (yeh line database me se user ko email address ke basis par search karega, aur agar koi user milta hai to uska record return karega, jisse ki hum uske password ko verify kar sakein)     

        if user and check_password_hash(user.password, password): # “Agar user milta hai aur uska password hash check_password_hash function ke through verify hota hai, to login successful hai” (yeh line check karega ki user record exist karta hai ya nahi, aur agar karta hai to uske stored password hash ko check_password_hash function ke through verify karega, jisse ki hum ensure kar sakein ki user ne sahi password enter kiya hai)
            session['user_id'] = user.id # “Session me user_id key set karo jisme user ka id store hoga, jisse ki hum user ke login state ko track kar sakein” (yeh line session me user_id store karega, jisse ki hum future requests me check kar sakein ki user logged in hai ya nahi)
            session['user_name'] = user.name # “Session me user_name key set karo jisme user ka name store hoga, jisse ki hum user ke naam ko display kar sakein” (yeh line session me user_name store karega, jisse ki hum home page ya kisi bhi page par user ke naam ko display kar sakein)
            flash(f'Welcome back, {user.name}!', 'success') # “Ek flash message show karo jisme user ko welcome back message dikhaya jaye, aur usme user ka name include karo” (yeh message user ko inform karega ki unka login successful hai, aur unke naam ke saath ek personalized welcome message dikhayega)
            return redirect(url_for('home')) # “User ko home page par redirect karo” (yeh ensure karega ki jab user successfully login ho jata hai, to wo home page par chala jaye, jahan se wo apni activities start kar sakta hai)

        flash('Invalid email or password.', 'error') # “Agar user nahi milta hai ya password verification fail hota hai, to ek flash message show karo jisme user ko invalid email or password message dikhaya jaye” (yeh message user ko inform karega ki unka login attempt unsuccessful tha, aur unhe sahi email address aur password enter karne ke liye encourage karega)
        return redirect(url_for('signin')) # “User ko signin page par wapas redirect karo” (yeh ensure karega that agar login attempt fail hota hai, to user wapas login page par chala jaye, jahan se wo apne credentials ko correct karke dobara login kar sakta hai)

    return render_template('login.html') # “Agar request method GET hai, to simply login.html template ko render karo” (yeh ensure karega ki jab user /signin URL par visit kare, to usse login page dikhai de, jahan se wo apne credentials enter karke login kar sakta hai)


@app.route('/signup', methods=['GET', 'POST']) # “Flask me ek route define karo jo /signup URL ke liye trigger hoga, aur usme GET aur POST dono methods allow karo” (yeh route sign-up page ko serve karega, jahan new users apne details enter karke registration kar sakte hain)
def signup():
    if request.method == 'POST': # “Agar request method POST hai, to iska matlab user registration form submit kar raha hai, to registration logic ko handle karo” (yeh check karega ki user registration form submit kar raha hai ya nahi, aur agar wo submit kar raha hai to hum uske details ko validate karenge aur usse database me ek new user record create karke register karenge)
        name = request.form.get('name', '').strip() # “Registration form se name field ki value nikaalo, agar wo field exist nahi karti hai to empty string return karo, aur uske aage-peeche ke spaces ko remove karo” (yeh line registration form se user ke name ko extract karega, aur agar name field form me nahi hai to usse empty string set karega, aur uske aage-peeche ke extra spaces ko remove karega, jisse ki hum name validation me use kar sakein)
        email = normalize_email(request.form.get('email')) # “Registration form se email field ki value nikaalo, usse normalize karo taaki wo standard format me ho jaye” (yeh line registration form se email address ko extract karega, aur usse normalize_email function ke through standard format me convert karega, jisse ki case sensitivity aur extra spaces ke issues se bach sakein)
        password = request.form.get('password', '') # “Registration form se password field ki value nikaalo, agar wo field exist nahi karti hai to empty string return karo” (yeh line registration form se password ko extract karega, aur agar password field form me nahi hai to usse empty string set karega, jisse ki hum password validation me use kar sakein)
        confirm_password = request.form.get('confirm_password', '') # “Registration form se confirm_password field ki value nikaalo, agar wo field exist nahi karti hai to empty string return karo” (yeh line registration form se confirm password ko extract karega, aur agar confirm_password field form me nahi hai to usse empty string set karega, jisse ki hum confirm password validation me use kar sakein)

        if len(name) < 2: # Agar name 2 characters se chhota hai
            flash('Name must be at least 2 characters long.', 'error') #Error message show karega
            return redirect(url_for('signup')) #User ko signup page par wapas redirect karega taaki wo apna name sahi kar sakein

        if not validate_email(email): # Email valid hai ya nahi check karta hai
            flash('Please enter a valid email address.', 'error') # Agar email valid nahi hai, to ek flash message show karo jisme user ko valid email address enter karne ke liye kaha jaye
            return redirect(url_for('signup')) # User ko signup page par wapas redirect karo taaki wo apna email address sahi kar sakein

        if not validate_password(password): # Password valid hai ya nahi check karta hai
            flash('Password must be at least 8 characters long and contain letters, numbers, and a special character.', 'error') # Agar password valid nahi hai, to ek flash message show karo jisme user ko strong password enter karne ke liye kaha jaye (password kam se kam 8 characters ka hona chahiye, aur usme letters, numbers, aur special character ka combination hona chahiye)
            return redirect(url_for('signup')) # User ko signup page par wapas redirect karo taaki wo apna password sahi kar sakein

        if confirm_password != password: # Confirm password aur password match karte hain ya nahi check karta hai
            flash('Confirm password should match password.', 'error') # Agar confirm password password se match nahi karta hai, to ek flash message show karo jisme user ko confirm password ko password ke saath match karne ke liye kaha jaye
            return redirect(url_for('signup')) # User ko signup page par wapas redirect karo taaki wo apna confirm password sahi kar sakein

        existing_user = User.query.filter_by(email=email).first() #Database me check karta hai ki same email already hai ya nahi
        if existing_user: #Agar user mil gaya
            flash('Email already exists. Please login.', 'error') # Agar user already exists, to ek flash message show karo jisme user ko login karne ke liye kaha jaye
            return redirect(url_for('signup')) # User ko signup page par wapas redirect karo taaki wo login page par ja sakein

        new_user = User(name=name, email=email, password=generate_password_hash(password)) # “Ek new User object banao jisme name, email, aur password hash set karo” (yeh line ek new user record create karega jisme user ke name, email, aur password hash store hoga, jisse ki hum usse database me save kar sakein)

        try: # Database me new user record add karna attempt karo
            db.session.add(new_user) # “New user record ko database session me add karo” (yeh line new user record ko database session me add karega, jisse ki wo database me save hone ke liye ready ho jayega)
            db.session.commit() # “Database session ko commit karo taaki changes database me save ho jaye” (yeh line database session ko commit karega, jisse ki new user record database me permanently save ho jayega)
            flash('Registration successful. Please sign in.', 'success') # “Ek flash message show karo jisme user ko registration successful message dikhaya jaye, aur usme user ko sign in karne ke liye encourage kiya jaye” (yeh message user ko inform karega ki unka registration successful hai, aur unhe login karne ke liye encourage karega)
            return redirect(url_for('signin')) # “User ko signin page par redirect karo” (yeh ensure karega ki jab user successfully register ho jata hai, to wo login page par chala jaye, jahan se wo apne credentials enter karke login kar sakta hai)
        except Exception: # “Agar database me user record add karne ya commit karne ke dauran koi error aata hai, to usse handle karo” (yeh block database errors ko catch karega, jisse ki agar koi issue hota hai to hum usse gracefully handle kar sakein)
            db.session.rollback() # “Database session ko rollback karo taaki koi partial changes database me save na ho jaye” (yeh line database session ko rollback karega, jisse ki agar commit ke dauran error aata hai to koi bhi incomplete data database me save na ho)
            flash('Some error occurred while registering.', 'error') # “Ek flash message show karo jisme user ko registration ke dauran error occurred message dikhaya jaye” (yeh message user ko inform karega ki unka registration attempt unsuccessful tha, aur unhe dobara try karne ke liye encourage karega)
            return redirect(url_for('signup')) # “User ko signup page par wapas redirect karo” (yeh ensure karega ki agar registration attempt fail hota hai, to user wapas registration page par chala jaye, jahan se wo apne details ko correct karke dobara register kar sakta hai)

    return render_template('register.html') # “Agar request method GET hai, to simply register.html template ko render karo” (yeh ensure karega ki jab user /signup URL par visit kare, to usse registration page dikhai de, jahan se wo apne details enter karke registration kar sakta hai)


@app.route('/forgot-password', methods=['GET', 'POST']) # “Flask me ek route define karo jo /forgot-password URL ke liye trigger hoga, aur usme GET aur POST dono methods allow karo” (yeh route forgot password page ko serve karega, jahan users apne email address enter karke apna password reset kar sakte hain)
def forgot_password():
    if request.method == 'POST': # “Agar request method POST hai, to iska matlab user forgot password form submit kar raha hai, to forgot password logic ko handle karo” (yeh check karega ki user forgot password form submit kar raha hai ya nahi, aur agar wo submit kar raha hai to hum uske email address ko validate karenge, aur agar valid hai to uske password reset karne ke process ko handle karenge)
        email = normalize_email(request.form.get('email')) # “Forgot password form se email field ki value nikaalo, usse normalize karo taaki wo standard format me ho jaye” (yeh line forgot password form se email address ko extract karega, aur usse normalize_email function ke through standard format me convert karega, jisse ki case sensitivity aur extra spaces ke issues se bach sakein)
        password = request.form.get('password', '') # “Forgot password form se password field ki value nikaalo, agar wo field exist nahi karti hai to empty string return karo” (yeh line forgot password form se new password ko extract karega, aur agar password field form me nahi hai to usse empty string set karega, jisse ki hum password validation me use kar sakein)
        confirm_password = request.form.get('confirm_password', '') # “Forgot password form se confirm_password field ki value nikaalo, agar wo field exist nahi karti hai to empty string return karo” (yeh line forgot password form se confirm password ko extract karega, aur agar confirm_password field form me nahi hai to usse empty string set karega, jisse ki hum confirm password validation me use kar sakein)

        if not validate_email(email): # “Email valid hai ya nahi check karta hai” (yeh check karega ki user ne jo email address enter kiya hai wo valid format me hai ya nahi, jisse ki hum ensure kar sakein ki user apna email address sahi tarike se enter kar raha hai)
            flash('Please enter a valid email address.', 'error') # “Ek flash message show karo jisme user ko valid email address enter karne ke liye prompt dikhaya jaye” (yeh message user ko inform karega ki unka email address valid nahi hai)
            return redirect(url_for('forgot_password')) # “User ko forgot-password page par wapas redirect karo” (yeh ensure karega ki agar email address invalid hai, to user wapas forgot password page par chala jaye, jahan se wo apna email address sahi karke dobara try kar sakta hai)

        user = User.query.filter_by(email=email).first() # “Database me User model ke through query karo taaki email ke basis par user ko find karo, aur pehla matching user return karo” (yeh line database me se user ko email address ke basis par search karega, aur agar koi user milta hai to uska record return karega, jisse ki hum uske password ko reset kar sakein)
        if not user: # “Agar user nahi milta hai, to ek flash message show karo jisme user ko account nahi milne ke liye prompt dikhaya jaye” (yeh message user ko inform karega ki unke diye gaye email address ke sath koi account nahi mila, aur unhe apna email address check karne ke liye encourage karega)
            flash('No account found for that email.', 'error') # “Ek flash message show karo jisme user ko account nahi milne ke liye prompt dikhaya jaye” (yeh message user ko inform karega ki uske diye gaye email address ke sath koi account nahi mila)
            return redirect(url_for('forgot_password')) # “User ko forgot-password page par wapas redirect karo” (yeh ensure karega ki agar email address ke sath koi account nahi milta hai, to user wapas forgot password page par chala jaye, jahan se wo apna email address sahi karke dobara try kar sakta hai)

        if not validate_password(password): # “Password valid hai ya nahi check karta hai” (yeh check karega ki user ne jo password enter kiya hai wo valid hai ya nahi, jisse ki hum ensure kar sakein ki user apna password sahi tarike se enter kar raha hai)
            flash('New password must be at least 8 characters long and contain letters, numbers, and a special character.', 'error') # “Agar password valid nahi hai, to ek flash message show karo jisme user ko strong password enter karne ke liye prompt dikhaya jaye” (yeh message user ko inform karega ki unka new password valid nahi hai, aur unhe strong password enter karne ke liye encourage karega)
            return redirect(url_for('forgot_password')) # “User ko forgot-password page par wapas redirect karo” (yeh ensure karega ki agar password invalid hai, to user wapas forgot password page par chala jaye, jahan se wo apna password sahi karke dobara try kar sakta hai)

        if password != confirm_password: # “Agar confirm password new password ke match nahi karta, to ek flash message show karo jisme user ko prompt dikhaya jaye” (yeh message user ko inform karega ki unka confirm password new password ke saath match nahi kar raha)
            flash('Confirm password should match the new password.', 'error') # “Agar confirm password new password ke match nahi karta, to ek flash message show karo jisme user ko prompt dikhaya jaye” (yeh message user ko inform karega ki unka confirm password new password ke saath match nahi kar raha)
            return redirect(url_for('forgot_password')) # “User ko forgot-password page par wapas redirect karo” (yeh ensure karega ki agar confirm password new password ke saath match nahi karta hai, to user wapas forgot password page par chala jaye, jahan se wo apna confirm password sahi karke dobara try kar sakta hai)

        user.password = generate_password_hash(password) # Password ko hash (secure format) me convert karke update kiya
        db.session.commit() # Database session ko commit karo taaki password change database me save ho jaye
        flash('Password updated successfully. Please sign in.', 'success') # “Ek flash message show karo jisme user ko password updated successfully message dikhaya jaye, aur usme user ko sign in karne ke liye encourage kiya jaye” (yeh message user ko inform karega ki unka password successfully update ho gaya hai, aur unhe login karne ke liye encourage karega)
        return redirect(url_for('signin')) # “User ko signin page par redirect karo” (yeh ensure karega ki jab user successfully reset password kar leta hai, to wo login page par chala jaye, jahan se wo apne new credentials enter karke login kar sakta hai)

    return render_template('forgot_password.html') # “Agar request method GET hai, to simply forgot_password.html template ko render karo” (yeh ensure karega ki jab user /forgot-password URL par visit kare, to usse forgot password page dikhai de, jahan se wo apne email address enter karke password reset kar sakta hai)


@app.route('/ask', methods=['POST']) # “Flask me ek route define karo jo /ask URL ke liye trigger hoga, aur usme sirf POST method allow karo” (yeh route user ke questions ko handle karega, jahan users apne questions submit kar sakte hain)
@login_required # “Ask route ko login_required decorator ke through protect karo taaki sirf logged-in users hi is route ko access kar sakein” (yeh ensure karega ki agar koi user /ask URL par access karne ki koshish karta hai aur wo logged in nahi hai, to usse login page par redirect kar diya jayega, jisse ki sirf authenticated users hi apne questions submit kar sakte hain)
def ask(): 
    question = request.form.get('questionInput', '').strip() # “Ask form se questionInput field ki value nikaalo, agar wo field exist nahi karti hai to empty string return karo, aur uske aage-peeche ke spaces ko remove karo” (yeh line ask form se user ke question ko extract karega, aur agar questionInput field form me nahi hai to usse empty string set karega, aur uske aage-peeche ke extra spaces ko remove karega, jisse ki hum question validation me use kar sakein)

    if not question: #Agar user ne kuch likha hi nahi
        flash('Please enter a question.', 'error') # Agar question empty hai, to ek flash message show karo jisme user ko question enter karne ke liye prompt dikhaya jaye (yeh message user ko inform karega ki unhe apna question enter karna hoga, aur agar wo empty question submit karne ki koshish karenge to unhe yeh error message dikhai dega)
        return redirect(url_for('home')) # “User ko home page par redirect karo” (yeh ensure karega ki agar user empty question submit karne ki koshish karta hai, to wo home page par wapas chala jaye, jahan se wo apna question sahi tarike se enter karke dobara submit kar sakta hai)

    flash(f'Your question was: {question}', 'success') #User ka question display karega (confirmation ke liye)
    return redirect(url_for('home')) # Wapas home page pe bhej dega


@app.route('/upload', methods=['POST']) # “Flask me ek route define karo jo /upload URL ke liye trigger hoga, aur usme sirf POST method allow karo” (yeh route file upload functionality ko handle karega, jahan users apni ZIP files upload kar sakte hain)
@login_required # “Upload route ko login_required decorator ke through protect karo taaki sirf logged-in users hi is route ko access kar sakein” (yeh ensure karega ki agar koi user /upload URL par access karne ki koshish karta hai aur wo logged in nahi hai, to usse login page par redirect kar diya jayega, jisse ki sirf authenticated users hi apni files upload kar sakte hain)
def upload_file():
    file = request.files.get('fileInput') # “Upload form se fileInput field ki value nikaalo, jisme user ne jo file select ki hai wo hogi” (yeh line upload form se user ke selected file ko extract karega, jisse ki hum us file ko validate karke save kar sakein)

    if not file or file.filename == '': # “Agar file exist nahi karti hai ya uska filename empty string hai, to iska matlab user ne koi file select nahi ki hai” (yeh check karega ki user ne file select ki hai ya nahi, aur agar wo file select nahi karta hai to usse yeh error message dikhai dega)
        flash('Please select a ZIP file.', 'error') # “Agar user ne file select nahi ki hai, to ek flash message show karo jisme user ko ZIP file select karne ke liye prompt dikhaya jaye” (yeh message user ko inform karega ki unhe apni ZIP file select karni hogi, aur agar wo bina file select kiye upload karne ki koshish karenge to unhe yeh error message dikhai dega)
        return redirect(url_for('home')) # “User ko home page par redirect karo” (yeh ensure karega ki agar user ne file select nahi ki hai, to wo home page par wapas chala jaye, jahan se wo apni file select karke dobara upload kar sakta hai)

    if not allowed_file(file.filename): # “Agar file ka filename allowed_file function ke through validate nahi hota hai, to iska matlab user ne ZIP file ke alawa koi aur file select ki hai” (yeh check karega ki user ne jo file select ki hai wo ZIP file hai ya nahi, aur agar wo ZIP file nahi hai to unhe yeh error message dikhai dega)
        flash('Only ZIP files are allowed.', 'error') # “Ek flash message show karo jisme user ko sirf ZIP files upload karne ke liye prompt dikhaya jaye” (yeh message user ko inform karega ki unhe sirf ZIP files upload karni hogi, aur agar wo bina ZIP file ke upload karne ki koshish karenge to unhe yeh error message dikhai dega)
        return redirect(url_for('home')) # “User ko home page par redirect karo” (yeh ensure karega ki agar user ne allowed file nahi select ki hai, to wo home page par wapas chala jaye, jahan se wo apni correct file select karke dobara upload kar sakta hai)

    saved_name = save_uploaded_zip(file) # “Agar file valid hai, to save_uploaded_zip function ko call karo taaki file server parsave ho jaye, aur uska saved name return ho jaye” (yeh line uploaded file ko save_uploaded_zip function ke through save karega, aur uske saved name ko saved_name variable me store karega, jisse ki hum usse user ko display kar sakein)
    session['last_uploaded_file'] = saved_name # “Session me last_uploaded_file key set karo jisme saved name store hoga, taaki user ke last uploaded file ka naam session me save ho jaye” (yeh line session me last_uploaded_file key set karega, jisme user ke last uploaded file ka naam store hoga, jisse ki hum usse home page par display kar sakein)
    flash(f'File "{saved_name}" uploaded successfully.', 'success') # “Ek flash message show karo jisme user ko file uploaded successfully message dikhaya jaye, aur usme uploaded file ka naam include karo” (yeh message user ko inform karega ki unka file successfully upload ho gaya hai, aur unke uploaded file ke naam ke saath ek confirmation message dikhayega)
    return redirect(url_for('home')) # “User ko home page par redirect karo” (yeh ensure karega ki jab user successfully file upload kar leta hai, to wo home page par chala jaye, jahan se wo apni uploaded file ka naam dekh sakta hai aur apni activities continue kar sakta hai)    


@app.route('/logout') # “Flask me ek route define karo jo /logout URL ke liye trigger hoga, aur usme GET method allow karo” (yeh route user logout functionality ko handle karega, jahan users apne session ko clear karke logout kar sakte hain)
def logout():
    user_name = session.get('user_name') # “Session se user_name key ki value nikaalo, jisme user ka name store hoga, taaki logout ke baad bhi hum user ke naam ko flash message me use kar sakein” (yeh variable user_name me user ke naam ko store karega, jisse ki hum logout confirmation message me user ke naam ko include kar sakein)
    last_uploaded_file = session.get('last_uploaded_file') # “Session se last_uploaded_file key ki value nikaalo, jisme user ke last uploaded file ka naam store hoga, taaki logout ke baad bhi hum us file ke naam ko flash message me use kar sakein” (yeh variable last_uploaded_file me user ke last uploaded file ka naam store karega, jisse ki hum logout confirmation message me us file ke naam ko include kar sakein)
    session.clear()  # “Session ko clear karo taaki user ke login state aur uski related information session se remove ho jaye” (yeh line session ko completely clear kar dega, jisse ki user logout ho jayega, aur uski login state aur related information session se remove ho jayegi)

    if last_uploaded_file: # “Agar last_uploaded_file variable me koi value hai, to usse session me wapas set karo taaki logout ke baad bhi user ke last uploaded file ka naam session me available rahe” (yeh check karega ki last_uploaded_file variable me koi value hai ya nahi, aur agar hai to usse session me wapas set kar dega, jisse ki user logout hone ke baad bhi uske last uploaded file ka naam session me available rahe)
        session['last_uploaded_file'] = last_uploaded_file # “Session me last_uploaded_file key set karo jisme last_uploaded_file variable ki value store hogi, taaki logout ke baad bhi user ke last uploaded file ka naam session me available rahe” (yeh line session me last_uploaded_file key set karega, jisme user ke last uploaded file ka naam store hoga, jisse ki logout hone ke baad bhi uska naam session me available rahe)

    if user_name: # Agar user ka naam available hai:
        flash(f'{user_name}, you have been logged out.', 'success') # “Ek flash message show karo jisme user ko logout message dikhaya jaye, aur usme user ka name include karo” (yeh message user ko inform karega ki unka logout successful hai, aur unke naam ke saath ek personalized logout message dikhayega)
    else: # Agar user ka naam available nahi hai (kisi wajah se session me user_name store nahi hua hai):
        flash('Logged out successfully.', 'success') # “Ek flash message show karo jisme user ko logout successful message dikhaya jaye” (yeh message user ko inform karega ki unka logout successful hai, aur agar user ka naam available nahi hai to ek generic logout message dikhayega)
    return redirect(url_for('home')) # “User ko home page par redirect karo” (yeh ensure karega ki jab user logout ho jata hai, to wo home page par chala jaye, jahan se wo apni activities continue kar sakta hai)


if __name__ == '__main__': # “Python script ke entry point ko define karo taaki jab ye script directly run ki jaye, to usme defined code execute ho” (yeh check karega ki agar ye script directly run ki jaye, to usme defined code execute hoga, aur agar ye script kisi aur module ke through import ki jaye, to is block ke andar ka code execute nahi hoga)
    app.run(debug=True) # Ye Flask server start karta hai, aur debug mode ko enable karta hai taaki development ke dauran errors aur changes ko easily track kiya ja sake.
