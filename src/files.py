from file_uploader_api import app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.sql import func

db = SQLAlchemy(app)

# fs_mixin = FlaskSerialize(db)

class Files(db.Model, SerializerMixin):

    name = db.Column(db.String(100), nullable=False, max_length=100)
    hash = db.Column(db.String(100), nullable=False, max_length=32, primary_key=True)
    time_upload = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False, auto_now_add=True)
    time_modify = db.Column(db.DateTime(timezone=True), nullable=False,auto_now=True)