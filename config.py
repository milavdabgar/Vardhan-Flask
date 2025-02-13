import os
from datetime import timedelta
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'vardhan_insys.db')

class DevelopmentConfig(Config):
    FLASK_ENV = 'development'
    DEBUG = True

class ProductionConfig(Config):
    FLASK_ENV = 'production'
    DEBUG = False

# Set the configuration based on environment
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
