"""
app/routes/apply.py
----------------------
Applying from inside ScholarMatch.

Essay library (reused across applications):
  GET    /api/essays              -> my essays
  POST   /api/essays              -> new essay {title, body}
  PUT    /api/essays/<id>         -> update {title?, body?}
  DELETE /api/essays/<id>         -> delete

Scholarships posted on ScholarMatch (hosted) are applied to right here:
  POST   /api/scholarships/<id>/apply        -> submit {full_name, email, school?, essay?, share_consent}
  GET    /api/scholarships/<id>/application  -> my application, if any
  DELETE /api/scholarships/<id>/application  -> withdraw before the deadline

Outside scholarships are submitted on the provider's site; this records it:
  POST   /api/scholarships/<id>/submitted    -> save it to my list as Submitted
"""

from datetime import date, datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import Application, Essay, Interaction, Scholarship, User
from app.services.hosted import validate_application
from app.services.scoring import is_eligible
from app.utils.validators import normalize_interests

apply_bp = Blueprint("apply", __name__, url_prefix="/api")

MAX_ESSAYS = 50
MAX_ESSAY_BODY = 20_000


def _me():
    return User.query.get_or_404(get_jwt_identity())


def _mark(user, scholarship_id, status):
    """Puts the scholarship on the student's Saved list with this status."""
    interaction = Interaction.query.filter_by(user_id=user.id, scholarship_id=scholarship_id).first()
    if interaction is None:
        interaction = Interaction(user_id=user.id, scholarship_id=scholarship_id, action="save")
        interaction.interest_snapshot = normalize_interests(user.interests)
        db.session.add(interaction)
    interaction.action = "save"
    interaction.app_status = status
    return interaction


# --- Essay library -----------------------------------------------------------

@apply_bp.get("/essays")
@jwt_required()
def list_essays():
    user = _me()
    essays = Essay.query.filter_by(user_id=user.id).order_by(Essay.updated_at.desc()).all()
    return jsonify({"results": [e.to_dict() for e in essays]})


def _essay_fields(data, essay=None):
    title = data.get("title", essay.title if essay else None)
    body = data.get("body", essay.body if essay else "")
    title = str(title or "").strip() or "Untitled essay"
    body = str(body or "")
    if len(title) > 160:
        return None, "Title is too long"
    if len(body) > MAX_ESSAY_BODY:
        return None, "Essay is too long"
    return (title, body), None


@apply_bp.post("/essays")
@jwt_required()
def create_essay():
    user = _me()
    if Essay.query.filter_by(user_id=user.id).count() >= MAX_ESSAYS:
        return jsonify({"error": f"You can keep up to {MAX_ESSAYS} essays. Delete one first."}), 400
    fields, err = _essay_fields(request.get_json(silent=True) or {})
    if err:
        return jsonify({"error": err}), 400
    essay = Essay(user_id=user.id, title=fields[0], body=fields[1])
    db.session.add(essay)
    db.session.commit()
    return jsonify(essay.to_dict()), 201


@apply_bp.put("/essays/<int:essay_id>")
@jwt_required()
def update_essay(essay_id):
    user = _me()
    essay = Essay.query.filter_by(id=essay_id, user_id=user.id).first_or_404()
    fields, err = _essay_fields(request.get_json(silent=True) or {}, essay)
    if err:
        return jsonify({"error": err}), 400
    essay.title, essay.body = fields
    db.session.commit()
    return jsonify(essay.to_dict())


@apply_bp.delete("/essays/<int:essay_id>")
@jwt_required()
def delete_essay(essay_id):
    user = _me()
    essay = Essay.query.filter_by(id=essay_id, user_id=user.id).first_or_404()
    db.session.delete(essay)
    db.session.commit()
    return "", 204


# --- In-app applications (hosted scholarships) ----------------------------------

@apply_bp.post("/scholarships/<int:scholarship_id>/apply")
@jwt_required()
def apply(scholarship_id):
    user = _me()
    scholarship = Scholarship.query.get_or_404(scholarship_id)
    if Application.query.filter_by(user_id=user.id, scholarship_id=scholarship_id).first():
        return jsonify({"error": "You already applied to this scholarship"}), 409

    fields, errors = validate_application(request.get_json(silent=True) or {}, scholarship)
    if errors:
        return jsonify({"error": errors[0], "errors": errors}), 400
    eligible, reasons = is_eligible(user, scholarship)
    if not eligible:
        return jsonify({"error": "Your profile doesn't meet this scholarship's requirements", "reasons": reasons}), 403

    application = Application(
        user_id=user.id, scholarship_id=scholarship_id, consented_at=datetime.utcnow(), **fields
    )
    db.session.add(application)
    _mark(user, scholarship_id, "submitted")
    db.session.commit()
    return jsonify(application.to_dict()), 201


@apply_bp.get("/scholarships/<int:scholarship_id>/application")
@jwt_required()
def my_application(scholarship_id):
    user = _me()
    application = Application.query.filter_by(user_id=user.id, scholarship_id=scholarship_id).first_or_404()
    return jsonify(application.to_dict())


@apply_bp.delete("/scholarships/<int:scholarship_id>/application")
@jwt_required()
def withdraw(scholarship_id):
    user = _me()
    application = Application.query.filter_by(user_id=user.id, scholarship_id=scholarship_id).first_or_404()
    scholarship = application.scholarship
    if application.status != "submitted" or (scholarship.deadline and scholarship.deadline < date.today()):
        return jsonify({"error": "This application can no longer be withdrawn"}), 400
    db.session.delete(application)
    _mark(user, scholarship_id, "saved")
    db.session.commit()
    return "", 204


# --- Outside scholarships ----------------------------------------------------------

@apply_bp.post("/scholarships/<int:scholarship_id>/submitted")
@jwt_required()
def mark_submitted(scholarship_id):
    user = _me()
    Scholarship.query.get_or_404(scholarship_id)
    interaction = _mark(user, scholarship_id, "submitted")
    db.session.commit()
    return jsonify(interaction.to_dict())
