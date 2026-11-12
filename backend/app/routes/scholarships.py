"""
app/routes/scholarships.py
-----------------------------
Read-only scholarship browsing, scored per-user.

  GET /api/scholarships/deck          -> next batch of swipe cards (scored, ranked)
  GET /api/scholarships/schools       -> colleges with their own awards (profile picker)
  GET /api/scholarships/<id>           -> single scholarship, scored for this user
  POST /api/scholarships/<id>/swipe     -> record a like/pass/save action
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import User, Scholarship, Interaction
from app.services.matching import get_swipe_deck_with_summary, school_options, score_single
from app.services.scoring import is_eligible
from app.utils.validators import normalize_interests

scholarships_bp = Blueprint("scholarships", __name__, url_prefix="/api/scholarships")

VALID_ACTIONS = {"like", "pass", "save"}


@scholarships_bp.get("/deck")
@jwt_required()
def deck():
    user = User.query.get_or_404(get_jwt_identity())
    if not user.profile_is_complete():
        return (
            jsonify({"error": "complete your profile before browsing scholarships"}),
            400,
        )
    limit = request.args.get("limit", default=25, type=int)
    cards, filtered = get_swipe_deck_with_summary(user, limit=limit)
    return jsonify({"count": len(cards), "results": cards, "filtered": filtered})


@scholarships_bp.get("/schools")
def schools():
    # Public: the start screen shows the picker before a profile exists.
    return jsonify(school_options())


@scholarships_bp.get("/<int:scholarship_id>")
@jwt_required()
def detail(scholarship_id):
    user = User.query.get_or_404(get_jwt_identity())
    scholarship = Scholarship.query.get_or_404(scholarship_id)
    payload = score_single(user, scholarship)
    # The Apply page shows why a student doesn't qualify and whether they
    # already marked it submitted.
    eligible, reasons = is_eligible(user, scholarship)
    payload["ineligible_reasons"] = [] if eligible else reasons
    interaction = Interaction.query.filter_by(user_id=user.id, scholarship_id=scholarship_id).first()
    payload["app_status"] = (interaction.app_status or "saved") if interaction and interaction.action == "save" else None
    return jsonify(payload)


@scholarships_bp.post("/<int:scholarship_id>/swipe")
@jwt_required()
def swipe(scholarship_id):
    user = User.query.get_or_404(get_jwt_identity())
    Scholarship.query.get_or_404(scholarship_id)  # 404s if the scholarship doesn't exist

    data = request.get_json(silent=True) or {}
    action = data.get("action")
    if action not in VALID_ACTIONS:
        return jsonify({"error": f"action must be one of {sorted(VALID_ACTIONS)}"}), 400

    interaction = Interaction.query.filter_by(
        user_id=user.id, scholarship_id=scholarship_id
    ).first()
    if interaction:
        # Upsert: the user can change their mind (e.g. "like" -> "save")
        interaction.action = action
    else:
        interaction = Interaction(
            user_id=user.id, scholarship_id=scholarship_id, action=action
        )
        db.session.add(interaction)

    # Snapshot the user's interests at the moment of a "pass" -- this is
    # the baseline app/services/matching.py compares against later to
    # decide whether a newly-added interest makes the skip stale enough
    # to reconsider. Only meaningful for "pass" (see matching._reentry_ids),
    # but harmless to record on any action for consistency.
    interaction.interest_snapshot = normalize_interests(user.interests)

    db.session.commit()
    return jsonify(interaction.to_dict()), 200
