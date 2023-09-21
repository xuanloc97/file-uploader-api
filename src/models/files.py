"""
Define model for DB
"""
from file_uploader_api import app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

db = SQLAlchemy(app)

class Files(db.Model):

    name = db.Column(db.String(100), nullable=False, primary_key=True)
    hash = db.Column(db.String(32), nullable=False)
    time_upload = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    time_modify = db.Column(db.DateTime(timezone=True), nullable=True)
