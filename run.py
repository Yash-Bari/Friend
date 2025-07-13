#!/usr/bin/env python3
"""
Lumi - Your AI Friend

A Flask-based AI companion that helps you stay productive and focused.
"""
import os
from app.factory import create_app

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    # Run the application
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    )
