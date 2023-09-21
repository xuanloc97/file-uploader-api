"""
Define model for DB
"""
from sqlalchemy.sql import func
from sqlalchemy_serializer import SerializerMixin
from . import db

class Files(db.Model, SerializerMixin):
    """Files Model"""
    name = db.Column(db.String(100), nullable=False, primary_key=True)
    hash = db.Column(db.String(32), nullable=False)
    time_upload = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    time_modify = db.Column(db.DateTime(timezone=True), nullable=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    public_id = db.Column(db.String(50), unique = True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(70), unique = True)
    password = db.Column(db.String(80))
