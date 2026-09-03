"""
run.py
--------
The script you actually execute to start the backend locally:

    python run.py

For production, don't use this -- use gunicorn instead (see Dockerfile /
README), since Flask's built-in server isn't designed to handle real
traffic.
"""

import os

from app import create_app

app = create_app(os.environ.get("FLASK_ENV", "development"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app.config.get("DEBUG", False))
