import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# from flask_login import LoginManager

db = SQLAlchemy()
DB_NAME = "database.db"

basedir = os.path.abspath(os.path.dirname(__file__))

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'ksdbhbehbwibdiaofen'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or f'sqlite:///{os.path.join(basedir, DB_NAME)}'
    db.init_app(app)

    from .file_uploader_api import file_uploader_api
    from .user_api import user_api

    app.register_blueprint(file_uploader_api, url_prefix='/')
    app.register_blueprint(user_api, url_prefix='/')

    with app.app_context():
        db.create_all()

    # login_manager = LoginManager()
    # login_manager.login_view = 'auth.login'
    # login_manager.init_app(app)

    # @login_manager.user_loader
    # def load_user(id):
    #     return User.query.get(int(id))

    return app


def create_database(app):
    if not os.path.exists('website/' + DB_NAME):
        db.create_all(app=app)
        print('Created Database!')