"""
app/models/user.py
-------------------
Represents a student account. Holds both login credentials and the profile
fields (GPA, grade level, state, demographics, interests, major) that the
matching engine (app/services/matching.py) uses to score scholarships.

Demographics and interests are stored as PostgreSQL ARRAY columns because a
student can belong to more than one group (e.g. ["first-generation",
"hispanic"]) and have more than one interest (e.g. ["robotics", "music"]).
"""

from datetime import datetime

import bcrypt
from sqlalchemy.dialects.postgresql import ARRAY

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    # Both NULL for a device account (started with one tap, no sign-up):
    # the student is identified by a long-lived token kept on their device.
    email = db.Column(db.String(255), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=True)

    # --- Profile fields used directly by the matching engine ---
    full_name = db.Column(db.String(120), nullable=True)
    gpa = db.Column(db.Float, nullable=True)                # e.g. 3.75 on a 4.0 scale
    grade_level = db.Column(db.String(20), nullable=True)    # "12" (HS senior) or "college_1".."college_5plus"
    state = db.Column(db.String(2), nullable=True)            # USPS abbreviation, e.g. "MD"
    demographics = db.Column(ARRAY(db.String), default=list)  # e.g. ["first-generation"]
    interests = db.Column(ARRAY(db.String), default=list)     # e.g. ["robotics", "art"]
    major = db.Column(db.String(120), nullable=True)          # intended college major
    # Colleges the student attends or is considering. NULL = not answered
    # (nothing hidden); [] = none of the listed ones (every college-only
    # award hidden). Matching hides awards tied to any other college.
    schools = db.Column(ARRAY(db.String), nullable=True)

    # --- Consent records ---
    # When (and to which version of the Terms/Privacy Policy) the student
    # agreed at signup, plus when they separately opted in to sharing
    # demographic data -- that's sensitive (race, disability, LGBTQ+), so it
    # gets its own explicit opt-in instead of riding on the general terms.
    terms_accepted_at = db.Column(db.DateTime, nullable=True)
    terms_version = db.Column(db.String(20), nullable=True)
    demographics_consent_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    interactions = db.relationship(
        "Interaction", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    # --- Password helpers ---
    def set_password(self, raw_password: str) -> None:
        hashed = bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt())
        self.password_hash = hashed.decode("utf-8")

    @property
    def is_device_account(self) -> bool:
        return not self.password_hash

    def check_password(self, raw_password: str) -> bool:
        if not self.password_hash:
            return False
        return bcrypt.checkpw(raw_password.encode("utf-8"), self.password_hash.encode("utf-8"))

    def profile_is_complete(self) -> bool:
        """Used by the frontend to decide whether to show the profile-setup flow."""
        return all([self.gpa, self.grade_level, self.state, self.major])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "is_device_account": self.is_device_account,
            "full_name": self.full_name,
            "gpa": self.gpa,
            "grade_level": self.grade_level,
            "state": self.state,
            "demographics": self.demographics or [],
            "interests": self.interests or [],
            "major": self.major,
            "schools": self.schools,
            "profile_complete": self.profile_is_complete(),
            "demographics_consent": self.demographics_consent_at is not None,
        }
