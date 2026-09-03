"""
app/routes/saved.py

  GET    /api/saved                          -> list saved scholarships
  DELETE /api/saved/<scholarship_id>          -> remove from saved
  PATCH  /api/saved/<scholarship_id>/status   -> update application status
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import Scholarship, Interaction
from app.services.matching import score_saved_list

saved_bp = Blueprint("saved", __name__, url_prefix="/api/saved")

VALID_STATUSES = {"saved", "planning", "in_progress", "submitted", "won", "declined"}


@saved_bp.get("")
@jwt_required()
def list_saved():
    user_id = get_jwt_identity()
    from app.models import User
    user = User.query.get_or_404(user_id)

    saved_interactions = Interaction.query.filter_by(user_id=user.id, action="save").all()
    scholarships = [interaction.scholarship for interaction in saved_interactions]
    status_by_id = {
        interaction.scholarship_id: interaction.app_status or "saved" for interaction in saved_interactions
    }

    results = score_saved_list(user, scholarships)
    for data in results:
        data["app_status"] = status_by_id.get(data["id"], "saved")

    results.sort(key=lambda s: s["deadline"] or "9999-12-31")
    return jsonify({"count": len(results), "results": results})


@saved_bp.delete("/<int:scholarship_id>")
@jwt_required()
def unsave(scholarship_id):
    user_id = get_jwt_identity()
    interaction = Interaction.query.filter_by(
        user_id=user_id, scholarship_id=scholarship_id, action="save"
    ).first_or_404()
    db.session.delete(interaction)
    db.session.commit()
    return jsonify({"deleted": True}), 200


@saved_bp.patch("/<int:scholarship_id>/status")
@jwt_required()
def update_status(scholarship_id):
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    status = data.get("status")

    if status not in VALID_STATUSES:
        return jsonify({"error": f"status must be one of {sorted(VALID_STATUSES)}"}), 400

    interaction = Interaction.query.filter_by(
        user_id=user_id, scholarship_id=scholarship_id, action="save"
    ).first_or_404()

    interaction.app_status = status
    db.session.commit()
    return jsonify({"scholarship_id": scholarship_id, "app_status": status}), 200
