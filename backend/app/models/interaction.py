"""
app/models/interaction.py
"""

from datetime import datetime
from app.extensions import db


class Interaction(db.Model):
    __tablename__ = "interactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    scholarship_id = db.Column(
        db.Integer, db.ForeignKey("scholarships.id"), nullable=False, index=True
    )
    action = db.Column(db.String(10), nullable=False)

    # Application tracker status. Only meaningful when action == "save".
    # NULL is treated as "saved" in the UI.
    # Values: saved | planning | in_progress | submitted | won | declined
    app_status = db.Column(db.String(20), nullable=True, default="saved")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    scholarship = db.relationship("Scholarship")

    __table_args__ = (
        db.UniqueConstraint("user_id", "scholarship_id", name="uq_user_scholarship"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "scholarship_id": self.scholarship_id,
            "action": self.action,
            "app_status": self.app_status or "saved",
            "created_at": self.created_at.isoformat(),
        }
