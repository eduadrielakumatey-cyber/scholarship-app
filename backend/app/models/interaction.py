"""
app/models/interaction.py
"""

from datetime import datetime

from sqlalchemy.dialects.postgresql import ARRAY

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

    # The user's normalized interests at the moment this interaction was
    # recorded. Only actually consulted for action == "pass" -- it's how
    # app/services/matching.py decides whether a scholarship a user
    # skipped is allowed to re-enter their swipe deck later: if their
    # CURRENT interests contain a tag that wasn't here at pass-time, and
    # that tag is one this scholarship lists, the pass no longer reflects
    # an up-to-date judgment and the scholarship gets another look. See
    # matching.py:_reentry_ids for the full rule and why it's designed
    # this way (bounded, no repeat spam, never re-shows unrelated passes).
    interest_snapshot = db.Column(ARRAY(db.String), nullable=True)

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
