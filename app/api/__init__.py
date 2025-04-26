# app/api/__init__.py
from flask import Blueprint

# API Blueprint
api_bp = Blueprint('api', __name__)

# Import routes
from . import routes