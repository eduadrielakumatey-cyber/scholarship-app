"""
app/routes/__init__.py
-------------------------
Exposes a single `register_routes(app)` function that the app factory
calls once. Keeping registration in one place means app/__init__.py
doesn't need to know about every individual blueprint -- it just calls
this function.
"""

from app.routes.auth import auth_bp
from app.routes.profile import profile_bp
from app.routes.scholarships import scholarships_bp
from app.routes.saved import saved_bp
from app.routes.stats import stats_bp
from app.routes.account import account_bp


def register_routes(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(scholarships_bp)
    app.register_blueprint(saved_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(account_bp)
