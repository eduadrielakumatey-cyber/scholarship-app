"""
app/models/__init__.py
------------------------
Re-exports model classes so other modules can write
`from app.models import User, Scholarship, Interaction`
instead of reaching into each submodule individually. Flask-Migrate also
needs every model imported somewhere before `flask db migrate` runs, or it
won't detect their tables -- importing them here, and importing this package
from app/__init__.py, guarantees that happens.
"""

from app.models.user import User
from app.models.scholarship import Scholarship
from app.models.interaction import Interaction
from app.models.device_link import DeviceLink

__all__ = ["User", "Scholarship", "Interaction", "DeviceLink"]
