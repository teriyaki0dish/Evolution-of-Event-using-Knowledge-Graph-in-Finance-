"""
Main entry point for the Financial Risk Knowledge Graph application.
This script runs the Flask web server.
"""
from app import app
from config import FLASK_CONFIG

if __name__ == "__main__":
    # Use localhost (127.0.0.1) instead of 0.0.0.0 to avoid permissions issues
    # Use port 8080 instead of 5000
    app.run(
        host="127.0.0.1",  # Changed from FLASK_CONFIG["host"]
        port=8080,         # Changed from FLASK_CONFIG["port"]
        debug=FLASK_CONFIG["debug"]
    )
