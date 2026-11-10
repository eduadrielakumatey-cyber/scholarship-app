"""
app/models/essay.py
----------------------
A student's saved essays. Most scholarships ask variations of the same few
questions (goals, leadership, a challenge you overcame), so essays are kept
in one library and reused across applications instead of being tied to a
single scholarship.
"""

from datetime import datetime

from app.extensions import db


class Essay(db.Model):
    __tablename__ = "essays"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title = db.Column(db.String(160), nullable=False)
    body = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        words = len(self.body.split()) if self.body else 0
        return {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "word_count": words,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
