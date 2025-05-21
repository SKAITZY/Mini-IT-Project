from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def init_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)