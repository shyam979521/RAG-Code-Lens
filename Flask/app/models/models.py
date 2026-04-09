from app import db
from datetime import datetime

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(1024), nullable=False)
    filetype = db.Column(db.String(50))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    chunks = db.relationship('Chunk', backref='file', lazy=True, cascade="all, deleteorphan")
class Chunk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=False)
    chunk_text = db.Column(db.Text, nullable=False)
    chunk_index = db.Column(db.Integer)
class Dependency(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parent_file = db.Column(db.String(1024), nullable=False)
    child_file = db.Column(db.String(1024), nullable=False)
