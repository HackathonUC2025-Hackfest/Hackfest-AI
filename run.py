# run.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file first
load_dotenv()

# Import the application factory after loading .env
from app import create_app

# Create the app instance; factory determines config from FLASK_ENV
app = create_app()

if __name__ == '__main__':
    # Run the Flask development server
    # Host, port, and debug settings are controlled by environment variables
    # and the configuration object loaded by create_app()
    host = os.environ.get('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_RUN_PORT', 5000))
    # Note: app.run() respects app.config['DEBUG'] which is set based on FLASK_ENV
    app.run(host=host, port=port)