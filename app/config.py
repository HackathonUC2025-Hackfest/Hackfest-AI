# app/config.py
import os
from dotenv import load_dotenv
import logging

# Logger setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s : %(message)s')
logger = logging.getLogger(__name__)

# .env loading
basedir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(basedir, '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    logger.info("Loaded .env file.")
else:
    logger.warning(".env file not found.")

class Config:
    """Base Config Class"""
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-flask-secret-key')
    DEBUG = False
    TESTING = False
    # JWT settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'default-jwt-secret-key')
    # Gemini settings
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    GEMINI_MODEL_NAME = os.environ.get('GEMINI_MODEL_NAME', 'gemini-2.0-flash-exp')
    GEMINI_API_VERSION = os.environ.get('GEMINI_API_VERSION', None)
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        logger.info("Constructing DB URI from components.")
        db_user = os.environ.get('POSTGRES_USER', 'default_user')
        db_pass = os.environ.get('POSTGRES_PASSWORD', 'default_password')
        db_host = os.environ.get('DB_HOST', 'db')
        db_port = os.environ.get('DB_PORT', '5432')
        db_name = os.environ.get('POSTGRES_DB', 'default_db')
        SQLALCHEMY_DATABASE_URI = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False # Disable SQL query logging by default

class DevelopmentConfig(Config):
    """Development Config"""
    DEBUG = os.environ.get('FLASK_DEBUG', '1') == '1'
    SQLALCHEMY_ECHO = True # Enable SQL query logging in dev

class ProductionConfig(Config):
    """Production Config"""
    DEBUG = False
    SQLALCHEMY_ECHO = False

class TestingConfig(Config):
    """Testing Config"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL', 'sqlite:///:memory:') # Default to in-memory SQLite
    SQLALCHEMY_ECHO = False
    JWT_SECRET_KEY = 'test-jwt-secret'
    GEMINI_API_KEY='test-key-for-testing' # Use placeholder key for tests

# Config mapping by environment name
config_by_name = dict(
    dev=DevelopmentConfig,
    test=TestingConfig,
    prod=ProductionConfig,
    default=DevelopmentConfig
)

# Configuration Validation Function
def validate_config(config_instance):
    """Validate loaded configuration settings."""
    # Skip external checks in testing
    if isinstance(config_instance, TestingConfig):
         logger.info("--- Skipping external API validation in TestingConfig ---")
         return

    logger.info(f"--- Validating Config: {type(config_instance).__name__} ---")
    # Check critical settings
    if not config_instance.GEMINI_API_KEY: logger.critical("CRITICAL: GEMINI_API_KEY missing.")
    if not config_instance.SQLALCHEMY_DATABASE_URI: logger.critical("CRITICAL: SQLALCHEMY_DATABASE_URI missing.")
    # Check default secrets
    if config_instance.SECRET_KEY == 'default-flask-secret-key': logger.warning("WARNING: Using default Flask SECRET_KEY.")
    if config_instance.JWT_SECRET_KEY == 'default-jwt-secret-key': logger.warning("WARNING: Using default JWT_SECRET_KEY.")
    # Log informational settings
    logger.info(f"Debug Mode: {config_instance.DEBUG}")
    logger.info(f"Gemini Model: {config_instance.GEMINI_MODEL_NAME}")
    if config_instance.GEMINI_API_VERSION: logger.info(f"Gemini API Version: {config_instance.GEMINI_API_VERSION}")
    logger.info(f"SQLAlchemy Echo: {config_instance.SQLALCHEMY_ECHO}")
    logger.info("--- Validation Complete ---")