"""Small, reusable authentication operations for session-based accounts."""

from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.models.models import User


class AuthService:
    MINIMUM_PASSWORD_LENGTH = 6

    @staticmethod
    def authenticate(email, password):
        normalized_email = (email or "").strip().lower()
        if not normalized_email or not password:
            return None, "Please enter both email and password."

        user = User.query.filter_by(email=normalized_email).first()
        if not user or not check_password_hash(user.password, password):
            return None, "Invalid email or password."
        return user, None

    @classmethod
    def register(cls, fullname, email, password, confirm_password):
        fullname = (fullname or "").strip()
        email = (email or "").strip().lower()
        if not fullname or not email or not password:
            return None, "Please fill in all required fields."
        if password != confirm_password:
            return None, "Passwords do not match."
        if len(password) < cls.MINIMUM_PASSWORD_LENGTH:
            return None, f"Password must be at least {cls.MINIMUM_PASSWORD_LENGTH} characters."
        if User.query.filter_by(email=email).first():
            return None, "An account already exists for this email. Please sign in instead."

        user = User(fullname=fullname, email=email, password=generate_password_hash(password))
        try:
            db.session.add(user)
            db.session.commit()
            return user, None
        except Exception:
            db.session.rollback()
            return None, "We could not create your account. Please try again."
