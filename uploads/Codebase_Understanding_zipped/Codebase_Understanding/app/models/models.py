from app import db
from datetime import datetime

class File(db.Model):
    __tablename__ = 'file'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(1024), nullable=False)
    filetype = db.Column(db.String(50))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    chunks = db.relationship('Chunk', backref='file', lazy=True, cascade="all, delete-orphan")

class Chunk(db.Model):
    __tablename__ = 'chunk'
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=False)
    chunk_text = db.Column(db.Text, nullable=False)
    chunk_index = db.Column(db.Integer)
    # We might store the embedding here if we wanted, but usually vector DB handles it.
    # We'll store a reference or just use the ID mapping.
    
class Dependency(db.Model):
    __tablename__ = 'dependency'
    id = db.Column(db.Integer, primary_key=True)
    parent_file = db.Column(db.String(1024), nullable=False)
    child_file = db.Column(db.String(1024), nullable=False)
