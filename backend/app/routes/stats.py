"""
app/routes/stats.py
----------------------
  GET /api/stats -> the "Stats for Idiots" dashboard payload for the
  logged-in user only (see app/services/stats.py for how each number is
  computed). No other user's data is ever touched -- everything is
  scoped to get_jwt_identity().
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import User
from app.services.stats import build_stats

stats_bp = Blueprint("stats", __name__, url_prefix="/api/stats")


@stats_bp.get("")
@jwt_required()
def stats():
    user = User.query.get_or_404(get_jwt_identity())
    return jsonify(build_stats(user))
