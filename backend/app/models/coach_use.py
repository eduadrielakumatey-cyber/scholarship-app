"""
app/models/coach_use.py
--------------------------
One row per AI feedback request, so each student's daily limit can be
enforced (and cost tracked). Stores no essay text.
"""

from datetime import datetime

from app.extensions import db


class CoachUse(db.Model):
    __tablename__ = "coach_uses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
