from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import config
import os

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # Get config based on environment
    config_name = os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.amc import bp as amc_bp
    app.register_blueprint(amc_bp, url_prefix='/amc')

    from app.service_requests import bp as service_requests_bp
    app.register_blueprint(service_requests_bp)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp, url_prefix='')

    # Initialize scheduler
    from app.tasks import init_scheduler
    init_scheduler(app)
    
    return app

from app import models

__all__ = ['create_app', 'db', 'login_manager', 'migrate']
