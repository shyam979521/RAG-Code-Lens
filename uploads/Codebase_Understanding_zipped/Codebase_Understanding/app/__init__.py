from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    import sys
    print("--- Initializing Flask App...")
    app = Flask(__name__)
    app.config.from_object(Config)
    
    print("--- Initializing Database...")
    db.init_app(app)
    
    # Import routes here to avoid circular dependency
    from app.routes.routes import main_bp
    app.register_blueprint(main_bp)
    
    with app.app_context():
        # Import models so they are registered with SQLAlchemy
        print("--- Creating DB tables (if not exist)...")
        from app.models import models
        db.create_all()
        print("--- Database logic verified.")
        sys.stdout.flush()
        
    return app
