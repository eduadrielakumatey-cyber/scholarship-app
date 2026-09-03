"""
app/__init__.py
------------------
The application factory. Rather than creating a single global `app = Flask(__name__)`
at import time, we build it inside a function (`create_app`). This is the
standard Flask pattern because:

  - Tests can call create_app("testing") to get a fresh app wired to an
    in-memory SQLite DB, without affecting the dev/prod app.
  - Extensions (db, jwt, cors, migrate) are defined once in extensions.py
    and bound to whichever app instance is being built.

run.py (at the project root) is the thin script that actually calls this
factory and starts the dev server.
"""

from flask import Flask, jsonify

from config import config_by_name
from app.extensions import db, migrate, jwt, cors

from flask_cors import CORS


def create_app(env_name: str = "development") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_by_name[env_name])

    # --- Bind extensions to this app instance ---
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    # Import models so Flask-Migrate can see them (see app/models/__init__.py
    # docstring for why this import matters even though nothing here uses it
    # directly).
    from app import models  # noqa: F401

    from app.routes import register_routes
    register_routes(app)

    @app.get("/api/health")
    def health():
        """Simple uptime check used by Docker healthchecks / load balancers."""
        return jsonify({"status": "ok"})

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify({"error": "not found"}), 404

    @app.errorhandler(500)
    def server_error(_e):
        return jsonify({"error": "internal server error"}), 500

    return app
