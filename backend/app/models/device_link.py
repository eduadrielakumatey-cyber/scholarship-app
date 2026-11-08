"""
app/models/device_link.py
----------------------------
A one-time code for opening an existing profile on another device. See
app/services/device_link.py for how codes are made and checked.
"""

from datetime import datetime

from app.extensions import db


class DeviceLink(db.Model):
    __tablename__ = "device_links"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
