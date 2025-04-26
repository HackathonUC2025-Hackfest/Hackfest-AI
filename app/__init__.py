# app/__init__.py
import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from .config import config_by_name, validate_config # Import config tools
from marshmallow import ValidationError
import logging

# Extension instances (defined globally)
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

# Basic Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s : %(message)s')

def create_app(config_name=None):
    """Application Factory"""
    app = Flask(__name__)

    # Determine and load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    try:
        config_object = config_by_name[config_name]()
        app.config.from_object(config_object)
        app.logger.info(f"Applied config: '{config_name}'")
    except KeyError:
        app.logger.error(f"Invalid config name: '{config_name}'. Falling back to default.")
        config_object = config_by_name['default']()
        app.config.from_object(config_object)

    # Validate loaded config
    validate_config(config_object)

    # Initialize Flask extensions
    db.init_app(app)
    migrate.init_app(app, db) # Init Flask-Migrate
    jwt.init_app(app)
    CORS(app) # Enable CORS for all origins by default

    # Register Blueprints
    from .api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # Simple health check route
    @app.route('/')
    def health_check():
        return jsonify({"status": "ok"})

    # Global Error Handlers
    @app.errorhandler(ValidationError) # Handle Marshmallow validation errors
    def handle_marshmallow_validation(err):
        app.logger.warning(f"Schema validation failed: {err.messages}")
        from .utils.helpers import api_response # Local import to avoid circularity
        return api_response(data=err.messages, message="Validation failed.", status_code=400, success=False)

    @app.errorhandler(404) # Handle Not Found errors
    def not_found_error(error):
        from .utils.helpers import api_response
        return api_response(message="Resource not found.", status_code=404, success=False)

    @app.errorhandler(500) # Handle generic Internal Server Errors
    def internal_error(error):
         # Ensure session is rolled back on unexpected errors
         db.session.rollback()
         app.logger.error(f"Internal Server Error: {error}", exc_info=True)
         from .utils.helpers import api_response
         return api_response(message="Internal server error.", status_code=500, success=False)

    app.logger.info("Flask app created.")
    return app