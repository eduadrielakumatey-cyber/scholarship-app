"""
app/extensions.py
------------------
Flask extensions (SQLAlchemy, Migrate, JWT, CORS) are instantiated here,
*without* an app attached yet. They get bound to the real Flask app inside
the app factory (`create_app` in app/__init__.py) via `.init_app(app)`.

Why this pattern? It avoids circular imports: models need `db`, routes need
`jwt`, and the app factory needs all of them. If we created these objects
directly inside __init__.py, every module that needed `db` would have to
import from __init__.py, which imports them back -> circular import errors.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
