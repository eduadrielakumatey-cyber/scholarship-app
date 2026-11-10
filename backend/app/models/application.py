"""
app/models/application.py
----------------------------
An application submitted inside ScholarMatch to a scholarship a sponsor
posted here (Scholarship.hosted). Outside scholarships are applied to on
the provider's own site; this table only holds in-app ones.

The student's name and email are collected only here, only with their
explicit consent, and are shown only to that scholarship's sponsor (via the
sponsor's private review link) so the sponsor can contact a winner.
"""

from datetime import datetime

from app.extensions import db

APPLICATION_STATUSES = ("submitted", "winner", "not_selected")


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    scholarship_id = db.Column(
        db.Integer, db.ForeignKey("scholarships.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    school = db.Column(db.String(160), nullable=True)
    essay = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="submitted")
    consented_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    scholarship = db.relationship("Scholarship")

    __table_args__ = (
        db.UniqueConstraint("scholarship_id", "user_id", name="uq_application_user_scholarship"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "scholarship_id": self.scholarship_id,
            "full_name": self.full_name,
            "email": self.email,
            "school": self.school,
            "essay": self.essay,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
