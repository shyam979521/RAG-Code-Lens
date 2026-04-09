from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    from app.routes.routes import main_bp
    app.register_blueprint(main_bp)
    with app.app_context():
        from app.models import models
        db.create_all()
    return app