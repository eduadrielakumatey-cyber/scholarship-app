"""
app/routes/profile.py
------------------------
Lets a logged-in student fill in / update the data the matching engine
needs: GPA, grade level, state, demographics, interests, major.

  GET  /api/profile    -> current profile
  PUT  /api/profile     -> update one or more profile fields
"""

from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import User
from app.utils.validators import is_valid_grade_level, is_valid_state, normalize_interests

profile_bp = Blueprint("profile", __name__, url_prefix="/api/profile")

# Only these fields can be mass-updated from the request body. Whitelisting
# protects against someone trying to PUT {"id": 999} and hijacking a
# different row, or PUT {"password_hash": "..."} to bypass the auth flow.
#
# full_name is deliberately not here: the matcher never uses it, so we
# don't collect it (data minimization).
ALLOWED_FIELDS = {
    "gpa",
    "grade_level",
    "state",
    "demographics",
    "interests",
    "major",
}


@profile_bp.get("")
@jwt_required()
def get_profile():
    user = User.query.get_or_404(get_jwt_identity())
    return jsonify(user.to_dict())


@profile_bp.put("")
@jwt_required()
def update_profile():
    user = User.query.get_or_404(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    if "grade_level" in data and data["grade_level"] is not None and not is_valid_grade_level(data["grade_level"]):
        return jsonify({
            "error": "grade_level must be one of: 12, college_1, college_2, college_3, college_4, college_5plus"
        }), 400

    if "state" in data and data["state"] and not is_valid_state(data["state"]):
        return jsonify({"error": "state must be a valid two-letter US state code"}), 400

    # Demographics are sensitive, so they're only stored with an explicit
    # opt-in. Withdrawing consent erases whatever was saved.
    if "demographics_consent" in data:
        if data["demographics_consent"] is True:
            if user.demographics_consent_at is None:
                user.demographics_consent_at = datetime.utcnow()
        else:
            user.demographics_consent_at = None
            user.demographics = []
    if data.get("demographics") and user.demographics_consent_at is None:
        return jsonify({"error": "please confirm you agree to share demographic information"}), 400

    for field in ALLOWED_FIELDS:
        if field == "demographics" and user.demographics_consent_at is None:
            continue
        if field in data:
            setattr(user, field, data[field])

    # Normalize after the generic assignment above so the whitelisted/typed
    # value always wins over this cleanup, never the other way around.
    if "interests" in data:
        user.interests = normalize_interests(data["interests"])

    if "gpa" in data and data["gpa"] is not None:
        try:
            gpa = float(data["gpa"])
        except (TypeError, ValueError):
            return jsonify({"error": "gpa must be a number"}), 400
        if not (0.0 <= gpa <= 5.0):
            return jsonify({"error": "gpa must be between 0.0 and 5.0"}), 400
        user.gpa = gpa

    if "state" in data and data["state"]:
        user.state = data["state"].strip().upper()[:2]

    db.session.commit()
    return jsonify(user.to_dict())
