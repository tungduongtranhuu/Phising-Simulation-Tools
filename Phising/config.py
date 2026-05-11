"""
Configuration file for Phishing Simulator Application
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory of the application
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Flask Configuration
class Config:
    """Base configuration"""
    
    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration
    DATABASE_PATH = os.path.join(BASE_DIR, 'data', 'phishing.db')
    
    # Session configuration
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Application settings
    DEBUG = False
    TESTING = False
    
    # Email settings (for future email sending functionality)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@phishing-sim.com')
    
    # Logging configuration
    LOG_FILE = os.path.join(BASE_DIR, 'logs', 'app.log')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Application URLs
    APP_URL = os.environ.get('APP_URL', 'http://localhost:5000')
    TRACKING_URL_BASE = f"{APP_URL}/track"
    
    # Pagination
    CAMPAIGNS_PER_PAGE = 20
    EVENTS_PER_PAGE = 50
    
    # Security settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file upload
    
    # Campaign settings
    DEFAULT_CAMPAIGN_STATUS = 'active'
    ALLOWED_CAMPAIGN_STATUSES = ['active', 'inactive', 'paused', 'completed']
    
    # Event types
    ALLOWED_EVENT_TYPES = ['clicked', 'opened', 'submitted', 'reported']


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    DATABASE_PATH = ':memory:'  # Use in-memory database for tests


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """Get configuration based on environment"""
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
