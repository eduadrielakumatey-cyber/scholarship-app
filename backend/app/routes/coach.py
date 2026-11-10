"""
app/routes/coach.py
----------------------
AI essay feedback (see app/services/coach.py).

  GET  /api/coach/status    -> {enabled, remaining_today, daily_limit}
  POST /api/coach/feedback  -> {text, question?, word_limit?, scholarship_id?}
                               => {feedback, remaining_today}
"""

from datetime import datetime, timedelta

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import CoachUse, Scholarship, User
from app.services.coach import CoachError, get_feedback

coach_bp = Blueprint("coach", __name__, url_prefix="/api/coach")


def _remaining(user_id) -> int:
    limit = current_app.config["COACH_DAILY_LIMIT"]
    since = datetime.utcnow() - timedelta(days=1)
    used = CoachUse.query.filter(CoachUse.user_id == user_id, CoachUse.created_at >= since).count()
    return max(0, limit - used)


def _enabled() -> bool:
    return bool(current_app.config.get("ANTHROPIC_API_KEY"))


@coach_bp.get("/status")
@jwt_required()
def status():
    user = User.query.get_or_404(get_jwt_identity())
    return jsonify({
        "enabled": _enabled(),
        "remaining_today": _remaining(user.id) if _enabled() else 0,
        "daily_limit": current_app.config["COACH_DAILY_LIMIT"],
    })


@coach_bp.post("/feedback")
@jwt_required()
def feedback():
    user = User.query.get_or_404(get_jwt_identity())
    if not _enabled():
        return jsonify({"error": "AI feedback isn't turned on yet."}), 503
    if _remaining(user.id) <= 0:
        return jsonify({"error": "You've used today's AI feedback. It resets 24 hours after your first request."}), 429

    data = request.get_json(silent=True) or {}
    text = str(data.get("text") or "")
    question = str(data.get("question") or "")[:2000] or None
    limit = data.get("word_limit")
    limit = limit if isinstance(limit, int) and 10 <= limit <= 5000 else None
    scholarship_name = None
    if isinstance(data.get("scholarship_id"), int):
        s = db.session.get(Scholarship, data["scholarship_id"])
        scholarship_name = f"{s.title} ({s.organization})" if s else None

    # Count the request before calling, so retries can't exceed the limit.
    db.session.add(CoachUse(user_id=user.id))
    db.session.commit()
    try:
        result = get_feedback(
            text, question, limit, scholarship_name,
            api_key=current_app.config["ANTHROPIC_API_KEY"],
            model=current_app.config["COACH_MODEL"],
        )
    except CoachError as exc:
        # A request that never reached the model shouldn't use up the limit.
        last = CoachUse.query.filter_by(user_id=user.id).order_by(CoachUse.id.desc()).first()
        if last:
            db.session.delete(last)
            db.session.commit()
        return jsonify({"error": str(exc)}), 400
    return jsonify({"feedback": result, "remaining_today": _remaining(user.id)})
