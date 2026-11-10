"""
app/routes/account.py
------------------------
Self-service privacy controls, so honoring a data request never depends on
someone emailing support (GDPR/CCPA access + deletion rights).

  GET    /api/account/export -> everything we store about the current user, as JSON
  DELETE /api/account        -> permanently delete the account and its swipe/saved history
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import Answer, Application, Essay, User

account_bp = Blueprint("account", __name__, url_prefix="/api/account")


def _iso(value):
    return value.isoformat() if value else None


@account_bp.get("/export")
@jwt_required()
def export_data():
    user = User.query.get_or_404(get_jwt_identity())
    return jsonify({
        "account": {
            "email": user.email,
            "created_at": _iso(user.created_at),
            "updated_at": _iso(user.updated_at),
            "terms_accepted_at": _iso(user.terms_accepted_at),
            "terms_version": user.terms_version,
            "demographics_consent_at": _iso(user.demographics_consent_at),
        },
        "profile": {
            "full_name": user.full_name,
            "gpa": user.gpa,
            "grade_level": user.grade_level,
            "state": user.state,
            "major": user.major,
            "demographics": user.demographics or [],
            "interests": user.interests or [],
        },
        "interactions": [
            {
                **interaction.to_dict(),
                "scholarship_title": interaction.scholarship.title if interaction.scholarship else None,
            }
            for interaction in user.interactions
        ],
        "essays": [e.to_dict() for e in Essay.query.filter_by(user_id=user.id)],
        "answers": [
            {"scholarship_id": a.scholarship_id, "question_key": a.question_key, "answer": a.body}
            for a in Answer.query.filter_by(user_id=user.id)
        ],
        "applications": [
            {**a.to_dict(), "scholarship_title": a.scholarship.title if a.scholarship else None}
            for a in Application.query.filter_by(user_id=user.id)
        ],
    })


@account_bp.delete("")
@jwt_required()
def delete_account():
    user = User.query.get_or_404(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    # Re-asking for the password means a stolen/forgotten-open session
    # can't wipe someone's account with a single request. A device account
    # has no password, so it confirms with an explicit {"confirm": true}.
    if user.is_device_account:
        if data.get("confirm") is not True:
            return jsonify({"error": "confirm is required to delete this profile"}), 400
    elif not user.check_password(data.get("password") or ""):
        return jsonify({"error": "incorrect password"}), 403

    # Interactions go with it via the relationship's delete-orphan cascade.
    db.session.delete(user)
    db.session.commit()
    return "", 204
